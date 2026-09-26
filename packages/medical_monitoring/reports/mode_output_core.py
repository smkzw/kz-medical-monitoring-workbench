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


def _build_one_finding_record(
    run: Mapping[str, Any],
    finding: Mapping[str, Any],
    draft: Mapping[str, Any],
) -> dict:
    """W01-R26 A12：从同一条structured finding构建冻结Finding DTO。

    Finding与QueryDraft分离：Finding携带稳定ID、subject/site、事件与时间
    窗、状态、分类型claims与逐条source refs，供公开结果卡直接导航；
    QueryDraft保留自身query_draft_id并以finding_id引用该Finding。
    """

    def _optional_text(value: Any) -> str:
        return str(value).strip() if _non_empty_str(value) else ""

    finding_state = _optional_text(finding.get("finding_state")) or "open"
    record = {
        "finding_id": draft["finding_id"],
        "risk_id": draft["risk_id"],
        "issue_id": draft["issue_id"],
        "project_id": draft["project_id"],
        "run_id": draft["run_id"],
        "subject_id": draft["subject_id"],
        "site_id": draft["site_id"],
        "scope_kind": draft["scope_kind"],
        "event_ref": _optional_text(finding.get("event_ref")),
        "window_start": _optional_text(finding.get("window_start")),
        "window_end": _optional_text(finding.get("window_end")),
        "finding_state": finding_state,
        "claims": [
            {"kind": "basis", "text": draft["basis"]},
            {"kind": "finding", "text": draft["finding"]},
            {"kind": "action", "text": draft["action"]},
        ],
        "source_refs": _copy_mapping({"refs": draft["evidence_refs"]})["refs"],
        "locator": _copy_mapping(draft["locator"]),
        "data_cutoff": draft["data_cutoff"],
        "source_revision_id": draft["source_revision_id"],
    }
    finding_kind = finding.get("finding_kind")
    if _non_empty_str(finding_kind):
        record["finding_kind"] = str(finding_kind)
    pd_wording = finding.get("pd_wording_state")
    if _non_empty_str(pd_wording):
        record["pd_wording_state"] = str(pd_wording)
    return record


def build_affected_query_draft(
    run: Mapping[str, Any],
    findings: Sequence[Mapping[str, Any]],
) -> dict:
    """Build the daily ``affected_query_draft`` payload from structured findings.

    Each draft keeps 依据/发现/行动项, a deterministic Chinese ``display_text``,
    evidence/locator/cutoff/revision/risk identity, and draft-only unsent/
    unclosed flags. PD-class findings may appear as wording only — never as
    registered/closed PD.

    W01-R26 A12：payload同时携带平行的冻结``findings``数组（Finding DTO，
    含稳定ID/subject/site/事件与时间窗/状态/分类型claims/逐条source refs），
    空集也显式写``findings: []``；QueryDraft保留自身ID并以finding_id引用。
    Does not mutate inputs.
    """
    if not isinstance(run, Mapping):
        raise ModeOutputError(IDENTITY_MISMATCH, "run_binding must be a mapping")
    run = _copy_mapping(run)
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

    drafts = []
    finding_records = []
    seen_finding_ids: set = set()
    for item in findings:
        draft = _build_one_query_draft(run, item)
        finding_id = draft["finding_id"]
        if finding_id in seen_finding_ids:
            raise ModeOutputError(
                OUTPUT_NOT_ELIGIBLE,
                f"duplicate finding_id {finding_id} in daily findings",
            )
        seen_finding_ids.add(finding_id)
        drafts.append(draft)
        finding_records.append(_build_one_finding_record(run, item, draft))
    # Stable order by query_draft_id / finding_id for byte-stable payloads.
    drafts.sort(key=lambda d: d["query_draft_id"])
    finding_records.sort(key=lambda item: item["finding_id"])
    return {
        "output_kind": "affected_query_draft",
        "project_id": run["project_id"],
        "run_id": run["run_id"],
        "mode": "daily",
        "data_cutoff": run["data_cutoff"],
        "source_revision_id": run["source_revision_id"],
        "query_drafts": drafts,
        "draft_count": len(drafts),
        "findings": finding_records,
        "finding_count": len(finding_records),
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
