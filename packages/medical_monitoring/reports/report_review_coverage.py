"""Coverage accounting and full-report-review eligibility for R6 reports."""
from __future__ import annotations

import copy
from typing import Any, Mapping, Sequence, Tuple

from .report_review import (
    EVIDENCE_RELATIONS, _copy_mapping, _stable_unique, canonical_bytes,
    sha256_hex, validate_object_cross_identity,
)

# ---------------------------------------------------------------------------
# Coverage / ClaimCoverageLedger surface (worker_02)
# ---------------------------------------------------------------------------
#
# Authority: R6 v0.1 prose contract §§4.5, 5, 6 (reviews/medical_
# monitoring_r6_external_report_mode_output_contract_v0_1_20260827.md) and
# contract.json ``claim_issue_coverage`` / ``objects`` (artifacts/medical_
# monitoring_r6_external_report_mode_output_contract_v0_1/contract.json).
#
# Design notes (intentional and frozen):
#
# * The frozen expected unit set is the ``units`` list carried in the
#   matrix. Ledger ``entries`` are derived deterministically from the units
#   plus the claim/issue unit links. Per-unit review annotations
#   (``anchor_status``, ``coverage_status``, ``coverage_reason``) ride on
#   the unit mapping; a missing ``anchor_status`` fails closed to
#   ``unverified`` (verification is never fabricated).
# * Double gate (contract §6.3): ``coverage_closed`` means the accounting
#   is closed (expected set non-empty and one-to-one, statuses canonical,
#   reasoned not_evaluable, all links resolved, identity intact).
#   ``full_report_reviewed_eligible`` requires coverage_closed plus no
#   full-eligibility blocker (reverse omission, partial/truncated/
#   not_evaluable entries, unverified required anchors, cutoff/revision
#   conflicts, missing comparison evidence, failed three-piece QC). A
#   reasoned ``not_evaluable`` entry therefore closes the ledger without
#   making full review eligible.
# * Every blocking reason is accumulated (never first-error-only), deduped,
#   and emitted in sorted order. All codes are frozen contract vocabulary:
#   the 16 ``blocking_error_codes`` of contract.json plus the canonical
#   validator-level codes ``identity_mismatch``,
#   ``source_revision_mismatch``, ``source_not_immutable``,
#   ``issue_identity_invalid``, ``claim_not_evaluable``,
#   ``coverage_incomplete``, and ``output_not_eligible``. No synonyms are
#   invented.
# * ``coverage_incomplete`` is emitted for every ``not_evaluable`` entry
#   (reasoned or not) because §6.3 predicate 2 bars full-report eligibility
#   while the accounting may still close; ``unreasoned_not_evaluable``
#   additionally blocks ``coverage_closed`` when the reason is missing.

COVERAGE_STATUSES = frozenset(
    {"claimed", "no_claim", "not_evaluable", "partial", "truncated"}
)
ANCHOR_STATUSES = frozenset(
    {"verified", "unverified", "broken", "not_applicable"}
)
EXPECTATION_KINDS = frozenset(
    {"accepted_risk", "accepted_metric", "protocol_control_point"}
)
BUNDLE_STATES = frozenset({"assembled", "qc_blocked", "qc_passed"})
MODES = frozenset({"daily", "pre_lock", "post_lock_pre_cfdi"})
EXECUTION_BASES = frozenset({"full", "incremental"})

# The 16 canonical coverage blocking codes, in contract.json order.
BLOCKING_ERROR_CODES = (
    "expected_set_missing",
    "expected_unit_missing",
    "duplicate_unit_entry",
    "unexpected_unit_entry",
    "reverse_omission_uncovered",
    "invalid_coverage_status",
    "unreasoned_not_evaluable",
    "partial_unit",
    "truncated_unit",
    "claim_without_unit",
    "unit_claim_link_unknown",
    "issue_without_unit_or_evidence",
    "anchor_unverified",
    "cutoff_mismatch",
    "revision_mismatch",
    "evidence_comparison_missing",
)

# Codes that break the coverage accounting and therefore block
# coverage_closed. Object-identity codes are closed-scope: a matrix whose
# identity is broken cannot be trusted as an accounting record, so broken
# identity fails both gates (fail-closed).
COVERAGE_CLOSED_BLOCKING_CODES = frozenset(
    {
        "expected_set_missing",
    "expected_unit_missing",
    "duplicate_unit_entry",
    "unexpected_unit_entry",
    "invalid_coverage_status",
    "unreasoned_not_evaluable",
    "claim_without_unit",
    "unit_claim_link_unknown",
    "issue_without_unit_or_evidence",
    "identity_mismatch",
    "source_revision_mismatch",
    "source_not_immutable",
    "issue_identity_invalid",
    "revision_mismatch",
    }
)

# Codes that only block full_report_reviewed_eligible (the accounting may
# still close). Together with COVERAGE_CLOSED_BLOCKING_CODES these cover
# every code this module can emit, so full eligibility == no codes at all.
FULL_ELIGIBILITY_BLOCKING_CODES = frozenset(
    {
        "reverse_omission_uncovered",
    "coverage_incomplete",
    "partial_unit",
    "truncated_unit",
    "anchor_unverified",
    "cutoff_mismatch",
    "revision_mismatch",
    "evidence_comparison_missing",
        "claim_not_evaluable",
        "output_not_eligible",
    }
)

# Additional matrix fields required by this slice (the contract requires a
# superset over the 14 contract-required fields): content-addressed id, the
# frozen expected unit set, and the derived coverage entries.
MATRIX_EXTRA_FIELDS = ("matrix_id", "units", "entries")

LEDGER_REQUIRED_FIELDS = (
    "ledger_id",
    "run_id",
    "project_id",
    "report_lineage_id",
    "report_revision_id",
    "report_source_revision_id",
    "report_artifact_id",
    "expected_unit_set_hash",
    "expected_unit_count",
    "entries",
    "claims",
    "claim_unit_links",
    "issue_unit_links",
    "coverage_closed",
    "coverage_counts",
    "full_report_reviewed_eligible",
    "blocking_reasons",
)

# Common run binding fields (contract.json common_binding.required_fields).
COMMON_BINDING_REQUIRED = (
    "project_id",
    "run_id",
    "mode",
    "execution_basis",
    "data_cutoff",
    "source_revision_id",
    "knowledge_pack_version",
    "rule_activation_version",
    "mapping_version",
    "identity_algorithm_version",
    "identity_algorithm_digest",
    "schema_version",
)

# ReportReviewMatrix contract-required fields (contract.json objects).
MATRIX_REQUIRED_FIELDS = (
    "source_identity",
    "run_binding",
    "claims",
    "claim_unit_links",
    "comparisons",
    "issues",
    "expected_review_surface",
    "expected_review_surface_hash",
    "reverse_coverage_links",
    "coverage_ledger_id",
    "revision_diff",
    "unresolved_conflicts",
    "qc",
    "output_eligibility",
)

EXPECTED_SURFACE_ENTRY_REQUIRED = (
    "expectation_id",
    "expectation_kind",
    "authority_ref",
    "scope",
    "temporal_window",
)
REVERSE_LINK_REQUIRED = (
    "expectation_id",
    "claim_ids",
    "issue_ids",
    "not_evaluable_exception",
    "evidence_refs",
)
NOT_EVALUABLE_EXCEPTION_REQUIRED = ("reason", "report_scope", "evidence_refs")
LEDGER_ENTRY_REQUIRED = (
    "unit_id",
    "unit_type",
    "parent_unit_id",
    "required",
    "locator",
    "extractability",
    "anchor_status",
    "coverage_status",
    "claim_ids",
    "issue_ids",
    "reason",
)
# Unit fields produced by build_report_unit that the matrix consumes.
UNIT_REQUIRED_FIELDS = (
    "unit_id",
    "unit_type",
    "report_revision_id",
    "parent_unit_id",
    "required",
    "locator",
    "extractability",
    "anchor_digest",
)
CLAIM_REQUIRED_FIELDS = (
    "claim_id",
    "claim_identity_key",
    "report_lineage_id",
    "report_revision_id",
    "report_source_revision_id",
    "project_id",
    "run_id",
    "unit_ids",
    "claim_kind",
    "source_text",
    "normalized_claim_concept",
    "scope",
    "temporal_window",
    "report_cutoff",
    "report_cutoff_status",
    "status",
    "evidence_refs",
    "issue_ids",
    "locator",
)
ISSUE_REQUIRED_FIELDS = (
    "issue_id",
    "issue_identity_key",
    "project_id",
    "run_id",
    "report_lineage_id",
    "report_revision_id",
    "report_source_revision_id",
    "issue_kind",
    "claim_ids",
    "unit_ids",
    "severity",
    "clinical_or_document_scope",
    "evidence_refs",
    "source_locators",
    "lifecycle_state",
    "revision_diff_state",
    "related_issue_ids",
    "transition_refs",
    "current_note",
)

# Anchor statuses that satisfy "all required anchors are verified" for full
# eligibility: not_applicable means the unit has no anchor to verify;
# unverified/broken block (contract §6.3 predicate 3, §3.4).
_ANCHORS_ELIGIBLE = frozenset({"verified", "not_applicable"})
# Extractability values under which a unit may be claimed or inspected clean;
# claimed/no_claim on an unextractable/unknown unit is an invalid status
# (contract §6.2: such units can only be not_evaluable).
_EXTRACTABLE = frozenset({"text", "table", "vector", "image", "ocr"})


def _sorted_dicts(values: Sequence[Mapping[str, Any]], key: str) -> list:
    """Copy mappings and return a deterministic identity-key order."""
    copied = [_copy_mapping(value) for value in values]
    return sorted(copied, key=lambda value: str(value.get(key, "")))


def _content_id(prefix: str, payload: Mapping[str, Any]) -> str:
    return f"{prefix}-{sha256_hex(canonical_bytes(payload))}"


def _coverage_entries(
    units: Sequence[Mapping[str, Any]],
    claims: Sequence[Mapping[str, Any]],
    issues: Sequence[Mapping[str, Any]],
) -> list:
    claim_links: dict[str, list[str]] = {}
    issue_links: dict[str, list[str]] = {}
    for claim in claims:
        for unit_id in claim.get("unit_ids") or []:
            claim_links.setdefault(str(unit_id), []).append(str(claim.get("claim_id", "")))
    for issue in issues:
        for unit_id in issue.get("unit_ids") or []:
            issue_links.setdefault(str(unit_id), []).append(str(issue.get("issue_id", "")))

    entries = []
    for unit in units:
        unit_id = unit.get("unit_id")
        entries.append(
            {
                "unit_id": unit_id,
                "unit_type": unit.get("unit_type"),
                "parent_unit_id": unit.get("parent_unit_id"),
                "required": unit.get("required"),
                "locator": copy.deepcopy(unit.get("locator")),
                "extractability": unit.get("extractability"),
                "anchor_status": unit.get("anchor_status", "unverified"),
                "coverage_status": unit.get("coverage_status", "not_evaluable"),
                "claim_ids": sorted(set(claim_links.get(str(unit_id), []))),
                "issue_ids": sorted(set(issue_links.get(str(unit_id), []))),
                "reason": unit.get("coverage_reason"),
            }
        )
    return sorted(entries, key=lambda entry: str(entry.get("unit_id", "")))


def _coverage_blockers(matrix: Mapping[str, Any]) -> Tuple[str, ...]:
    """Accumulate every frozen coverage/identity blocker in stable order."""
    codes: list[str] = []

    def add(code: str) -> None:
        codes.append(code)

    def meaningful(value: Any) -> bool:
        return bool(value.strip()) if isinstance(value, str) else bool(value)

    def evidence_refs_valid(value: Any) -> bool:
        if not isinstance(value, list) or not value:
            return False
        required = (
            "evidence_id", "authority_class", "snapshot_id", "data_cutoff",
            "locator", "content_hash", "relation",
        )
        for ref in value:
            if not isinstance(ref, Mapping):
                return False
            if any(not meaningful(ref.get(field)) for field in required):
                return False
            if ref.get("relation") not in EVIDENCE_RELATIONS:
                return False
            if not (meaningful(ref.get("source_revision_id")) or meaningful(ref.get("authority_artifact_id"))):
                return False
        return True

    source = matrix.get("source_identity")
    binding = matrix.get("run_binding")
    units = matrix.get("units")
    entries = matrix.get("entries")
    claims = matrix.get("claims")
    issues = matrix.get("issues")
    surface = matrix.get("expected_review_surface")
    reverse = matrix.get("reverse_coverage_links")
    if not isinstance(source, Mapping) or not isinstance(binding, Mapping):
        return ("identity_mismatch",)
    if not isinstance(units, list):
        units = []
        add("expected_set_missing")
    if not isinstance(entries, list):
        entries = []
        add("expected_unit_missing")
    if not isinstance(claims, list):
        claims = []
        add("claim_without_unit")
    if not isinstance(issues, list):
        issues = []
        add("issue_without_unit_or_evidence")

    for field in COMMON_BINDING_REQUIRED:
        value = binding.get(field)
        if not isinstance(value, str) or not value:
            add("identity_mismatch")
    if binding.get("mode") not in MODES or binding.get("execution_basis") not in EXECUTION_BASES:
        add("identity_mismatch")
    if binding.get("project_id") != source.get("project_id"):
        add("identity_mismatch")
    if binding.get("source_revision_id") in {
        source.get("source_revision_id"),
        source.get("report_source_revision_id"),
    }:
        add("identity_mismatch")

    codes.extend(
        validate_object_cross_identity(
            source,
            units,
            claims,
            issues,
            run_source_revision_id=binding.get("source_revision_id"),
        )
    )

    unit_ids = [unit.get("unit_id") for unit in units]
    expected = set(unit_ids)
    if not expected:
        add("expected_set_missing")
    if len(unit_ids) != len(expected):
        add("duplicate_unit_entry")

    parent_by_id = {
        unit.get("unit_id"): unit.get("parent_unit_id")
        for unit in units
        if isinstance(unit, Mapping) and unit.get("unit_id")
    }
    for start in parent_by_id:
        seen: set[str] = set()
        current = start
        while current is not None and current in parent_by_id:
            if current in seen:
                add("identity_mismatch")
                break
            seen.add(current)
            current = parent_by_id[current]

    entry_ids = [entry.get("unit_id") for entry in entries if isinstance(entry, Mapping)]
    entry_set = set(entry_ids)
    if len(entry_ids) != len(entry_set):
        add("duplicate_unit_entry")
    if expected - entry_set:
        add("expected_unit_missing")
    if entry_set - expected:
        add("unexpected_unit_entry")

    claim_by_id = {
        claim.get("claim_id"): claim
        for claim in claims
        if isinstance(claim, Mapping) and claim.get("claim_id")
    }
    issue_by_id = {
        issue.get("issue_id"): issue
        for issue in issues
        if isinstance(issue, Mapping) and issue.get("issue_id")
    }
    for entry in entries:
        if not isinstance(entry, Mapping):
            add("invalid_coverage_status")
            continue
        status = entry.get("coverage_status")
        if status not in COVERAGE_STATUSES:
            add("invalid_coverage_status")
        if status == "not_evaluable":
            add("coverage_incomplete")
            if not entry.get("reason"):
                add("unreasoned_not_evaluable")
        if status == "partial":
            add("partial_unit")
            if not entry.get("reason"):
                add("coverage_incomplete")
        if status == "truncated":
            add("truncated_unit")
            if not entry.get("reason"):
                add("coverage_incomplete")
        if entry.get("required") is True and entry.get("anchor_status") not in _ANCHORS_ELIGIBLE:
            add("anchor_unverified")
        if status in {"claimed", "no_claim"} and entry.get("extractability") not in _EXTRACTABLE:
            add("invalid_coverage_status")
        linked_claims = entry.get("claim_ids") or []
        if status == "claimed" and not linked_claims:
            add("claim_without_unit")
        if status == "no_claim" and linked_claims:
            add("invalid_coverage_status")
        for claim_id in linked_claims:
            if claim_id not in claim_by_id:
                add("unit_claim_link_unknown")
        for issue_id in entry.get("issue_ids") or []:
            if issue_id not in issue_by_id:
                add("issue_without_unit_or_evidence")

    report_cutoff = source.get("reported_data_cutoff")
    if source.get("reported_cutoff_status") != "declared" or report_cutoff != binding.get("data_cutoff"):
        add("cutoff_mismatch")
    for claim in claims:
        refs = claim.get("evidence_refs") or []
        if not refs:
            add("evidence_comparison_missing")
        matching = False
        for ref in refs:
            if not isinstance(ref, Mapping):
                continue
            if (
                ref.get("data_cutoff") == binding.get("data_cutoff")
                and ref.get("source_revision_id") == binding.get("source_revision_id")
                and ref.get("relation") in EVIDENCE_RELATIONS
            ):
                matching = True
        if not matching:
            add("evidence_comparison_missing")
        if claim.get("status") == "not_evaluable":
            add("claim_not_evaluable")

    if not isinstance(surface, list) or not surface:
        add("reverse_omission_uncovered")
        surface = []
    expected_surface_hash = sha256_hex(canonical_bytes(surface))
    if matrix.get("expected_review_surface_hash") != expected_surface_hash:
        add("identity_mismatch")
    expectation_ids = [item.get("expectation_id") for item in surface if isinstance(item, Mapping)]
    if len(expectation_ids) != len(set(expectation_ids)):
        add("duplicate_unit_entry")
    for expectation in surface:
        if not isinstance(expectation, Mapping):
            add("identity_mismatch")
            continue
        if any(not meaningful(expectation.get(field)) for field in EXPECTED_SURFACE_ENTRY_REQUIRED):
            add("identity_mismatch")
        if expectation.get("expectation_kind") not in EXPECTATION_KINDS:
            add("identity_mismatch")
    reverse = reverse if isinstance(reverse, list) else []
    reverse_ids = [item.get("expectation_id") for item in reverse if isinstance(item, Mapping)]
    if set(reverse_ids) != set(expectation_ids) or len(reverse_ids) != len(expectation_ids):
        add("reverse_omission_uncovered")
    for link in reverse:
        if not isinstance(link, Mapping):
            add("reverse_omission_uncovered")
            continue
        exception = link.get("not_evaluable_exception")
        has_exception = (
            isinstance(exception, Mapping)
            and meaningful(exception.get("reason"))
            and meaningful(exception.get("report_scope"))
            and evidence_refs_valid(exception.get("evidence_refs"))
        )
        if not (link.get("claim_ids") or link.get("issue_ids") or has_exception):
            add("reverse_omission_uncovered")
        if not evidence_refs_valid(link.get("evidence_refs")):
            add("evidence_comparison_missing")
        if isinstance(exception, Mapping) and not has_exception:
            add("evidence_comparison_missing")
        for claim_id in link.get("claim_ids") or []:
            if claim_id not in claim_by_id:
                add("unit_claim_link_unknown")
        for issue_id in link.get("issue_ids") or []:
            if issue_id not in issue_by_id:
                add("issue_without_unit_or_evidence")

    if matrix.get("unresolved_conflicts"):
        add("revision_mismatch")
    return _stable_unique(codes)


def _ledger_payload(matrix: Mapping[str, Any], codes: Sequence[str]) -> dict:
    source = matrix["source_identity"]
    binding = matrix["run_binding"]
    entries = copy.deepcopy(matrix.get("entries") or [])
    units = matrix.get("units") or []
    expected_ids = sorted(str(unit.get("unit_id")) for unit in units)
    expected_hash = sha256_hex(canonical_bytes(expected_ids))
    coverage_counts = {status: 0 for status in sorted(COVERAGE_STATUSES)}
    for entry in entries:
        status = entry.get("coverage_status")
        if status in coverage_counts:
            coverage_counts[status] += 1
    closed = not bool(set(codes) & COVERAGE_CLOSED_BLOCKING_CODES)
    eligible = closed and not bool(codes)
    return {
        "run_id": binding.get("run_id"),
        "project_id": binding.get("project_id"),
        "report_lineage_id": source.get("report_lineage_id"),
        "report_revision_id": source.get("report_revision_id"),
        "report_source_revision_id": source.get("report_source_revision_id"),
        "report_artifact_id": source.get("report_artifact_id"),
        "expected_unit_set_hash": expected_hash,
        "expected_unit_count": len(expected_ids),
        "entries": entries,
        "claims": copy.deepcopy(matrix.get("claims") or []),
        "claim_unit_links": copy.deepcopy(matrix.get("claim_unit_links") or []),
        "issue_unit_links": [
            {"issue_id": issue.get("issue_id"), "unit_ids": sorted(set(issue.get("unit_ids") or []))}
            for issue in matrix.get("issues") or []
        ],
        "coverage_closed": closed,
        "coverage_counts": coverage_counts,
        "full_report_reviewed_eligible": eligible,
        "blocking_reasons": list(codes),
    }


def build_report_review_matrix(
    binding: Mapping[str, Any],
    report_source: Mapping[str, Any],
    units: Sequence[Mapping[str, Any]],
    claims: Sequence[Mapping[str, Any]],
    issues: Sequence[Mapping[str, Any]],
    expected_review_surface: Sequence[Mapping[str, Any]],
    reverse_coverage_links: Sequence[Mapping[str, Any]],
) -> dict:
    """Build the canonical synthetic/offline report-review matrix."""
    source = _copy_mapping(report_source)
    run_binding = _copy_mapping(binding)
    copied_units = _sorted_dicts(units, "unit_id")
    copied_claims = _sorted_dicts(claims, "claim_id")
    copied_issues = _sorted_dicts(issues, "issue_id")
    surface = _sorted_dicts(expected_review_surface, "expectation_id")
    reverse = _sorted_dicts(reverse_coverage_links, "expectation_id")
    entries = _coverage_entries(copied_units, copied_claims, copied_issues)
    matrix = {
        "artifact_type": "report_review_matrix",
        "payload_role": "report_review",
        "source_identity": source,
        "run_binding": run_binding,
        "units": copied_units,
        "entries": entries,
        "claims": copied_claims,
        "claim_unit_links": [
            {"claim_id": claim.get("claim_id"), "unit_ids": sorted(set(claim.get("unit_ids") or []))}
            for claim in copied_claims
        ],
        "comparisons": [
            {
                "claim_id": claim.get("claim_id"),
                "evidence_refs": copy.deepcopy(claim.get("evidence_refs") or []),
            }
            for claim in copied_claims
        ],
        "issues": copied_issues,
        "expected_review_surface": surface,
        "expected_review_surface_hash": sha256_hex(canonical_bytes(surface)),
        "reverse_coverage_links": reverse,
        "coverage_ledger_id": "",
        "revision_diff": [],
        "unresolved_conflicts": [],
        "qc": {"state": "assembled"},
        "output_eligibility": {"eligible": False, "blocking_reasons": []},
    }
    codes = _coverage_blockers(matrix)
    ledger_payload = _ledger_payload(matrix, codes)
    matrix["coverage_ledger_id"] = _content_id("ledger", ledger_payload)
    matrix["qc"] = {"state": "qc_passed" if not codes else "qc_blocked"}
    matrix["output_eligibility"] = {
        "eligible": not bool(codes),
        "blocking_reasons": list(codes),
    }
    matrix["matrix_id"] = _content_id("matrix", matrix)
    return matrix


def validate_report_review_matrix(matrix: Mapping[str, Any]) -> Tuple[str, ...]:
    """Return all deterministic blockers, including stored-hash tamper checks."""
    if not isinstance(matrix, Mapping):
        return ("identity_mismatch",)
    copied = _copy_mapping(matrix)
    codes = list(_coverage_blockers(copied))
    try:
        payload = _ledger_payload(copied, codes)
        if copied.get("coverage_ledger_id") != _content_id("ledger", payload):
            codes.append("identity_mismatch")
        stored_matrix_id = copied.pop("matrix_id", None)
        if stored_matrix_id != _content_id("matrix", copied):
            codes.append("identity_mismatch")
    except (KeyError, TypeError, ValueError):
        codes.append("identity_mismatch")
    return _stable_unique(codes)


def build_claim_coverage_ledger(matrix: Mapping[str, Any]) -> dict:
    """Build the immutable coverage ledger and preserve the two distinct gates."""
    copied = _copy_mapping(matrix)
    codes = list(_coverage_blockers(copied))
    payload = _ledger_payload(copied, codes)
    ledger = {"ledger_id": _content_id("ledger", payload), **payload}
    if copied.get("coverage_ledger_id") != ledger["ledger_id"]:
        codes = list(_stable_unique([*codes, "identity_mismatch"]))
        payload = _ledger_payload(copied, codes)
        ledger = {"ledger_id": _content_id("ledger", payload), **payload}
    return ledger

