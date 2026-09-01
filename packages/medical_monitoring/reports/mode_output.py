"""R6 slice-04/05/06 ModeContract / ModeOutput runtime (offline).

Slice-04: immutable three-mode ``ModeContract`` builders, the Run entry gate
(execution basis, entry conditions, cutoff/source revision, carry-forward,
fixed-total, silent mode conversion), generic ``ModeOutput`` identity/
eligibility envelope, daily four outputs, and structured
``affected_query_draft`` projection (依据/发现/行动项 Chinese display,
evidence/identity binding, draft-only unsent/unclosed).

Slice-05: pre_lock four default outputs (``full_risk``, ``revision_impact``,
``check_package``, ``query_revision_package``) reused on the same ModeOutput
envelope / Run gate / eligibility / authority binding. No second identity
framework. No Query send/close, PD register/close, or user confirmation.

Slice-06: post_lock_pre_cfdi four fixed-total outputs (``full_project_report``,
``site_materials``, ``subject_materials``, ``checklist``) on the same
ModeOutput / Run-gate / authority framework. Locked snapshot identity,
population totals, nested IDs, and cross-output reconciliation. No overwrite,
no sign/send, no external-report rename, no second identity framework.

Canonical JSON objects only. Stdlib only. Does not mutate inputs. Does not
touch product/frontend/services, real projects, ports 8911/5174, browsers,
OCR, or models.
"""

from __future__ import annotations

import copy
from typing import Any, Mapping, Optional, Sequence, Tuple

from . import contracts
from .report_review import (
    COMMON_BINDING_REQUIRED,
    EXECUTION_BASES,
    MODES,
    canonical_bytes,
    sha256_hex,
)

CONTRACT_VERSION = "0.1"

# Canonical failure codes (R6-C-MODE-001 + R6-C-OUT-001 + adjacent identity).
MODE_ENTRY_BLOCKED = "mode_entry_blocked"
SILENT_MODE_CONVERSION = "silent_mode_conversion"
OUTPUT_NOT_ELIGIBLE = "output_not_eligible"
AUTHORITY_MISMATCH = "authority_mismatch"
IDENTITY_MISMATCH = "identity_mismatch"
CUTOFF_MISMATCH = "cutoff_mismatch"
REVISION_MISMATCH = "revision_mismatch"

PRODUCER_SYSTEM = "system_monitoring_output"
PRODUCER_EXTERNAL = "external_report_review"
PRODUCER_KINDS = frozenset({PRODUCER_SYSTEM, PRODUCER_EXTERNAL})

DAILY_OUTPUT_KINDS = (
    "change_summary",
    "current_full_risk",
    "affected_query_draft",
    "data_knowledge_rule_model_change_note",
)

PRE_LOCK_OUTPUT_KINDS = (
    "full_risk",
    "revision_impact",
    "check_package",
    "query_revision_package",
)

POST_LOCK_OUTPUT_KINDS = (
    "full_project_report",
    "site_materials",
    "subject_materials",
    "checklist",
)

SYSTEM_DEFAULT_OUTPUT_KINDS = frozenset(
    DAILY_OUTPUT_KINDS + PRE_LOCK_OUTPUT_KINDS + POST_LOCK_OUTPUT_KINDS
)

POST_LOCK_FORBIDDEN_TRUE_FLAGS = (
    "is_user_confirmed",
    "user_confirmed",
    "is_signed",
    "signed",
    "is_sent",
    "sent",
    "is_closed",
    "external_dispatch_allowed",
    "pd_registered",
    "pd_closed",
    "is_pd_recorded",
    "is_pd_closed",
)
POST_LOCK_REQUIRED_FALSE_FLAGS = (
    "is_user_confirmed",
    "is_signed",
    "is_sent",
    "external_dispatch_allowed",
)
POST_LOCK_FORBIDDEN_WORKFLOW_KEYS = frozenset(
    {
        "sent_at",
        "closed_at",
        "pd_record_id",
        "external_reply_id",
        "dispatch_id",
    }
)
POST_LOCK_OVERWRITE_META_KEYS = frozenset(
    {
        "overwrites_output_id",
        "replaces_output_id",
        "replaces_artifact_id",
        "in_place_update",
        "mutate_existing",
        "overwrite",
        "overwrites",
    }
)
POPULATION_TOTAL_KEYS = ("site_count", "subject_count", "risk_count")
RISK_SUMMARY_COUNT_KEYS = ("high_count", "medium_count", "low_count")

CHECK_LEVELS = frozenset({"project", "site", "subject"})
CHECK_STATUSES = frozenset({"ready", "blocked", "not_applicable"})
CHECK_FORBIDDEN_STATUSES = frozenset(
    {"completed", "passed", "user_confirmed", "done", "closed", "sent"}
)
REVISION_KINDS = frozenset({"new", "updated", "unchanged", "withdrawn_draft"})
IMPACT_KINDS = frozenset(
    {"clinical_data", "knowledge_rule_mapping_model", "user_decision"}
)
KNOWLEDGE_CHANGE_SURFACES = frozenset(
    {
        "knowledge",
        "rule",
        "mapping",
        "model",
        "knowledge_rule_mapping_model",
    }
)
FULL_RISK_FORBIDDEN_TRUE_FLAGS = (
    "is_user_confirmed",
    "disposition_closed",
    "medical_conclusion_final",
    "is_disposition_complete",
    "user_confirmed",
)

OUTPUT_STATES = frozenset(
    {"not_published", "dashboard_visible", "draft_exportable", "exported"}
)

EXTERNAL_REPORT_REQUIRED = (
    "report_source_revision_id",
    "report_lineage_id",
    "report_revision_id",
    "report_artifact_id",
    "coverage_ledger_id",
)

MODE_OUTPUT_ENVELOPE_REQUIRED = (
    "output_id",
    "output_kind",
    "producer_kind",
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
    "authority_refs",
    "coverage_refs",
    "qc_refs",
    "output_state",
    "is_user_confirmed",
)

ELIGIBILITY_BOOL_TRUE = (
    "entry_conditions_verified",
    "required_snapshot_acceptance_verified",
    "required_coverage_closed",
    "issue_and_conflict_policy_passed",
    "deterministic_qc_passed",
    "format_identity_qc_passed",
)

ELIGIBILITY_REQUIRED = (
    "mode_contract_matches_run",
    "entry_conditions_verified",
    "cutoff_and_revision_match",
    "required_snapshot_acceptance_verified",
    "analysis_state",
    "evidence_state",
    "required_coverage_closed",
    "issue_and_conflict_policy_passed",
    "deterministic_qc_passed",
    "format_identity_qc_passed",
    "has_external_report_input",
)

QUERY_DRAFT_REQUIRED = (
    "query_draft_id",
    "finding_id",
    "risk_id",
    "project_id",
    "run_id",
    "subject_id",
    "site_id",
    "scope_kind",
    "basis",
    "finding",
    "action",
    "display_text",
    "evidence_refs",
    "locator",
    "data_cutoff",
    "source_revision_id",
    "issue_id",
    "draft_state",
    "is_sent",
    "is_closed",
    "is_user_confirmed",
)

# Lifecycle / external-workflow fields that must stay false or absent.
QUERY_FORBIDDEN_TRUE_FLAGS = (
    "is_sent",
    "is_closed",
    "is_user_confirmed",
    "is_pd_recorded",
    "is_pd_closed",
    "pd_registered",
    "pd_closed",
)
QUERY_REQUIRED_FALSE_FLAGS = (
    "is_sent",
    "is_closed",
    "is_user_confirmed",
    "is_pd_recorded",
    "is_pd_closed",
)
QUERY_FORBIDDEN_KEYS = frozenset(
    {
        "sent_at",
        "closed_at",
        "pd_record_id",
        "external_reply_id",
        "dispatch_id",
    }
)

QUERY_LABEL_BASIS = "依据"
QUERY_LABEL_FINDING = "发现"
QUERY_LABEL_ACTION = "行动项"

MODE_CONTRACT_REQUIRED = (
    "contract_id",
    "contract_version",
    "mode",
    "allowed_execution_basis",
    "entry_conditions",
    "cutoff_policy",
    "revision_policy",
    "carry_forward_policy",
    "output_eligibility",
    "immutable",
)

OUTPUT_ELIGIBILITY_REQUIRED = (
    "default_outputs",
    "conditional_outputs",
    "external_report_review_default",
    "output_requirements",
)

# MonitoringRun identity fields used by the Run gate (contract.json identity_rules).
RUN_IDENTITY_REQUIRED = (
    "run_id",
    "project_id",
    "mode",
    "execution_basis",
    "data_cutoff",
    "source_revision_id",
    "carry_forward_run_ids",
)

RUN_GATE_OPTIONAL_FLAGS = (
    "mode_transition",
    "carry_forward_compatibility",
    "carry_forward_source_run",
    "fixed_total",
    "locked_snapshot_hash",
    "output_cutoff_ref",
    "output_revision_ref",
    "prior_baseline_ref",
)

EXPLICIT_NEW_RUN = "explicit_new_run"
SILENT_IN_PLACE = "silent_in_place"
CARRY_FORWARD_COMPATIBLE = "compatible"
CARRY_FORWARD_INCOMPATIBLE = "incompatible"


class ModeOutputError(ValueError):
    """Fail-closed error for ModeContract / ModeOutput / Query-draft construction."""

    def __init__(self, failure_code: str, message: str) -> None:
        self.failure_code = failure_code
        super().__init__(f"{failure_code}: {message}")


def _copy_mapping(obj: Mapping[str, Any]) -> dict:
    return copy.deepcopy(dict(obj))


def _require_non_empty_str(value: Any, field: str, code: str) -> str:
    if not isinstance(value, str) or value.strip() == "":
        raise ModeOutputError(code, f"{field} must be a non-empty string")
    return value


def _frozen_mode_contract_rows() -> Tuple[dict, ...]:
    """Return the three frozen ``mode_contracts`` rows from contract.json."""
    obj = contracts.contract_obj()
    rows = obj.get("mode_contracts")
    if not isinstance(rows, list) or len(rows) != 3:
        raise ModeOutputError(
            IDENTITY_MISMATCH,
            "frozen mode_contracts must be exactly three rows",
        )
    return tuple(copy.deepcopy(row) for row in rows)


def _row_by_mode(mode: str) -> dict:
    mode = _require_non_empty_str(mode, "mode", IDENTITY_MISMATCH)
    if mode not in MODES:
        raise ModeOutputError(IDENTITY_MISMATCH, f"mode={mode!r} is not a frozen mode")
    for row in _frozen_mode_contract_rows():
        if row.get("mode") == mode:
            return row
    raise ModeOutputError(IDENTITY_MISMATCH, f"no frozen mode_contract for mode={mode!r}")


def _reshape_mode_contract(row: Mapping[str, Any]) -> dict:
    """Map a frozen mode_contracts row onto the ModeContract object schema."""
    mode = _require_non_empty_str(row.get("mode"), "mode", IDENTITY_MISMATCH)
    allowed = row.get("allowed_execution_basis")
    if not isinstance(allowed, list) or not allowed:
        raise ModeOutputError(
            MODE_ENTRY_BLOCKED,
            f"mode={mode!r} allowed_execution_basis must be a non-empty list",
        )
    for basis in allowed:
        if basis not in EXECUTION_BASES:
            raise ModeOutputError(
                MODE_ENTRY_BLOCKED,
                f"mode={mode!r} has unknown execution_basis={basis!r}",
            )
    entry_conditions = row.get("entry_conditions")
    if not isinstance(entry_conditions, list) or not entry_conditions:
        raise ModeOutputError(
            MODE_ENTRY_BLOCKED,
            f"mode={mode!r} entry_conditions must be a non-empty list",
        )
    output_eligibility = {
        "default_outputs": copy.deepcopy(list(row.get("default_outputs") or [])),
        "conditional_outputs": copy.deepcopy(list(row.get("conditional_outputs") or [])),
        "external_report_review_default": bool(
            row.get("external_report_review_default", False)
        ),
        "output_requirements": copy.deepcopy(list(row.get("output_requirements") or [])),
    }
    contract = {
        "contract_id": _require_non_empty_str(
            row.get("contract_id"), "contract_id", IDENTITY_MISMATCH
        ),
        "contract_version": _require_non_empty_str(
            row.get("contract_version", CONTRACT_VERSION),
            "contract_version",
            IDENTITY_MISMATCH,
        ),
        "mode": mode,
        "allowed_execution_basis": list(allowed),
        "entry_conditions": copy.deepcopy(list(entry_conditions)),
        "cutoff_policy": _require_non_empty_str(
            row.get("cutoff_policy"), "cutoff_policy", MODE_ENTRY_BLOCKED
        ),
        "revision_policy": _require_non_empty_str(
            row.get("revision_policy"), "revision_policy", MODE_ENTRY_BLOCKED
        ),
        "carry_forward_policy": _require_non_empty_str(
            row.get("carry_forward_policy"), "carry_forward_policy", MODE_ENTRY_BLOCKED
        ),
        "output_eligibility": output_eligibility,
        "immutable": True,
    }
    return contract


def build_mode_contract(mode: str) -> dict:
    """Build the immutable ModeContract for ``daily`` / ``pre_lock`` / ``post_lock_pre_cfdi``.

    Returns a deep copy derived from the frozen ``contract.json`` ``mode_contracts``
    row. Inputs are never mutated. ``immutable`` is always ``True``.
    """
    return _reshape_mode_contract(_row_by_mode(mode))


def build_all_mode_contracts() -> Tuple[dict, dict, dict]:
    """Return the three ModeContracts in frozen contract.json order."""
    contracts_out = []
    for row in _frozen_mode_contract_rows():
        contracts_out.append(_reshape_mode_contract(row))
    return tuple(contracts_out)  # type: ignore[return-value]


def mode_contract_digest(mode_contract: Mapping[str, Any]) -> str:
    """SHA-256 of the canonical JSON bytes of a ModeContract."""
    return sha256_hex(canonical_bytes(_copy_mapping(mode_contract)))


def validate_mode_contract(mode_contract: Mapping[str, Any]) -> Tuple[str, ...]:
    """Validate a ModeContract against the frozen three-mode table.

    Returns a tuple of canonical failure codes (empty on success). Does not
    mutate ``mode_contract``.
    """
    codes: list[str] = []
    if not isinstance(mode_contract, Mapping):
        return (IDENTITY_MISMATCH,)
    mc = _copy_mapping(mode_contract)

    for field in MODE_CONTRACT_REQUIRED:
        if field not in mc:
            codes.append(IDENTITY_MISMATCH)
    if codes:
        return tuple(_dedupe(codes))

    mode = mc.get("mode")
    if mode not in MODES:
        codes.append(IDENTITY_MISMATCH)

    if mc.get("immutable") is not True:
        # Tampering with immutability is a silent contract conversion.
        codes.append(SILENT_MODE_CONVERSION)

    if mc.get("contract_version") != CONTRACT_VERSION:
        codes.append(IDENTITY_MISMATCH)

    allowed = mc.get("allowed_execution_basis")
    if not isinstance(allowed, list) or not allowed:
        codes.append(MODE_ENTRY_BLOCKED)
    else:
        for basis in allowed:
            if basis not in EXECUTION_BASES:
                codes.append(MODE_ENTRY_BLOCKED)

    for text_field in (
        "contract_id",
        "cutoff_policy",
        "revision_policy",
        "carry_forward_policy",
    ):
        value = mc.get(text_field)
        if not isinstance(value, str) or value.strip() == "":
            codes.append(IDENTITY_MISMATCH)

    entry_conditions = mc.get("entry_conditions")
    if not isinstance(entry_conditions, list) or not entry_conditions:
        codes.append(MODE_ENTRY_BLOCKED)
    elif any(not isinstance(item, str) or item.strip() == "" for item in entry_conditions):
        codes.append(MODE_ENTRY_BLOCKED)

    eligibility = mc.get("output_eligibility")
    if not isinstance(eligibility, Mapping):
        codes.append(MODE_ENTRY_BLOCKED)
    else:
        for field in OUTPUT_ELIGIBILITY_REQUIRED:
            if field not in eligibility:
                codes.append(MODE_ENTRY_BLOCKED)
        defaults = eligibility.get("default_outputs")
        if not isinstance(defaults, list) or not defaults:
            codes.append(MODE_ENTRY_BLOCKED)
        if not isinstance(eligibility.get("conditional_outputs"), list):
            codes.append(MODE_ENTRY_BLOCKED)
        if not isinstance(eligibility.get("output_requirements"), list):
            codes.append(MODE_ENTRY_BLOCKED)
        if not isinstance(eligibility.get("external_report_review_default"), bool):
            codes.append(MODE_ENTRY_BLOCKED)

    if mode in MODES:
        try:
            expected = build_mode_contract(str(mode))
        except ModeOutputError:
            codes.append(IDENTITY_MISMATCH)
        else:
            if canonical_bytes(mc) != canonical_bytes(expected):
                # Any drift from the frozen ModeContract is fail-closed.
                codes.append(SILENT_MODE_CONVERSION)

    return tuple(_dedupe(codes))


def _dedupe(codes: Sequence[str]) -> list[str]:
    seen = set()
    out: list[str] = []
    for code in codes:
        if code not in seen:
            seen.add(code)
            out.append(code)
    return out


def _append(codes: list[str], code: str) -> None:
    if code not in codes:
        codes.append(code)


def _non_empty_str(value: Any) -> bool:
    return isinstance(value, str) and value.strip() != ""


def _truthy_flag(ctx: Mapping[str, Any], key: str) -> bool:
    return ctx.get(key) is True


def _validate_common_binding(run: Mapping[str, Any], codes: list[str]) -> None:
    for field in COMMON_BINDING_REQUIRED:
        if field not in run or not _non_empty_str(run.get(field)):
            _append(codes, IDENTITY_MISMATCH)
    mode = run.get("mode")
    if mode not in MODES:
        _append(codes, IDENTITY_MISMATCH)
    basis = run.get("execution_basis")
    if basis not in EXECUTION_BASES:
        _append(codes, MODE_ENTRY_BLOCKED)


def _validate_silent_conversion(
    run: Mapping[str, Any],
    prior_run: Optional[Mapping[str, Any]],
    codes: list[str],
) -> None:
    transition = run.get("mode_transition")
    if transition == SILENT_IN_PLACE:
        _append(codes, SILENT_MODE_CONVERSION)
    elif transition is not None and transition != EXPLICIT_NEW_RUN:
        _append(codes, SILENT_MODE_CONVERSION)

    if prior_run is None:
        return
    prior = _copy_mapping(prior_run)
    # Same run_id with changed mode/cutoff/revision/basis is an in-place conversion.
    if prior.get("run_id") == run.get("run_id"):
        for field in (
            "mode",
            "data_cutoff",
            "source_revision_id",
            "execution_basis",
            "knowledge_pack_version",
            "rule_activation_version",
            "mapping_version",
            "identity_algorithm_digest",
        ):
            if prior.get(field) != run.get(field):
                _append(codes, SILENT_MODE_CONVERSION)
                break
    # post_lock_pre_cfdi cannot silently become daily/pre_lock under a reused identity.
    if (
        prior.get("mode") == "post_lock_pre_cfdi"
        and run.get("mode") in {"daily", "pre_lock"}
        and prior.get("run_id") == run.get("run_id")
    ):
        _append(codes, SILENT_MODE_CONVERSION)


def _validate_execution_basis(
    run: Mapping[str, Any],
    mode_contract: Mapping[str, Any],
    entry_context: Mapping[str, Any],
    codes: list[str],
) -> None:
    basis = run.get("execution_basis")
    allowed = mode_contract.get("allowed_execution_basis") or []
    if basis not in allowed:
        _append(codes, MODE_ENTRY_BLOCKED)
        return

    mode = mode_contract.get("mode")
    if mode in {"pre_lock", "post_lock_pre_cfdi"} and basis != "full":
        _append(codes, MODE_ENTRY_BLOCKED)
        return

    if mode == "daily" and basis == "incremental":
        prior = entry_context.get("prior_baseline")
        prior_ref = run.get("prior_baseline_ref")
        if prior_ref is None and "prior_baseline_ref" in run:
            _append(codes, MODE_ENTRY_BLOCKED)
            return
        if not isinstance(prior, Mapping):
            _append(codes, MODE_ENTRY_BLOCKED)
            return
        if prior.get("project_id") != run.get("project_id"):
            _append(codes, MODE_ENTRY_BLOCKED)
            return
        required_flags = (
            "compatible",
            "evidence_complete",
            "identity_compatible",
            "mapping_compatible",
            "rule_compatible",
            "knowledge_compatible",
        )
        if any(prior.get(flag) is not True for flag in required_flags):
            _append(codes, MODE_ENTRY_BLOCKED)
            return
        if not _non_empty_str(prior.get("run_id")):
            _append(codes, MODE_ENTRY_BLOCKED)
            return
        if prior_ref is not None and prior_ref != prior.get("run_id"):
            _append(codes, MODE_ENTRY_BLOCKED)


def _validate_entry_conditions(
    mode: str,
    entry_context: Mapping[str, Any],
    codes: list[str],
) -> None:
    if not _truthy_flag(entry_context, "accepted_full_snapshot"):
        _append(codes, MODE_ENTRY_BLOCKED)
    if not _truthy_flag(entry_context, "scope_non_ambiguous"):
        _append(codes, MODE_ENTRY_BLOCKED)
    if not _non_empty_str(entry_context.get("data_cutoff")) and not _truthy_flag(
        entry_context, "cutoff_declared_on_run"
    ):
        # Cutoff may be declared only on the run; entry_context may mirror it.
        pass

    if mode == "pre_lock":
        if not _truthy_flag(entry_context, "lock_preparation_window_declared"):
            _append(codes, MODE_ENTRY_BLOCKED)
        if not _truthy_flag(entry_context, "cutoff_confirmed"):
            _append(codes, MODE_ENTRY_BLOCKED)

    if mode == "post_lock_pre_cfdi":
        if not _truthy_flag(entry_context, "baseline_eligible"):
            _append(codes, MODE_ENTRY_BLOCKED)
        if not _truthy_flag(entry_context, "cutoff_confirmed"):
            _append(codes, MODE_ENTRY_BLOCKED)
        if not _truthy_flag(entry_context, "fixed_total_confirmed"):
            _append(codes, MODE_ENTRY_BLOCKED)
        selection = entry_context.get("locked_version_selection")
        if not isinstance(selection, Mapping):
            _append(codes, MODE_ENTRY_BLOCKED)
        else:
            for field in (
                "local_os_user",
                "snapshot_hash",
                "acceptance_evidence_hash",
            ):
                if not _non_empty_str(selection.get(field)):
                    _append(codes, MODE_ENTRY_BLOCKED)


def _validate_cutoff_and_revision(
    run: Mapping[str, Any],
    mode_contract: Mapping[str, Any],
    entry_context: Mapping[str, Any],
    codes: list[str],
) -> None:
    if not _non_empty_str(run.get("data_cutoff")):
        _append(codes, CUTOFF_MISMATCH)
    if not _non_empty_str(run.get("source_revision_id")):
        _append(codes, REVISION_MISMATCH)

    ctx_cutoff = entry_context.get("data_cutoff")
    if _non_empty_str(ctx_cutoff) and ctx_cutoff != run.get("data_cutoff"):
        _append(codes, CUTOFF_MISMATCH)
    ctx_revision = entry_context.get("source_revision_id")
    if _non_empty_str(ctx_revision) and ctx_revision != run.get("source_revision_id"):
        _append(codes, REVISION_MISMATCH)

    mode = mode_contract.get("mode")
    if mode != "post_lock_pre_cfdi":
        return

    # Fixed-total post_lock: output refs must bind the locked cutoff/revision.
    out_cutoff = run.get("output_cutoff_ref")
    if out_cutoff is not None and out_cutoff != run.get("data_cutoff"):
        _append(codes, CUTOFF_MISMATCH)
    out_revision = run.get("output_revision_ref")
    if out_revision is not None and out_revision != run.get("source_revision_id"):
        _append(codes, REVISION_MISMATCH)

    locked_hash = run.get("locked_snapshot_hash")
    selection = entry_context.get("locked_version_selection")
    if isinstance(selection, Mapping):
        expected_hash = selection.get("snapshot_hash")
        if not _non_empty_str(locked_hash):
            _append(codes, MODE_ENTRY_BLOCKED)
        elif locked_hash != expected_hash:
            _append(codes, REVISION_MISMATCH)
        if run.get("local_os_user") != selection.get("local_os_user"):
            _append(codes, MODE_ENTRY_BLOCKED)
        if run.get("acceptance_evidence_hash") != selection.get(
            "acceptance_evidence_hash"
        ):
            _append(codes, MODE_ENTRY_BLOCKED)
        if run.get("fixed_total") is not True:
            _append(codes, MODE_ENTRY_BLOCKED)
        if run.get("output_cutoff_ref") != run.get("data_cutoff"):
            _append(codes, CUTOFF_MISMATCH)
        if run.get("output_revision_ref") != run.get("source_revision_id"):
            _append(codes, REVISION_MISMATCH)
    else:
        if run.get("fixed_total") is not True:
            _append(codes, MODE_ENTRY_BLOCKED)


def _validate_carry_forward(
    run: Mapping[str, Any],
    prior_run: Optional[Mapping[str, Any]],
    entry_context: Mapping[str, Any],
    codes: list[str],
) -> None:
    carry_ids = run.get("carry_forward_run_ids")
    if carry_ids is None:
        _append(codes, MODE_ENTRY_BLOCKED)
        return
    if not isinstance(carry_ids, list):
        _append(codes, MODE_ENTRY_BLOCKED)
        return
    if any(not _non_empty_str(item) for item in carry_ids):
        _append(codes, MODE_ENTRY_BLOCKED)
        return

    cross_mode = entry_context.get("cross_mode_carry_forward") is True
    has_carry = bool(carry_ids) or cross_mode or "carry_forward_source_run" in run

    if not has_carry:
        return

    source = run.get("carry_forward_source_run")
    target = run.get("carry_forward_target_run")
    reason = run.get("carry_forward_reason")
    artifact_hash = run.get("reusable_artifact_hash")
    compatibility = run.get("carry_forward_compatibility")
    if (
        not _non_empty_str(source)
        or source not in carry_ids
        or target != run.get("run_id")
        or not _non_empty_str(reason)
        or not _non_empty_str(artifact_hash)
        or compatibility != CARRY_FORWARD_COMPATIBLE
    ):
        _append(codes, MODE_ENTRY_BLOCKED)
        return

    if prior_run is None:
        _append(codes, MODE_ENTRY_BLOCKED)
        return

    if _non_empty_str(source):
        if prior_run.get("run_id") != source:
            _append(codes, MODE_ENTRY_BLOCKED)
        # Carry-forward is provenance only: it cannot rewrite target identity.
        if prior_run.get("data_cutoff") != run.get("data_cutoff") and run.get(
            "mode"
        ) == "post_lock_pre_cfdi":
            # Different cutoff under post_lock fixed identity is a revision event,
            # not a silent carry rewrite — require distinct run_id (already checked
            # in silent conversion). Here only flag undeclared incompatibility.
            if run.get("carry_forward_compatibility") != CARRY_FORWARD_COMPATIBLE:
                _append(codes, MODE_ENTRY_BLOCKED)


def validate_run_mode_gate(
    run_binding: Mapping[str, Any],
    mode_contract: Mapping[str, Any],
    *,
    entry_context: Optional[Mapping[str, Any]] = None,
    prior_run: Optional[Mapping[str, Any]] = None,
) -> Tuple[str, ...]:
    """Validate a MonitoringRun against an immutable ModeContract (Run gate).

    Fail-closes on silent mode conversion, execution-basis mismatch, unmet entry
    conditions, cutoff/source-revision drift, undeclared/incompatible
    carry-forward, and post_lock fixed-total violations.

    Returns canonical failure codes. Does not mutate inputs.
    """
    codes: list[str] = []
    if not isinstance(run_binding, Mapping) or not isinstance(mode_contract, Mapping):
        return (IDENTITY_MISMATCH,)

    run = _copy_mapping(run_binding)
    contract = _copy_mapping(mode_contract)
    ctx = _copy_mapping(entry_context or {})
    prior = None if prior_run is None else _copy_mapping(prior_run)

    contract_codes = validate_mode_contract(contract)
    for code in contract_codes:
        _append(codes, code)
    if contract_codes:
        # A broken contract cannot authorize a run.
        return tuple(_dedupe(codes))

    _validate_common_binding(run, codes)

    if run.get("mode") != contract.get("mode"):
        _append(codes, MODE_ENTRY_BLOCKED)

    for field in RUN_IDENTITY_REQUIRED:
        if field not in run:
            _append(codes, IDENTITY_MISMATCH)
        elif field == "carry_forward_run_ids":
            if not isinstance(run.get(field), list):
                _append(codes, IDENTITY_MISMATCH)
        elif not _non_empty_str(run.get(field)):
            _append(codes, IDENTITY_MISMATCH)

    _validate_silent_conversion(run, prior, codes)
    _validate_execution_basis(run, contract, ctx, codes)
    _validate_entry_conditions(str(contract.get("mode")), ctx, codes)
    _validate_cutoff_and_revision(run, contract, ctx, codes)
    _validate_carry_forward(run, prior, ctx, codes)

    return tuple(_dedupe(codes))


def default_entry_context_for_mode(
    mode: str,
    *,
    run_binding: Optional[Mapping[str, Any]] = None,
) -> dict:
    """Build a synthetic accepted entry_context that passes the Run gate.

    Useful for offline positive fixtures. Not a product acceptance signal.
    """
    mode = _require_non_empty_str(mode, "mode", IDENTITY_MISMATCH)
    if mode not in MODES:
        raise ModeOutputError(IDENTITY_MISMATCH, f"mode={mode!r} is not a frozen mode")
    run = {} if run_binding is None else _copy_mapping(run_binding)
    ctx: dict[str, Any] = {
        "accepted_full_snapshot": True,
        "scope_non_ambiguous": True,
        "cutoff_declared_on_run": True,
        "data_cutoff": run.get("data_cutoff"),
        "source_revision_id": run.get("source_revision_id"),
        "cross_mode_carry_forward": False,
    }
    if mode == "daily" and run.get("execution_basis") == "incremental":
        prior_ref = run.get("prior_baseline_ref") or "run-daily-prior-001"
        ctx["prior_baseline"] = {
            "run_id": prior_ref,
            "project_id": run.get("project_id") or "project-r6-synthetic",
            "compatible": True,
            "evidence_complete": True,
            "identity_compatible": True,
            "mapping_compatible": True,
            "rule_compatible": True,
            "knowledge_compatible": True,
        }
    if mode == "pre_lock":
        ctx["lock_preparation_window_declared"] = True
        ctx["cutoff_confirmed"] = True
    if mode == "post_lock_pre_cfdi":
        ctx["baseline_eligible"] = True
        ctx["cutoff_confirmed"] = True
        ctx["fixed_total_confirmed"] = True
        snap = run.get("locked_snapshot_hash") or "snap-hash-fixed-001"
        ctx["locked_version_selection"] = {
            "local_os_user": "local-user-synthetic",
            "snapshot_hash": snap,
            "acceptance_evidence_hash": "accept-hash-fixed-001",
        }
    return ctx


# ---------------------------------------------------------------------------
# Work item 2 — ModeOutput envelope + daily Query draft projection
# ---------------------------------------------------------------------------


def default_output_eligibility(*, has_external_report_input: bool = False) -> dict:
    """Synthetic eligibility gates that satisfy R6-C-OUT-001 for offline fixtures."""
    gates = {
        "mode_contract_matches_run": True,
        "entry_conditions_verified": True,
        "cutoff_and_revision_match": True,
        "required_snapshot_acceptance_verified": True,
        "analysis_state": "complete",
        "evidence_state": "complete",
        "required_coverage_closed": True,
        "issue_and_conflict_policy_passed": True,
        "deterministic_qc_passed": True,
        "format_identity_qc_passed": True,
        "has_external_report_input": bool(has_external_report_input),
    }
    if has_external_report_input:
        gates["full_report_reviewed_eligible"] = True
    else:
        gates["system_report_facts_risk_coverage_qc"] = True
    return gates


def _eligible_kinds_for_mode(mode_contract: Mapping[str, Any]) -> set[str]:
    eligibility = mode_contract.get("output_eligibility") or {}
    kinds: set[str] = set()
    for key in ("default_outputs", "conditional_outputs"):
        values = eligibility.get(key) or []
        if isinstance(values, list):
            kinds.update(str(v) for v in values)
    return kinds


def _require_ref_mapping(value: Any, field: str) -> dict:
    if not isinstance(value, Mapping) or not value:
        raise ModeOutputError(
            AUTHORITY_MISMATCH, f"{field} must be a non-empty mapping"
        )
    return _copy_mapping(value)


def _bind_refs_to_run(refs: Mapping[str, Any], run: Mapping[str, Any], field: str) -> None:
    for key in ("project_id", "run_id", "data_cutoff", "source_revision_id"):
        if key in refs and refs.get(key) != run.get(key):
            raise ModeOutputError(
                AUTHORITY_MISMATCH,
                f"{field}.{key} drifts from run_binding",
            )
    # Authority/coverage/QC refs must themselves carry non-empty identity digests.
    digest = refs.get("authority_digest") or refs.get("coverage_digest") or refs.get(
        "qc_digest"
    ) or refs.get("digest")
    if not _non_empty_str(digest):
        raise ModeOutputError(
            AUTHORITY_MISMATCH, f"{field} must include a non-empty digest"
        )


def _check_eligibility(spec: Mapping[str, Any], *, producer_kind: str) -> None:
    for field in ELIGIBILITY_REQUIRED:
        if field not in spec:
            raise ModeOutputError(
                OUTPUT_NOT_ELIGIBLE, f"eligibility missing {field}"
            )
    if spec.get("analysis_state") != "complete":
        raise ModeOutputError(OUTPUT_NOT_ELIGIBLE, "analysis_state must be complete")
    if spec.get("evidence_state") != "complete":
        raise ModeOutputError(OUTPUT_NOT_ELIGIBLE, "evidence_state must be complete")
    for flag in ELIGIBILITY_BOOL_TRUE:
        if spec.get(flag) is not True:
            raise ModeOutputError(OUTPUT_NOT_ELIGIBLE, f"{flag} must be true")
    if spec.get("cutoff_and_revision_match") is not True:
        raise ModeOutputError(OUTPUT_NOT_ELIGIBLE, "cutoff_and_revision_match failed")
    if spec.get("mode_contract_matches_run") is not True:
        raise ModeOutputError(OUTPUT_NOT_ELIGIBLE, "mode_contract_matches_run failed")

    has_external = spec.get("has_external_report_input") is True
    if has_external:
        if spec.get("full_report_reviewed_eligible") is not True:
            raise ModeOutputError(
                OUTPUT_NOT_ELIGIBLE,
                "external report input requires full_report_reviewed_eligible",
            )
    else:
        if producer_kind == PRODUCER_EXTERNAL:
            raise ModeOutputError(
                OUTPUT_NOT_ELIGIBLE,
                "external_report_review producer requires external report input",
            )
        if spec.get("system_report_facts_risk_coverage_qc") is not True:
            # Absent external input: system coverage/QC gate is required.
            raise ModeOutputError(
                OUTPUT_NOT_ELIGIBLE,
                "system_report_facts_risk_coverage_qc must be true",
            )


def _zh_clause(raw: Any, label: str) -> str:
    if not isinstance(raw, str) or raw.strip() == "":
        raise ModeOutputError(OUTPUT_NOT_ELIGIBLE, f"Query {label} is missing")
    text = raw.strip()
    if text.startswith(f"{label}：") or text.startswith(f"{label}:"):
        clause = text if text.startswith(f"{label}：") else f"{label}：{text[len(label) + 1:].lstrip()}"
    else:
        clause = f"{label}：{text}"
    if not clause.endswith(("。", "；", ".", ";")):
        clause = clause + "。"
    return clause


def project_query_display_text(basis: str, finding: str, action: str) -> str:
    """Deterministic Chinese three-clause projection: 依据 + 发现 + 行动项."""
    return (
        _zh_clause(basis, QUERY_LABEL_BASIS)
        + _zh_clause(finding, QUERY_LABEL_FINDING)
        + _zh_clause(action, QUERY_LABEL_ACTION)
    )


def _finding_scope(finding: Mapping[str, Any]) -> Tuple[str, str, str]:
    scope_kind = finding.get("scope_kind")
    subject = finding.get("subject_id")
    site = finding.get("site_id")
    if not _non_empty_str(site):
        raise ModeOutputError(OUTPUT_NOT_ELIGIBLE, "finding.site_id is required")
    if scope_kind == "subject":
        if not _non_empty_str(subject):
            raise ModeOutputError(
                OUTPUT_NOT_ELIGIBLE, "subject scope requires subject_id"
            )
    elif scope_kind == "site":
        if subject not in (None, ""):
            raise ModeOutputError(
                OUTPUT_NOT_ELIGIBLE, "site scope must not claim subject_id"
            )
    else:
        raise ModeOutputError(
            OUTPUT_NOT_ELIGIBLE, "scope_kind must be subject or site"
        )
    return str(subject or ""), str(site), str(scope_kind)


def _finding_evidence(finding: Mapping[str, Any]) -> Tuple[list, dict]:
    evidence = finding.get("evidence_refs")
    locator = finding.get("locator")
    if not isinstance(evidence, list) or not evidence:
        raise ModeOutputError(OUTPUT_NOT_ELIGIBLE, "evidence_refs must be non-empty")
    if any(
        (not isinstance(item, Mapping) and not _non_empty_str(item))
        for item in evidence
    ):
        raise ModeOutputError(OUTPUT_NOT_ELIGIBLE, "evidence_refs entries must be checkable")
    # Normalize evidence to strings or mappings (deep-copied).
    normalized: list = []
    for item in evidence:
        if isinstance(item, Mapping):
            if not _non_empty_str(item.get("evidence_id")) and not _non_empty_str(
                item.get("ref")
            ):
                raise ModeOutputError(
                    OUTPUT_NOT_ELIGIBLE, "evidence mapping lacks evidence_id/ref"
                )
            normalized.append(_copy_mapping(item))
        else:
            normalized.append(str(item))
    if not isinstance(locator, Mapping) or not locator:
        raise ModeOutputError(OUTPUT_NOT_ELIGIBLE, "locator must be a non-empty mapping")
    loc = _copy_mapping(locator)
    if not any(_non_empty_str(loc.get(k)) for k in ("path", "record_id", "field", "uri")):
        raise ModeOutputError(
            OUTPUT_NOT_ELIGIBLE, "locator must include a checkable path/record/field/uri"
        )
    return normalized, loc


def _assert_query_draft_boundary(draft: Mapping[str, Any]) -> None:
    for flag in QUERY_REQUIRED_FALSE_FLAGS:
        if flag not in draft or draft.get(flag) is not False:
            raise ModeOutputError(
                OUTPUT_NOT_ELIGIBLE,
                f"Query draft {flag} must be explicitly false",
            )
    for key in QUERY_FORBIDDEN_KEYS:
        if key in draft and draft.get(key) not in (None, "", False):
            raise ModeOutputError(
                OUTPUT_NOT_ELIGIBLE,
                f"Query draft must not carry external workflow field {key}",
            )
    for flag in QUERY_FORBIDDEN_TRUE_FLAGS:
        if flag in draft and draft.get(flag) is not False:
            raise ModeOutputError(
                OUTPUT_NOT_ELIGIBLE,
                f"Query draft {flag} must remain false (unsent/unclosed/draft-only)",
            )
    if draft.get("draft_state") != "draft":
        raise ModeOutputError(OUTPUT_NOT_ELIGIBLE, "draft_state must be 'draft'")


def _query_draft_id(draft: Mapping[str, Any]) -> str:
    fields = (
        "finding_id",
        "risk_id",
        "issue_id",
        "project_id",
        "run_id",
        "subject_id",
        "site_id",
        "scope_kind",
        "basis",
        "finding",
        "action",
        "data_cutoff",
        "source_revision_id",
        "evidence_refs",
        "locator",
    )
    return "qd-" + sha256_hex(
        canonical_bytes({field: copy.deepcopy(draft.get(field)) for field in fields})
    )[:32]


def _build_one_query_draft(
    run: Mapping[str, Any],
    finding: Mapping[str, Any],
) -> dict:
    if not isinstance(finding, Mapping):
        raise ModeOutputError(OUTPUT_NOT_ELIGIBLE, "finding must be a mapping")
    finding_id = _require_non_empty_str(
        finding.get("finding_id"), "finding_id", OUTPUT_NOT_ELIGIBLE
    )
    risk_id = _require_non_empty_str(
        finding.get("risk_id"), "risk_id", OUTPUT_NOT_ELIGIBLE
    )
    issue_id = _require_non_empty_str(
        finding.get("issue_id"),
        "issue_id",
        OUTPUT_NOT_ELIGIBLE,
    )
    subject_id, site_id, scope_kind = _finding_scope(finding)
    evidence_refs, locator = _finding_evidence(finding)

    # Cutoff / revision: finding may omit them (inherit run) but must not drift.
    f_cutoff = finding.get("data_cutoff", run.get("data_cutoff"))
    f_revision = finding.get("source_revision_id", run.get("source_revision_id"))
    if f_cutoff != run.get("data_cutoff"):
        raise ModeOutputError(CUTOFF_MISMATCH, "finding data_cutoff drifts from run")
    if f_revision != run.get("source_revision_id"):
        raise ModeOutputError(
            REVISION_MISMATCH, "finding source_revision_id drifts from run"
        )
    if finding.get("project_id") not in (None, run.get("project_id")):
        raise ModeOutputError(IDENTITY_MISMATCH, "finding project_id drifts from run")
    if finding.get("run_id") not in (None, run.get("run_id")):
        raise ModeOutputError(IDENTITY_MISMATCH, "finding run_id drifts from run")

    basis = _zh_clause(finding.get("basis"), QUERY_LABEL_BASIS)
    finding_text = _zh_clause(finding.get("finding"), QUERY_LABEL_FINDING)
    action = _zh_clause(finding.get("action"), QUERY_LABEL_ACTION)
    display_text = basis + finding_text + action

    id_payload = {
        "finding_id": finding_id,
        "risk_id": risk_id,
        "issue_id": issue_id,
        "project_id": run.get("project_id"),
        "run_id": run.get("run_id"),
        "subject_id": subject_id,
        "site_id": site_id,
        "scope_kind": scope_kind,
        "basis": basis,
        "finding": finding_text,
        "action": action,
        "data_cutoff": f_cutoff,
        "source_revision_id": f_revision,
        "evidence_refs": evidence_refs,
        "locator": locator,
    }
    # Stable id from canonical content (excluding generated id itself).
    query_draft_id = _query_draft_id(id_payload)

    draft = {
        "query_draft_id": query_draft_id,
        "finding_id": finding_id,
        "risk_id": risk_id,
        "issue_id": issue_id,
        "project_id": run.get("project_id"),
        "run_id": run.get("run_id"),
        "subject_id": subject_id,
        "site_id": site_id,
        "scope_kind": scope_kind,
        "basis": basis,
        "finding": finding_text,
        "action": action,
        "display_text": display_text,
        "evidence_refs": evidence_refs,
        "locator": locator,
        "data_cutoff": f_cutoff,
        "source_revision_id": f_revision,
        "draft_state": "draft",
        "is_sent": False,
        "is_closed": False,
        "is_user_confirmed": False,
        "is_pd_recorded": False,
        "is_pd_closed": False,
        "producer_kind": PRODUCER_SYSTEM,
    }
    # PD / prohibited-medication findings may enter the draft as wording only.
    finding_kind = finding.get("finding_kind")
    if _non_empty_str(finding_kind):
        draft["finding_kind"] = str(finding_kind)
    pd_wording = finding.get("pd_wording_state")
    if _non_empty_str(pd_wording):
        draft["pd_wording_state"] = str(pd_wording)

    _assert_query_draft_boundary(draft)
    if draft["display_text"] != draft["basis"] + draft["finding"] + draft["action"]:
        raise ModeOutputError(
            OUTPUT_NOT_ELIGIBLE, "display_text must equal basis+finding+action"
        )
    return draft


def build_affected_query_draft(
    run_binding: Mapping[str, Any],
    findings: Sequence[Mapping[str, Any]],
) -> dict:
    """Build the daily ``affected_query_draft`` payload from structured findings.

    Each draft keeps 依据/发现/行动项, a deterministic Chinese ``display_text``,
    evidence/locator/cutoff/revision/risk identity, and draft-only unsent/
    unclosed flags. PD-class findings may appear as wording only — never as
    registered/closed PD. Does not mutate inputs.
    """
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
    if run.get("mode") != "daily":
        raise ModeOutputError(
            OUTPUT_NOT_ELIGIBLE,
            "affected_query_draft is a daily default output",
        )
    if not isinstance(findings, Sequence) or isinstance(findings, (str, bytes)):
        raise ModeOutputError(OUTPUT_NOT_ELIGIBLE, "findings must be a sequence")

    drafts = [_build_one_query_draft(run, item) for item in findings]
    # Stable order by query_draft_id for byte-stable payloads.
    drafts.sort(key=lambda d: d["query_draft_id"])
    return {
        "output_kind": "affected_query_draft",
        "project_id": run["project_id"],
        "run_id": run["run_id"],
        "mode": "daily",
        "data_cutoff": run["data_cutoff"],
        "source_revision_id": run["source_revision_id"],
        "query_drafts": drafts,
        "draft_count": len(drafts),
        "is_sent": False,
        "is_closed": False,
        "is_user_confirmed": False,
        "pd_registration_allowed": False,
        "external_dispatch_allowed": False,
    }


def _default_payload_for_kind(
    output_kind: str,
    run: Mapping[str, Any],
    authority_refs: Mapping[str, Any],
    output_spec: Mapping[str, Any],
) -> dict:
    if output_kind == "affected_query_draft":
        findings = output_spec.get("findings") or []
        return build_affected_query_draft(run, findings)

    if output_kind in PRE_LOCK_OUTPUT_KINDS:
        return _default_pre_lock_payload_for_kind(
            output_kind, run, authority_refs, output_spec
        )

    if output_kind in POST_LOCK_OUTPUT_KINDS:
        return _default_post_lock_payload_for_kind(
            output_kind, run, authority_refs, output_spec
        )

    shared = {
        "authority_digest": authority_refs.get("digest")
        or authority_refs.get("authority_digest"),
        "project_id": run.get("project_id"),
        "run_id": run.get("run_id"),
        "data_cutoff": run.get("data_cutoff"),
        "source_revision_id": run.get("source_revision_id"),
    }
    if output_kind == "change_summary":
        changes = output_spec.get("changes")
        if changes is None:
            changes = []
        if not isinstance(changes, list):
            raise ModeOutputError(OUTPUT_NOT_ELIGIBLE, "changes must be a list")
        return {
            "output_kind": output_kind,
            "change_kinds": ["clinical_data", "knowledge_rule_mapping_model", "user_decision"],
            "changes": copy.deepcopy(changes),
            **shared,
        }
    if output_kind == "current_full_risk":
        risks = output_spec.get("risks")
        if risks is None:
            risks = []
        if not isinstance(risks, list):
            raise ModeOutputError(OUTPUT_NOT_ELIGIBLE, "risks must be a list")
        numeric = output_spec.get("numeric")
        if numeric is not None and not isinstance(numeric, Mapping):
            raise ModeOutputError(OUTPUT_NOT_ELIGIBLE, "numeric must be a mapping")
        return {
            "output_kind": output_kind,
            "risks": copy.deepcopy(list(risks)),
            "numeric": copy.deepcopy(dict(numeric or {})),
            "coverage_note": "current_full_risk bound to accepted full snapshot",
            **shared,
        }
    if output_kind == "data_knowledge_rule_model_change_note":
        notes = output_spec.get("change_notes")
        if notes is None:
            notes = []
        if not isinstance(notes, list):
            raise ModeOutputError(OUTPUT_NOT_ELIGIBLE, "change_notes must be a list")
        return {
            "output_kind": output_kind,
            "change_notes": copy.deepcopy(list(notes)),
            "distinguishes_clinical_from_knowledge": True,
            **shared,
        }
    # Non-daily / non-pre_lock kinds: envelope-only payload with kind marker.
    return {"output_kind": output_kind, **shared}


def _numeric_near(a: Any, b: Any) -> bool:
    try:
        fa, fb = float(a), float(b)
    except (TypeError, ValueError):
        return False
    return abs(fa - fb) <= max(1e-12, 1e-9 * max(abs(fa), abs(fb), 1.0))


def _validate_numeric_payload(
    payload: Mapping[str, Any], run: Mapping[str, Any], codes: list[str]
) -> None:
    numeric = payload.get("numeric")
    if not isinstance(numeric, Mapping):
        _append(codes, OUTPUT_NOT_ELIGIBLE)
        return
    for row in numeric.values():
        if not isinstance(row, Mapping):
            _append(codes, OUTPUT_NOT_ELIGIBLE)
            continue
        raw = row.get("raw")
        numerator = row.get("numerator")
        denominator = row.get("denominator")
        if raw is None or numerator is None or denominator is None:
            _append(codes, OUTPUT_NOT_ELIGIBLE)
            continue
        try:
            numerator_value = float(numerator)
            denominator_value = float(denominator)
        except (TypeError, ValueError):
            _append(codes, OUTPUT_NOT_ELIGIBLE)
            continue
        if denominator_value <= 0 or not _numeric_near(
            raw, numerator_value / denominator_value
        ):
            _append(codes, AUTHORITY_MISMATCH)
        if row.get("count_kind") == "unique_subject" and numerator_value > denominator_value:
            _append(codes, AUTHORITY_MISMATCH)
        if row.get("data_cutoff") not in (None, run.get("data_cutoff")):
            _append(codes, CUTOFF_MISMATCH)
        if row.get("source_revision_id") not in (
            None,
            run.get("source_revision_id"),
        ):
            _append(codes, REVISION_MISMATCH)

    risks = payload.get("risks")
    if not isinstance(risks, list):
        _append(codes, OUTPUT_NOT_ELIGIBLE)
        return
    for risk in risks:
        if not isinstance(risk, Mapping):
            _append(codes, OUTPUT_NOT_ELIGIBLE)
            continue
        quantitative_keys = {
            "raw_rate",
            "rate",
            "raw",
            "raw_value",
            "pct",
            "percentage",
            "numerator",
            "denominator",
        }
        if not quantitative_keys.intersection(risk):
            continue
        metric_id = risk.get("metric_id")
        row = numeric.get(metric_id) if _non_empty_str(metric_id) else None
        if not isinstance(row, Mapping):
            _append(codes, AUTHORITY_MISMATCH)
            continue
        for key in ("raw_rate", "rate", "raw", "raw_value", "pct", "percentage"):
            if key in risk and not _numeric_near(risk.get(key), row.get("raw")):
                _append(codes, AUTHORITY_MISMATCH)
        if "numerator" in risk or "denominator" in risk:
            try:
                numerator = float(risk.get("numerator"))
                denominator = float(risk.get("denominator"))
            except (TypeError, ValueError):
                _append(codes, OUTPUT_NOT_ELIGIBLE)
            else:
                if denominator <= 0 or not _numeric_near(
                    numerator / denominator, row.get("raw")
                ):
                    _append(codes, AUTHORITY_MISMATCH)


def _validate_change_entries(
    payload: Mapping[str, Any], field: str, codes: list[str]
) -> None:
    entries = payload.get(field)
    allowed = {"clinical_data", "knowledge_rule_mapping_model", "user_decision"}
    if not isinstance(entries, list):
        _append(codes, OUTPUT_NOT_ELIGIBLE)
        return
    for entry in entries:
        if not isinstance(entry, Mapping) or entry.get("change_kind") not in allowed:
            _append(codes, AUTHORITY_MISMATCH)


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


# ---------------------------------------------------------------------------
# Slice-05 — pre_lock four default ModeOutputs (reuse ModeOutput envelope)
# ---------------------------------------------------------------------------


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


# ---------------------------------------------------------------------------
# Slice-06 — post_lock_pre_cfdi four fixed-total ModeOutputs
# ---------------------------------------------------------------------------


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
