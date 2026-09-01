"""Minimal Python-stdlib 11-validator dispatcher and one-replace-per-row executor.

Implements work item 2 of the R6 v0.1 synthetic/offline runtime slice:

* apply exactly one RFC 6902 ``replace`` per challenge row to a deep copy of the
  frozen baseline fixture;
* dispatch every content validator for every challenge row;
* emit canonical ``failure_code``, ``blocking``, diagnostic code, ``outcome``,
  and ``projection`` only — no medical conclusions.

Validators inspect the post-mutation candidate document under ``/candidate``.
Where two rows share an identical post-mutation document (R6C-065 / R6C-066),
the executor also supplies the frozen ``baseline_value`` as mutation context so
the status-transition oracle remains deterministic. The challenge category is
projection metadata, not a validation boundary:
``category_validator_map_normative=false`` in the frozen contract. Every row
therefore runs all ten content validators; the governed execution audit owns
the eleventh boundary validator.

``R6-C-BOUNDARY-001`` is registered for completeness but is intentionally
outside the 12 content categories (audit-execution acceptor; see contract
``boundary_validator_policy``).

Stdlib only. Deterministic under any ``PYTHONHASHSEED`` and ``-O``/``-OO``.
"""

from __future__ import annotations

from typing import Callable, Iterable, List, Optional, Sequence, Tuple

from . import contracts, fixtures

CANDIDATE_ROOT = fixtures.CANDIDATE_ROOT

#: Outcomes that use ``block:`` rather than ``reject:`` (matrix oracle).
_BLOCK_DIAGNOSTICS = frozenset(
    {
        "REPORT_REVERSE_OMISSION_UNCOVERED",
        "REPORT_COVERAGE_INCOMPLETE",
    }
)

#: Daily mode allowed output_scope values (synthetic fixture convention).
_DAILY_ALLOWED_SCOPES = frozenset(
    {
        "delta_only",
        "delta_plus_current_full",
        "change_summary_plus_current_full_risk",
    }
)

#: Post-lock fixed cutoff / revision identities (synthetic fixture convention).
_POST_LOCK_CUTOFF = "cutoff-fixed-001"
_POST_LOCK_REVISION = "revision-fixed-001"
_PRIOR_REPORT_ROLE = "prior_report"
_IMMUTABLE_STATES = frozenset({"immutable", "immutable_frozen"})


class ValidatorError(RuntimeError):
    """Raised when the challenge executor violates the one-replace contract."""


class Finding:
    """One canonical validator finding (failure + diagnostic + blocking)."""

    __slots__ = ("validator_id", "failure_code", "diagnostic_code", "blocking")

    def __init__(
        self,
        validator_id: str,
        failure_code: str,
        diagnostic_code: str,
        blocking: bool,
    ) -> None:
        self.validator_id = validator_id
        self.failure_code = failure_code
        self.diagnostic_code = diagnostic_code
        self.blocking = bool(blocking)

    def as_dict(self) -> dict:
        return {
            "validator_id": self.validator_id,
            "failure_code": self.failure_code,
            "diagnostic_code": self.diagnostic_code,
            "blocking": self.blocking,
        }

    def __repr__(self) -> str:
        return (
            f"Finding({self.validator_id!r}, {self.failure_code!r}, "
            f"{self.diagnostic_code!r}, blocking={self.blocking})"
        )


class ChallengeResult:
    """Canonical executor output for one challenge row."""

    __slots__ = (
        "challenge_id",
        "category",
        "mutations_applied",
        "findings",
        "outcome",
        "error",
        "projection",
        "blocking",
        "record_token",
        "accept_token",
    )

    def __init__(
        self,
        challenge_id: str,
        category: str,
        mutations_applied: int,
        findings: Sequence[Finding],
        outcome: str,
        error: Optional[str],
        projection: str,
        blocking: bool,
        record_token: Optional[str] = None,
        accept_token: Optional[str] = None,
    ) -> None:
        self.challenge_id = challenge_id
        self.category = category
        self.mutations_applied = mutations_applied
        self.findings = tuple(findings)
        self.outcome = outcome
        self.error = error
        self.projection = projection
        self.blocking = blocking
        self.record_token = record_token
        self.accept_token = accept_token

    def as_dict(self) -> dict:
        return {
            "challenge_id": self.challenge_id,
            "category": self.category,
            "mutations_applied": self.mutations_applied,
            "findings": [f.as_dict() for f in self.findings],
            "outcome": self.outcome,
            "error": self.error,
            "projection": self.projection,
            "blocking": self.blocking,
            "record_token": self.record_token,
            "accept_token": self.accept_token,
        }


# ---------------------------------------------------------------------------
# error_code_map helpers
# ---------------------------------------------------------------------------

def build_diagnostic_index(matrix: dict) -> dict:
    """Map diagnostic_code → (validator_id, failure_code, blocking)."""
    index = {}
    for entry in matrix["error_code_map"]:
        for code in entry["diagnostic_codes"]:
            index[code] = (
                entry["validator_id"],
                entry["failure_code"],
                bool(entry["blocking"]),
            )
    return index


def finding_for(diagnostic_code: str, index: dict) -> Finding:
    if diagnostic_code not in index:
        raise ValidatorError(f"undeclared diagnostic: {diagnostic_code}")
    validator_id, failure_code, blocking = index[diagnostic_code]
    return Finding(validator_id, failure_code, diagnostic_code, blocking)


# ---------------------------------------------------------------------------
# RFC 6902 replace (exactly one)
# ---------------------------------------------------------------------------

def apply_one_replace(doc: dict, mutation: dict) -> dict:
    """Apply exactly one RFC 6902 ``replace``; fail-closed on any other op."""
    if not isinstance(mutation, dict):
        raise ValidatorError("mutation must be an object")
    if mutation.get("op") != "replace":
        raise ValidatorError(f"only replace is authorized, got op={mutation.get('op')!r}")
    path = mutation.get("path")
    if not isinstance(path, str) or not path.startswith("/"):
        raise ValidatorError(f"invalid mutation path: {path!r}")
    if "value" not in mutation:
        raise ValidatorError("mutation missing value")
    return fixtures.set_pointer(doc, path, mutation["value"])


# ---------------------------------------------------------------------------
# candidate accessors
# ---------------------------------------------------------------------------

def _cand(doc: dict) -> dict:
    node = doc.get(CANDIDATE_ROOT)
    if not isinstance(node, dict):
        raise ValidatorError("candidate document missing top-level 'candidate'")
    return node


def _get(node, *keys, default=None):
    cur = node
    for key in keys:
        if not isinstance(cur, dict) or key not in cur:
            return default
        cur = cur[key]
    return cur


def _locators(cand: dict) -> set:
    return set(cand.get("source_locators") or [])


def _ambiguous(cand: dict) -> set:
    return set(cand.get("ambiguous_locators") or [])


def _stale(cand: dict) -> set:
    return set(cand.get("stale_or_missing_locators") or [])


def _populations(cand: dict) -> set:
    return set(cand.get("populations") or [])


def _cutoffs(cand: dict) -> set:
    return set(cand.get("cutoff_registry") or [])


def _evidence_ids(cand: dict) -> set:
    return {e.get("evidence_id") for e in (cand.get("evidence_registry") or []) if isinstance(e, dict)}


def _claim_ids_in_registry(cand: dict) -> set:
    return {c.get("claim_id") for c in (cand.get("claim_registry") or []) if isinstance(c, dict)}


def _issue_ids(cand: dict) -> set:
    return {i.get("issue_id") for i in (cand.get("issue_registry") or []) if isinstance(i, dict)}


def _denom_entry(cand: dict, ref) -> Optional[dict]:
    if ref is None:
        return None
    registry = cand.get("denominator_registry") or {}
    entry = registry.get(ref)
    return entry if isinstance(entry, dict) else None


# ---------------------------------------------------------------------------
# individual validators (return list[Finding])
# ---------------------------------------------------------------------------

ValidatorFn = Callable[[dict, dict, Optional[dict]], List[Finding]]


def _claim_identity_collision(cand: dict, index: dict) -> List[Finding]:
    """Body claim_id must match the registry entry for unit body-001."""
    out: List[Finding] = []
    body_claim_id = _get(cand, "body", "paragraph", "claim", "claim_id")
    registered_for_body = None
    for entry in cand.get("claim_registry") or []:
        if isinstance(entry, dict) and "body-001" in (entry.get("unit_ids") or []):
            registered_for_body = entry.get("claim_id")
            break
    if (
        body_claim_id is not None
        and registered_for_body is not None
        and body_claim_id != registered_for_body
    ):
        out.append(finding_for("REPORT_CLAIM_IDENTITY_COLLISION", index))
    return out


def _v_id_001(cand: dict, index: dict, ctx: Optional[dict]) -> List[Finding]:
    """R6-C-ID-001: identity / claim-identity agreement."""
    out: List[Finding] = []
    identity = cand.get("identity") or {}
    risk = cand.get("risk") or {}
    source_revision = cand.get("source_revision") or {}
    run = cand.get("run") or {}

    out.extend(_claim_identity_collision(cand, index))

    # Source / run identity agreement.
    if risk.get("authority_run_ref") not in (None, identity.get("run_id"), run.get("run_id")):
        out.append(finding_for("REPORT_SOURCE_IDENTITY_MISMATCH", index))
    if source_revision.get("role") not in (None, _PRIOR_REPORT_ROLE):
        if source_revision.get("role") != _PRIOR_REPORT_ROLE:
            out.append(finding_for("REPORT_SOURCE_IDENTITY_MISMATCH", index))

    # Undeclared revision transition blocks output eligibility (cutoff_revision rows).
    if run.get("revision_transition") == "undeclared":
        out.append(finding_for("REPORT_OUTPUT_NOT_ELIGIBLE", index))
    return out


def _v_src_001(cand: dict, index: dict, ctx: Optional[dict]) -> List[Finding]:
    """R6-C-SRC-001: source revision / immutability."""
    out: List[Finding] = []
    identity = cand.get("identity") or {}
    source_revision = cand.get("source_revision") or {}
    revision = cand.get("revision") or {}
    revision_issue = cand.get("revision_issue") or {}
    original = cand.get("original_report") or {}

    src_id = source_revision.get("id")
    if src_id is not None and src_id != identity.get("report_revision_id"):
        out.append(finding_for("REPORT_SOURCE_REVISION_MISMATCH", index))

    parent = revision.get("parent_report_ref")
    expected_parent = revision.get("previous_report_revision_id")
    if parent is not None and expected_parent is not None and parent != expected_parent:
        out.append(finding_for("REPORT_REVISION_PARENT_MISMATCH", index))
    issue_parent = revision_issue.get("parent_report_ref")
    if (
        issue_parent is not None
        and expected_parent is not None
        and issue_parent != expected_parent
    ):
        out.append(finding_for("REPORT_REVISION_PARENT_MISMATCH", index))

    state = original.get("state")
    if state is not None and state not in _IMMUTABLE_STATES:
        out.append(finding_for("ORIGINAL_OVERWRITE_FORBIDDEN", index))
    return out


def _v_claim_001(cand: dict, index: dict, ctx: Optional[dict]) -> List[Finding]:
    """R6-C-CLAIM-001: claim/locator/evidence/cutoff/population/unit checks."""
    out: List[Finding] = []
    locs = _locators(cand)
    amb = _ambiguous(cand)
    cuts = _cutoffs(cand)
    evidence = _evidence_ids(cand)

    # Identity collision is mapped to R6-C-ID-001 but body rows only dispatch
    # CLAIM/COV; emit the diagnostic here so category-scoped dispatch still works.
    out.extend(_claim_identity_collision(cand, index))

    # Body claim
    body_claim = _get(cand, "body", "paragraph", "claim") or {}
    body_loc = body_claim.get("locator_ref")
    if body_loc is None or body_loc not in locs:
        if body_loc in amb:
            out.append(finding_for("REPORT_ANCHOR_AMBIGUOUS", index))
        else:
            out.append(finding_for("REPORT_CLAIM_LOCATOR_INVALID", index))
    refs = body_claim.get("evidence_refs")
    if isinstance(refs, list) and len(refs) == 0:
        out.append(finding_for("REPORT_CLAIM_EVIDENCE_MISSING", index))
    elif isinstance(refs, list):
        for rid in refs:
            if rid not in evidence:
                out.append(finding_for("REPORT_CLAIM_EVIDENCE_MISSING", index))
                break
    if body_claim.get("evidence_state") == "conflicted":
        out.append(finding_for("REPORT_EVIDENCE_CONFLICT", index))

    # no_claim cannot hide substantive unit content (mapped to COV-002; also needed
    # on table/figure/footnote categories that do not dispatch COV-002).
    for path_keys in (("table", "row"), ("figure",), ("footnote",)):
        node = _get(cand, *path_keys) or {}
        if node.get("coverage_status") == "no_claim":
            out.append(finding_for("REPORT_NO_CLAIM_INVALID", index))

    # Table claim locator / population
    table_claim = _get(cand, "table", "row", "claim") or {}
    table_loc = table_claim.get("locator_ref")
    if table_loc is None:
        out.append(finding_for("REPORT_CLAIM_LOCATOR_INVALID", index))
    elif table_loc not in locs:
        out.append(finding_for("REPORT_CLAIM_LOCATOR_INVALID", index))
    table_pop = table_claim.get("population_ref")
    table_denom_ref = _get(cand, "table", "summary", "denominator_ref")
    if table_denom_ref is None:
        out.append(finding_for("REPORT_DENOMINATOR_MISSING", index))
    else:
        denom = _denom_entry(cand, table_denom_ref)
        if denom and table_pop and denom.get("population_ref") and table_pop != denom.get("population_ref"):
            out.append(finding_for("REPORT_POPULATION_MISMATCH", index))

    # Figure caption locator / legend / series unit
    fig_cap_loc = _get(cand, "figure", "caption", "claim", "locator_ref")
    if fig_cap_loc is None:
        out.append(finding_for("REPORT_CLAIM_LOCATOR_INVALID", index))
    elif fig_cap_loc not in locs:
        out.append(finding_for("REPORT_CLAIM_LOCATOR_INVALID", index))
    legend_loc = _get(cand, "figure", "legend", "locator_ref")
    if legend_loc in amb:
        out.append(finding_for("REPORT_ANCHOR_AMBIGUOUS", index))
    elif legend_loc is not None and legend_loc not in locs and legend_loc not in amb:
        out.append(finding_for("REPORT_ANCHOR_NOT_IN_SOURCE", index))
    series_unit = _get(cand, "figure", "series", "unit")
    if series_unit is not None and series_unit not in ("percent", "proportion", "rate", "count"):
        out.append(finding_for("REPORT_UNIT_MISMATCH", index))

    # Footnote locator → membership (not claim-locator) when absent from source
    fn_loc = _get(cand, "footnote", "claim", "locator_ref")
    if fn_loc is None:
        out.append(finding_for("REPORT_CLAIM_LOCATOR_INVALID", index))
    elif fn_loc in amb:
        out.append(finding_for("REPORT_ANCHOR_AMBIGUOUS", index))
    elif fn_loc not in locs:
        out.append(finding_for("REPORT_ANCHOR_NOT_IN_SOURCE", index))

    # Denominator / rate / count / exposure
    denom_ref = _get(cand, "denominator", "ref")
    denom_value = _get(cand, "denominator", "value")
    denom_pop = _get(cand, "denominator", "population_ref")
    num_value = _get(cand, "numerator", "value")
    num_pop = _get(cand, "numerator", "population_ref")
    num_unit = _get(cand, "numerator", "unit")
    count_unit = _get(cand, "count", "unit")
    rate = cand.get("rate") or {}
    exposure = cand.get("exposure_rate") or {}

    if denom_ref is None:
        out.append(finding_for("REPORT_DENOMINATOR_MISSING", index))
    if exposure.get("exposure_denominator_ref") is None and "exposure_rate" in cand:
        # Only flag when exposure_rate object is present with a null ref.
        if "exposure_denominator_ref" in exposure and exposure.get("exposure_denominator_ref") is None:
            out.append(finding_for("REPORT_DENOMINATOR_MISSING", index))
    if isinstance(denom_value, (int, float)) and denom_value == 0:
        out.append(finding_for("REPORT_DENOMINATOR_ZERO", index))
    if (
        isinstance(num_value, (int, float))
        and isinstance(denom_value, (int, float))
        and denom_value > 0
        and num_value > denom_value
        and num_unit == _get(cand, "denominator", "unit")
        and num_pop == denom_pop
    ):
        out.append(finding_for("REPORT_NUMERATOR_DENOMINATOR_MISMATCH", index))
    if count_unit is not None and num_unit is not None and count_unit != num_unit:
        out.append(finding_for("REPORT_COUNT_SEMANTICS_MISMATCH", index))
    if count_unit is not None and _get(cand, "denominator", "unit") is not None:
        if count_unit != _get(cand, "denominator", "unit"):
            out.append(finding_for("REPORT_COUNT_SEMANTICS_MISMATCH", index))
    if denom_pop and num_pop and denom_pop != num_pop:
        out.append(finding_for("REPORT_POPULATION_MISMATCH", index))

    # Rate recompute (raw authoritative): numerator/denom must match reported display.
    if (
        isinstance(rate.get("numerator"), (int, float))
        and isinstance(denom_value, (int, float))
        and denom_value > 0
        and isinstance(rate.get("reported_value"), (int, float))
    ):
        raw = rate["numerator"] / denom_value
        precision = rate.get("display_precision")
        reported = rate["reported_value"]
        if isinstance(precision, int) and precision >= 0:
            display = round(raw, precision)
            # Fail when reported matches neither raw nor declared display rounding.
            if reported != display and abs(reported - raw) > 1e-12:
                out.append(finding_for("REPORT_RATE_RECOMPUTE_MISMATCH", index))
        elif abs(reported - raw) > 1e-12:
            out.append(finding_for("REPORT_RATE_RECOMPUTE_MISMATCH", index))

    # Cutoff
    cutoff_ref = _get(cand, "cutoff", "ref")
    identity_cutoff = _get(cand, "identity", "data_cutoff")
    if cutoff_ref is None:
        out.append(finding_for("REPORT_CUTOFF_MISSING", index))
    elif cutoff_ref not in cuts:
        out.append(finding_for("REPORT_CUTOFF_MISMATCH", index))
    elif identity_cutoff is not None and cutoff_ref != identity_cutoff:
        out.append(finding_for("REPORT_CUTOFF_MISMATCH", index))

    # Output claim_status transitions (needs mutation baseline for 065/066).
    claim_status = _get(cand, "output", "claim_status")
    baseline = None if ctx is None else ctx.get("baseline_value")
    if claim_status == "supported":
        if baseline == "outdated_wrong_cutoff":
            out.append(finding_for("REPORT_CUTOFF_MISMATCH", index))
        elif baseline == "unsupported":
            out.append(finding_for("REPORT_STATUS_EVIDENCE_MISMATCH", index))
        elif baseline not in (None, "supported") and ctx and ctx.get("path", "").endswith(
            "/output/claim_status"
        ):
            # Any other promotion into supported without matching evidence.
            out.append(finding_for("REPORT_STATUS_EVIDENCE_MISMATCH", index))

    # Aggregation: not_evaluable treated as zero
    if _get(cand, "aggregation", "not_evaluable_as_zero") is True:
        out.append(finding_for("REPORT_NOT_EVALUABLE_AS_ZERO", index))

    # HTML nearest-fallback policy
    if _get(cand, "html", "anchor_fallback_policy") not in (None, "none"):
        out.append(finding_for("REPORT_NEAREST_ANCHOR_FALLBACK_FORBIDDEN", index))

    return _dedupe(out)


def _v_issue_001(cand: dict, index: dict, ctx: Optional[dict]) -> List[Finding]:
    """R6-C-ISSUE-001: revision issue identity / transition."""
    out: List[Finding] = []
    issue = cand.get("revision_issue") or {}
    known = _issue_ids(cand)
    issue_id = issue.get("issue_id")
    if issue_id is not None and issue_id not in known:
        out.append(finding_for("REPORT_REVISION_ISSUE_ID_DRIFT", index))
    diff_state = issue.get("diff_state")
    # resolved without justifying transition_refs → unjustified
    if diff_state == "resolved" and not (issue.get("transition_refs") or []):
        out.append(finding_for("REPORT_REVISION_STATUS_UNJUSTIFIED", index))
    # Coverage incompleteness is mapped to COV-002; revision_issue_diff rows only
    # dispatch SRC/ISSUE, so surface it here.
    if issue.get("coverage_closed") is False:
        out.append(finding_for("REPORT_REVISION_COVERAGE_INCOMPLETE", index))
    return out


def _v_cov_001(cand: dict, index: dict, ctx: Optional[dict]) -> List[Finding]:
    """R6-C-COV-001: expected-set / reverse-omission coverage."""
    out: List[Finding] = []
    coverage_units = cand.get("coverage_units") or {}
    for unit_kind, entries in coverage_units.items():
        if isinstance(entries, list) and len(entries) == 0:
            out.append(finding_for("REPORT_COVERAGE_UNIT_MISSING", index))

    matrix = cand.get("report_review_matrix") or {}
    expected = matrix.get("expected_review_surface") or []
    links = matrix.get("reverse_coverage_links") or []
    if len(expected) != len(links):
        out.append(finding_for("REPORT_REVERSE_OMISSION_UNCOVERED", index))
    for link in links:
        if not isinstance(link, dict):
            out.append(finding_for("REPORT_REVERSE_OMISSION_UNCOVERED", index))
            continue
        claims = link.get("claim_ids") or []
        issues = link.get("issue_ids") or []
        exception = link.get("not_evaluable_exception")
        if not claims and not issues and not exception:
            out.append(finding_for("REPORT_REVERSE_OMISSION_UNCOVERED", index))
    return _dedupe(out)


def _v_cov_002(cand: dict, index: dict, ctx: Optional[dict]) -> List[Finding]:
    """R6-C-COV-002: coverage status / anchors / partial-truncated."""
    out: List[Finding] = []
    locs = _locators(cand)
    amb = _ambiguous(cand)
    stale = _stale(cand)

    # no_claim on units that still carry substantive claim content
    for path_keys, has_substance in (
        (("table", "row"), True),  # table row always has claim payload in fixture
        (("figure",), True),
        (("footnote",), True),
    ):
        node = _get(cand, *path_keys) or {}
        if node.get("coverage_status") == "no_claim" and has_substance:
            # publication.coverage_status=no_claim is the legitimate positive case
            out.append(finding_for("REPORT_NO_CLAIM_INVALID", index))

    # Cross-page / annotation / html anchors
    cross = cand.get("cross_page") or {}
    anchor_state = cross.get("anchor_state")
    if anchor_state == "ambiguous":
        out.append(finding_for("REPORT_ANCHOR_AMBIGUOUS", index))
    anchor_ref = cross.get("anchor_ref")
    if anchor_ref is not None and anchor_ref not in locs:
        out.append(finding_for("REPORT_ANCHOR_NOT_IN_SOURCE", index))
    if cross.get("continuation_ref") is None and anchor_state in ("unique", "linked", "unlinked", "ambiguous"):
        # incomplete continuation when the cross_page object is active
        if "continuation_ref" in cross and cross.get("continuation_ref") is None:
            out.append(finding_for("REPORT_CROSS_PAGE_ANCHOR_INCOMPLETE", index))

    annotation = cand.get("annotation") or {}
    if annotation.get("anchor_validation") == "stale":
        out.append(finding_for("REPORT_ANNOTATION_ANCHOR_STALE", index))
    ann_loc = annotation.get("locator_ref")
    if ann_loc is not None and ann_loc not in locs and ann_loc not in amb:
        out.append(finding_for("REPORT_ANCHOR_NOT_IN_SOURCE", index))

    html = cand.get("html") or {}
    dom = html.get("dom_anchor")
    if dom is not None and dom not in locs:
        if dom in stale or dom not in locs:
            out.append(finding_for("REPORT_ANCHOR_NOT_IN_SOURCE", index))
    if html.get("anchor_fallback_policy") not in (None, "none"):
        out.append(finding_for("REPORT_NEAREST_ANCHOR_FALLBACK_FORBIDDEN", index))

    legend_loc = _get(cand, "figure", "legend", "locator_ref")
    if legend_loc in amb:
        out.append(finding_for("REPORT_ANCHOR_AMBIGUOUS", index))

    # Revision coverage
    if _get(cand, "revision_issue", "coverage_closed") is False:
        out.append(finding_for("REPORT_REVISION_COVERAGE_INCOMPLETE", index))

    publication = cand.get("publication") or {}
    if publication.get("coverage_closed") is False:
        out.append(finding_for("REPORT_COVERAGE_INCOMPLETE", index))

    # Analysis completion cannot hide residual partial coverage. The canonical
    # fixture stays ``running`` until a challenge explicitly completes it, so
    # this rule is independent of challenge category.
    if (
        publication.get("analysis_state") == "complete"
        and publication.get("coverage_status") == "partial"
        and publication.get("evidence_state") == "complete"
    ):
        out.append(finding_for("REPORT_PARTIAL_OUTPUT", index))

    return _dedupe(out)


def _v_bundle_001(cand: dict, index: dict, ctx: Optional[dict]) -> List[Finding]:
    """R6-C-BUNDLE-001: three-piece / format identity / annotation anchors."""
    out: List[Finding] = []
    derivative = cand.get("derivative") or {}
    annotation_copy = cand.get("annotation_copy") or {}
    source_refs = cand.get("source_ref_registry") or {}
    lineage_registry = cand.get("lineage_registry") or {}
    original = cand.get("original_report") or {}
    annotation = cand.get("annotation") or {}

    parent = derivative.get("parent_source_ref")
    lineage_ref = derivative.get("lineage_ref")
    out_hash = derivative.get("output_hash")
    deriv_hash = derivative.get("derivative_content_hash")

    if lineage_ref is None and "lineage_ref" in derivative:
        out.append(finding_for("FORMAT_OUTPUT_IDENTITY_MISSING", index))
    if out_hash is None and "output_hash" in derivative:
        out.append(finding_for("FORMAT_HASH_MISSING", index))
    if deriv_hash is not None and parent is not None:
        src = source_refs.get(parent) or {}
        # Preserved content must not silently diverge from a declared preserved hash.
        if deriv_hash not in (
            None,
            "sha256-content-preserved",
            src.get("content_hash"),
            original.get("content_hash"),
        ):
            # Undeclared content change
            if "undeclared" in str(deriv_hash) or deriv_hash != "sha256-content-preserved":
                if deriv_hash != original.get("content_hash"):
                    out.append(finding_for("FORMAT_CONTENT_HASH_MISMATCH", index))
    elif deriv_hash is not None and "undeclared" in str(deriv_hash):
        out.append(finding_for("FORMAT_CONTENT_HASH_MISMATCH", index))

    # annotation_copy must bind to original report content hash
    ac_hash = annotation_copy.get("source_content_hash")
    if ac_hash is not None and ac_hash not in (
        "sha256-original-report",
        original.get("content_hash"),
    ):
        out.append(finding_for("FORMAT_IDENTITY_MISMATCH", index))

    if annotation_copy.get("annotation_mode_declared") is False:
        out.append(finding_for("FORMAT_ANNOTATION_FIDELITY_FAILED", index))

    if annotation.get("anchor_validation") == "stale":
        out.append(finding_for("REPORT_ANNOTATION_ANCHOR_STALE", index))

    html = cand.get("html") or {}
    if html.get("anchor_fallback_policy") not in (None, "none"):
        out.append(finding_for("REPORT_NEAREST_ANCHOR_FALLBACK_FORBIDDEN", index))

    # lineage registry consistency when lineage_ref present
    if lineage_ref is not None and lineage_ref not in lineage_registry:
        out.append(finding_for("FORMAT_OUTPUT_IDENTITY_MISSING", index))
    return _dedupe(out)


def _v_draft_001(cand: dict, index: dict, ctx: Optional[dict]) -> List[Finding]:
    """R6-C-DRAFT-001: clean draft identity."""
    out: List[Finding] = []
    draft = cand.get("clean_draft") or {}
    if "draft_marker" in draft and draft.get("draft_marker") is None:
        out.append(finding_for("DRAFT_IDENTITY_MISSING", index))
    elif draft.get("draft_marker") not in (None, "DRAFT"):
        out.append(finding_for("DRAFT_IDENTITY_MISSING", index))
    return out


def _v_mode_001(cand: dict, index: dict, ctx: Optional[dict]) -> List[Finding]:
    """R6-C-MODE-001: mode entry / carry-forward / cutoff / revision."""
    out: List[Finding] = []
    run = cand.get("run") or {}
    daily = cand.get("daily") or {}
    pre_lock = cand.get("pre_lock") or {}
    post_lock = cand.get("post_lock") or {}

    if run.get("mode_transition") == "silent_in_place":
        out.append(finding_for("MODE_SILENT_TRANSITION_FORBIDDEN", index))

    if post_lock.get("output_cutoff_ref") not in (None, _POST_LOCK_CUTOFF):
        if post_lock.get("output_cutoff_ref") != _POST_LOCK_CUTOFF:
            out.append(finding_for("MODE_CUTOFF_MISMATCH", index))

    if "carry_forward_source_run" in run and run.get("carry_forward_source_run") is None:
        out.append(finding_for("MODE_CARRY_FORWARD_UNDECLARED", index))
    if run.get("carry_forward_compatibility") == "incompatible":
        out.append(finding_for("MODE_CARRY_FORWARD_INCOMPATIBLE", index))

    if post_lock.get("output_revision_ref") not in (None, _POST_LOCK_REVISION):
        if post_lock.get("output_revision_ref") != _POST_LOCK_REVISION:
            out.append(finding_for("MODE_REVISION_MISMATCH", index))

    if pre_lock.get("execution_basis") not in (None, "full"):
        out.append(finding_for("MODE_ANALYSIS_BASIS_MISMATCH", index))
    if "prior_baseline_ref" in daily and daily.get("prior_baseline_ref") is None:
        out.append(finding_for("MODE_ANALYSIS_BASIS_MISMATCH", index))

    scope = daily.get("output_scope")
    if scope is not None and scope not in _DAILY_ALLOWED_SCOPES:
        out.append(finding_for("MODE_OUTPUT_SCOPE_MISMATCH", index))
    return _dedupe(out)


def _v_out_001(cand: dict, index: dict, ctx: Optional[dict]) -> List[Finding]:
    """R6-C-OUT-001: output eligibility / authority / numeric / risk."""
    out: List[Finding] = []
    publication = cand.get("publication") or {}
    draft = cand.get("clean_draft") or {}
    run = cand.get("run") or {}
    risk = cand.get("risk") or {}
    body_claim = _get(cand, "body", "paragraph", "claim") or {}
    figure = cand.get("figure") or {}
    baseline = None if ctx is None else ctx.get("baseline_value")

    # Evidence conflict on claim or publication
    if body_claim.get("evidence_state") == "conflicted":
        out.append(finding_for("REPORT_EVIDENCE_CONFLICT", index))
    if publication.get("evidence_state") == "conflicted":
        out.append(finding_for("REPORT_EVIDENCE_CONFLICT", index))

    if publication.get("analysis_state") == "failed":
        out.append(finding_for("REPORT_FAILED", index))

    if run.get("revision_transition") == "undeclared":
        out.append(finding_for("REPORT_OUTPUT_NOT_ELIGIBLE", index))

    # Claiming full-report eligibility while gates fail
    if publication.get("full_report_reviewed_eligible") is True:
        if (
            publication.get("coverage_status") in ("partial", "truncated")
            or publication.get("coverage_closed") is False
            or publication.get("evidence_state") in ("conflicted", "truncated")
            or publication.get("analysis_state") in ("failed", "running")
        ):
            out.append(finding_for("REPORT_OUTPUT_NOT_ELIGIBLE", index))

    if draft.get("publish_state") == "blocked_conflict":
        out.append(finding_for("REPORT_OUTPUT_NOT_ELIGIBLE", index))

    # Mode output scope also surfaces here for mode_isolation category overlap
    daily = cand.get("daily") or {}
    scope = daily.get("output_scope")
    if scope is not None and scope not in _DAILY_ALLOWED_SCOPES:
        out.append(finding_for("MODE_OUTPUT_SCOPE_MISMATCH", index))

    # Status / evidence (065) — OUT owns STATUS_EVIDENCE; CLAIM owns CUTOFF for 066
    claim_status = _get(cand, "output", "claim_status")
    if claim_status == "supported" and baseline == "unsupported":
        out.append(finding_for("REPORT_STATUS_EVIDENCE_MISMATCH", index))

    # Risk / run identity (mapped to ID-001; numeric category dispatches OUT).
    identity = cand.get("identity") or {}
    if risk.get("authority_run_ref") not in (None, identity.get("run_id"), run.get("run_id")):
        out.append(finding_for("REPORT_SOURCE_IDENTITY_MISMATCH", index))

    # Risk set / numeric reconciliation
    member_ids = risk.get("member_ids") or []
    if isinstance(risk.get("project_member_count"), int):
        if risk["project_member_count"] != len(member_ids):
            out.append(finding_for("REPORT_RISK_SET_MISMATCH", index))
    site_totals = risk.get("site_totals") or []
    if isinstance(risk.get("project_total"), (int, float)) and site_totals:
        if risk["project_total"] != sum(site_totals):
            out.append(finding_for("REPORT_NUMERIC_RECONCILIATION_FAILED", index))

    # Figure raw_rate must stay at the frozen synthetic authority value 0.3333
    raw_rate = figure.get("raw_rate")
    if isinstance(raw_rate, (int, float)) and abs(raw_rate - 0.3333) > 1e-12:
        out.append(finding_for("REPORT_NUMERIC_RECONCILIATION_FAILED", index))

    # Denominator / rate authority mismatches also owned by OUT via authority_mismatch
    denom_value = _get(cand, "denominator", "value")
    num_value = _get(cand, "numerator", "value")
    num_unit = _get(cand, "numerator", "unit")
    denom_unit = _get(cand, "denominator", "unit")
    if (
        isinstance(num_value, (int, float))
        and isinstance(denom_value, (int, float))
        and denom_value > 0
        and num_value > denom_value
        and num_unit == denom_unit
    ):
        out.append(finding_for("REPORT_NUMERATOR_DENOMINATOR_MISMATCH", index))

    rate = cand.get("rate") or {}
    if (
        isinstance(rate.get("numerator"), (int, float))
        and isinstance(denom_value, (int, float))
        and denom_value > 0
        and isinstance(rate.get("reported_value"), (int, float))
    ):
        raw = rate["numerator"] / denom_value
        precision = rate.get("display_precision")
        reported = rate["reported_value"]
        if isinstance(precision, int) and precision >= 0:
            display = round(raw, precision)
            if reported != display and abs(reported - raw) > 1e-12:
                out.append(finding_for("REPORT_RATE_RECOMPUTE_MISMATCH", index))
        elif abs(reported - raw) > 1e-12:
            out.append(finding_for("REPORT_RATE_RECOMPUTE_MISMATCH", index))

    count_unit = _get(cand, "count", "unit")
    if count_unit is not None and denom_unit is not None and count_unit != denom_unit:
        out.append(finding_for("REPORT_COUNT_SEMANTICS_MISMATCH", index))

    return _dedupe(out)


def _v_boundary_001(cand: dict, index: dict, ctx: Optional[dict]) -> List[Finding]:
    """R6-C-BOUNDARY-001: governed workflow scope (not in content categories)."""
    # Synthetic slice never writes outside create-only paths; this validator is
    # a no-op acceptor for content challenges. Audit-execution supplies the
    # non-LLM boundary acceptor separately.
    return []


VALIDATORS: dict = {
    "R6-C-ID-001": _v_id_001,
    "R6-C-SRC-001": _v_src_001,
    "R6-C-CLAIM-001": _v_claim_001,
    "R6-C-ISSUE-001": _v_issue_001,
    "R6-C-COV-001": _v_cov_001,
    "R6-C-COV-002": _v_cov_002,
    "R6-C-BUNDLE-001": _v_bundle_001,
    "R6-C-DRAFT-001": _v_draft_001,
    "R6-C-MODE-001": _v_mode_001,
    "R6-C-OUT-001": _v_out_001,
    "R6-C-BOUNDARY-001": _v_boundary_001,
}

VALIDATOR_ORDER: Tuple[str, ...] = (
    "R6-C-ID-001",
    "R6-C-SRC-001",
    "R6-C-CLAIM-001",
    "R6-C-ISSUE-001",
    "R6-C-COV-001",
    "R6-C-COV-002",
    "R6-C-BUNDLE-001",
    "R6-C-DRAFT-001",
    "R6-C-MODE-001",
    "R6-C-OUT-001",
    "R6-C-BOUNDARY-001",
)


def _dedupe(findings: Iterable[Finding]) -> List[Finding]:
    seen = set()
    out: List[Finding] = []
    for f in findings:
        key = (f.validator_id, f.failure_code, f.diagnostic_code)
        if key in seen:
            continue
        seen.add(key)
        out.append(f)
    return out


# ---------------------------------------------------------------------------
# dispatcher
# ---------------------------------------------------------------------------

def validators_for_category(contract: dict, category: str) -> List[str]:
    """Return all content validators after confirming the category is declared.

    The frozen category map is descriptive metadata only. Treating it as a
    filter would let a candidate hide findings merely by changing category.
    """
    binding = contract.get("challenge_matrix_binding") or {}
    mapping = binding.get("category_validator_map") or {}
    if category not in mapping:
        raise ValidatorError(f"unknown challenge category: {category!r}")
    if binding.get("category_validator_map_normative") is not False:
        raise ValidatorError("category validator map must remain non-normative")
    return [vid for vid in VALIDATOR_ORDER if vid != "R6-C-BOUNDARY-001"]


def dispatch_validators(
    doc: dict,
    category: str,
    contract: dict,
    matrix: dict,
    mutation_ctx: Optional[dict] = None,
) -> List[Finding]:
    """Run every content validator; preserve all blocking findings."""
    index = build_diagnostic_index(matrix)
    cand = _cand(doc)
    findings: List[Finding] = []
    for vid in validators_for_category(contract, category):
        fn = VALIDATORS.get(vid)
        if fn is None:
            raise ValidatorError(f"validator not implemented: {vid}")
        findings.extend(fn(cand, index, mutation_ctx))
    return _dedupe(findings)


# ---------------------------------------------------------------------------
# non-blocking record / accept classifiers (when no blocking findings)
# ---------------------------------------------------------------------------

def _classify_record(cand: dict, category: str) -> Optional[str]:
    """Return a record:<token> without error, or None."""
    publication = cand.get("publication") or {}
    if publication.get("evidence_state") == "truncated":
        return "truncated_output"

    # extractability → not_evaluable
    for keys in (("figure",), ("footnote",), ("source_page",)):
        node = _get(cand, *keys) or {}
        if node.get("extractability") == "unextractable":
            return "not_evaluable"

    # reverse-coverage explicit exception
    links = _get(cand, "report_review_matrix", "reverse_coverage_links") or []
    for link in links:
        if isinstance(link, dict) and link.get("not_evaluable_exception"):
            # Only record when the exception actually accounts for an empty claim/issue set
            claims = link.get("claim_ids") or []
            issues = link.get("issue_ids") or []
            if not claims:
                return "not_evaluable"

    # revision issue diff / new
    issue = cand.get("revision_issue") or {}
    if issue.get("transition_refs"):
        return "issue_diff"
    if issue.get("diff_state") == "new":
        return "issue_new"

    # format lineage
    derivative = cand.get("derivative") or {}
    if derivative.get("parent_source_ref"):
        # record format_lineage only in format category when parent was previously missing
        if category == "format_identity_provenance":
            return "format_lineage"

    return None


def _classify_accept(cand: dict, category: str) -> str:
    if category == "cutoff_revision":
        return "cutoff_bound"
    if category == "cross_page_anchor_extraction":
        if _get(cand, "cross_page", "anchor_state") == "linked":
            return "cross_page_anchor_linked"
        return "claim_recorded"
    if category == "mode_isolation_carry_forward":
        return "mode_output_eligible"
    if category in ("denominator", "numeric_risk_consistency"):
        if _get(cand, "numeric", "reconciliation_state") == "matched" or category == "denominator":
            if category == "denominator" or _get(cand, "numeric", "reconciliation_state") == "matched":
                return "numeric_reconciled"
    if category == "error_semantics_publication_gate":
        if _get(cand, "publication", "coverage_status") == "no_claim":
            return "no_claim_unit"
    return "claim_recorded"


# ---------------------------------------------------------------------------
# projection
# ---------------------------------------------------------------------------

def project_result(
    findings: Sequence[Finding],
    category: str,
    cand: dict,
    record_token: Optional[str],
    accept_token: Optional[str],
) -> Tuple[str, Optional[str], str, bool]:
    """Return (outcome, error, projection, blocking)."""
    blocking_findings = [f for f in findings if f.blocking]
    if blocking_findings:
        primary = _select_primary(blocking_findings, category, cand)
        code = primary.diagnostic_code
        if code in _BLOCK_DIAGNOSTICS:
            outcome = f"block:{code}"
        else:
            outcome = f"reject:{code}"
        return outcome, code, _projection_for(code, category, cand), True

    if record_token:
        return f"record:{record_token}", None, _record_projection(record_token, category), False

    token = accept_token or "claim_recorded"
    return f"accept:{token}", None, _accept_projection(token, category), False


def _select_primary(findings: Sequence[Finding], category: str, cand: dict) -> Finding:
    """Pick the primary finding when multiple blocking findings exist.

    Preference follows the challenge category's dominant oracle, then a stable
    diagnostic priority list so results stay deterministic.
    """
    preferred_by_category = {
        "body": (
            "REPORT_CLAIM_LOCATOR_INVALID",
            "REPORT_CLAIM_IDENTITY_COLLISION",
            "REPORT_CLAIM_EVIDENCE_MISSING",
            "REPORT_EVIDENCE_CONFLICT",
            "REPORT_REVERSE_OMISSION_UNCOVERED",
        ),
        "table": (
            "REPORT_CLAIM_LOCATOR_INVALID",
            "REPORT_DENOMINATOR_MISSING",
            "REPORT_NO_CLAIM_INVALID",
            "REPORT_POPULATION_MISMATCH",
            "REPORT_REVERSE_OMISSION_UNCOVERED",
        ),
        "figure": (
            "REPORT_CLAIM_LOCATOR_INVALID",
            "REPORT_NO_CLAIM_INVALID",
            "REPORT_UNIT_MISMATCH",
            "REPORT_ANCHOR_AMBIGUOUS",
            "REPORT_NUMERIC_RECONCILIATION_FAILED",
        ),
        "footnote": (
            "REPORT_COVERAGE_UNIT_MISSING",
            "REPORT_NO_CLAIM_INVALID",
            "REPORT_ANCHOR_NOT_IN_SOURCE",
        ),
        "denominator": (
            "REPORT_DENOMINATOR_MISSING",
            "REPORT_DENOMINATOR_ZERO",
            "REPORT_NUMERATOR_DENOMINATOR_MISMATCH",
            "REPORT_RATE_RECOMPUTE_MISMATCH",
            "REPORT_COUNT_SEMANTICS_MISMATCH",
            "REPORT_POPULATION_MISMATCH",
        ),
        "cutoff_revision": (
            "REPORT_CUTOFF_MISSING",
            "REPORT_CUTOFF_MISMATCH",
            "REPORT_SOURCE_REVISION_MISMATCH",
            "REPORT_REVISION_PARENT_MISMATCH",
            "REPORT_SOURCE_IDENTITY_MISMATCH",
            "REPORT_OUTPUT_NOT_ELIGIBLE",
        ),
        "cross_page_anchor_extraction": (
            "REPORT_ANCHOR_NOT_IN_SOURCE",
            "REPORT_ANCHOR_AMBIGUOUS",
            "REPORT_CROSS_PAGE_ANCHOR_INCOMPLETE",
            "REPORT_ANNOTATION_ANCHOR_STALE",
        ),
        "revision_issue_diff": (
            "REPORT_REVISION_ISSUE_ID_DRIFT",
            "REPORT_REVISION_STATUS_UNJUSTIFIED",
            "REPORT_REVISION_COVERAGE_INCOMPLETE",
            "REPORT_REVISION_PARENT_MISMATCH",
            "ORIGINAL_OVERWRITE_FORBIDDEN",
        ),
        "mode_isolation_carry_forward": (
            "MODE_SILENT_TRANSITION_FORBIDDEN",
            "MODE_CUTOFF_MISMATCH",
            "MODE_CARRY_FORWARD_UNDECLARED",
            "MODE_CARRY_FORWARD_INCOMPATIBLE",
            "MODE_OUTPUT_SCOPE_MISMATCH",
            "MODE_REVISION_MISMATCH",
            "MODE_ANALYSIS_BASIS_MISMATCH",
        ),
        "numeric_risk_consistency": (
            "REPORT_RISK_SET_MISMATCH",
            "REPORT_NUMERIC_RECONCILIATION_FAILED",
            "REPORT_STATUS_EVIDENCE_MISMATCH",
            "REPORT_CUTOFF_MISMATCH",
            "REPORT_SOURCE_IDENTITY_MISMATCH",
            "REPORT_NOT_EVALUABLE_AS_ZERO",
        ),
        "format_identity_provenance": (
            "FORMAT_CONTENT_HASH_MISMATCH",
            "FORMAT_OUTPUT_IDENTITY_MISSING",
            "FORMAT_IDENTITY_MISMATCH",
            "DRAFT_IDENTITY_MISSING",
            "ORIGINAL_OVERWRITE_FORBIDDEN",
            "FORMAT_ANNOTATION_FIDELITY_FAILED",
            "REPORT_NEAREST_ANCHOR_FALLBACK_FORBIDDEN",
            "FORMAT_HASH_MISSING",
        ),
        "error_semantics_publication_gate": (
            "REPORT_COVERAGE_INCOMPLETE",
            "REPORT_OUTPUT_NOT_ELIGIBLE",
            "REPORT_EVIDENCE_CONFLICT",
            "REPORT_FAILED",
            "REPORT_PARTIAL_OUTPUT",
        ),
    }
    preferred = preferred_by_category.get(category, ())
    by_code = {f.diagnostic_code: f for f in findings}
    for code in preferred:
        if code in by_code:
            return by_code[code]
    # Stable fallback: sort by (validator order, diagnostic_code)
    order = {vid: i for i, vid in enumerate(VALIDATOR_ORDER)}
    return sorted(
        findings,
        key=lambda f: (order.get(f.validator_id, 99), f.diagnostic_code),
    )[0]


def _projection_for(code: str, category: str, cand: dict) -> str:
    if code in (
        "REPORT_CLAIM_LOCATOR_INVALID",
        "REPORT_CLAIM_IDENTITY_COLLISION",
        "REPORT_CLAIM_EVIDENCE_MISSING",
        "REPORT_NO_CLAIM_INVALID",
        "REPORT_ANCHOR_AMBIGUOUS",
        "REPORT_ANCHOR_NOT_IN_SOURCE",
        "REPORT_CUTOFF_MISSING",
        "FORMAT_CONTENT_HASH_MISMATCH",
        "FORMAT_OUTPUT_IDENTITY_MISSING",
        "FORMAT_IDENTITY_MISMATCH",
        "FORMAT_ANNOTATION_FIDELITY_FAILED",
        "FORMAT_HASH_MISSING",
        "REPORT_NEAREST_ANCHOR_FALLBACK_FORBIDDEN",
        "REPORT_ANNOTATION_ANCHOR_STALE",
        "REPORT_REVISION_PARENT_MISMATCH",
        "REPORT_SOURCE_REVISION_MISMATCH",
    ):
        if code == "REPORT_CUTOFF_MISMATCH" and category == "numeric_risk_consistency":
            return "publication_blocked"
        if code == "REPORT_SOURCE_IDENTITY_MISMATCH" and category == "cutoff_revision":
            return "not_emitted"
        if code in (
            "REPORT_CLAIM_LOCATOR_INVALID",
            "REPORT_CLAIM_IDENTITY_COLLISION",
            "REPORT_CLAIM_EVIDENCE_MISSING",
            "REPORT_NO_CLAIM_INVALID",
            "REPORT_ANCHOR_AMBIGUOUS",
            "REPORT_ANCHOR_NOT_IN_SOURCE",
            "REPORT_CUTOFF_MISSING",
            "REPORT_SOURCE_REVISION_MISMATCH",
            "REPORT_REVISION_PARENT_MISMATCH",
            "REPORT_ANNOTATION_ANCHOR_STALE",
            "FORMAT_CONTENT_HASH_MISMATCH",
            "FORMAT_OUTPUT_IDENTITY_MISSING",
            "FORMAT_IDENTITY_MISMATCH",
            "FORMAT_ANNOTATION_FIDELITY_FAILED",
            "FORMAT_HASH_MISSING",
            "REPORT_NEAREST_ANCHOR_FALLBACK_FORBIDDEN",
        ):
            return "not_emitted"

    if code == "REPORT_CUTOFF_MISMATCH":
        return "publication_blocked" if category == "numeric_risk_consistency" else "not_emitted"
    if code == "REPORT_SOURCE_IDENTITY_MISMATCH":
        return (
            "numeric_reconciliation_blocked"
            if category == "numeric_risk_consistency"
            else "not_emitted"
        )
    if code == "REPORT_OUTPUT_NOT_ELIGIBLE":
        if _get(cand, "clean_draft", "publish_state") == "blocked_conflict":
            return "draft_only"
        return "publication_blocked"
    if code == "DRAFT_IDENTITY_MISSING":
        return "draft_only"
    if code == "ORIGINAL_OVERWRITE_FORBIDDEN":
        return "original_unchanged"
    if code == "REPORT_FAILED":
        return "failed"
    if code in (
        "REPORT_DENOMINATOR_MISSING",
        "REPORT_NUMERATOR_DENOMINATOR_MISMATCH",
        "REPORT_RATE_RECOMPUTE_MISMATCH",
        "REPORT_COUNT_SEMANTICS_MISMATCH",
        "REPORT_POPULATION_MISMATCH",
        "REPORT_UNIT_MISMATCH",
        "REPORT_RISK_SET_MISMATCH",
        "REPORT_NUMERIC_RECONCILIATION_FAILED",
        "REPORT_NOT_EVALUABLE_AS_ZERO",
    ):
        return "numeric_reconciliation_blocked"
    if code == "REPORT_DENOMINATOR_ZERO":
        return "not_evaluable"
    if code in (
        "REPORT_COVERAGE_UNIT_MISSING",
        "REPORT_CROSS_PAGE_ANCHOR_INCOMPLETE",
        "REPORT_REVISION_COVERAGE_INCOMPLETE",
    ):
        return "coverage_incomplete"
    if code in (
        "REPORT_REVISION_ISSUE_ID_DRIFT",
        "REPORT_REVISION_STATUS_UNJUSTIFIED",
    ):
        return "issue_diff"
    if code.startswith("MODE_"):
        return "mode_output_blocked"
    if code in (
        "REPORT_EVIDENCE_CONFLICT",
        "REPORT_REVERSE_OMISSION_UNCOVERED",
        "REPORT_COVERAGE_INCOMPLETE",
        "REPORT_STATUS_EVIDENCE_MISMATCH",
        "REPORT_PARTIAL_OUTPUT",
    ):
        return "publication_blocked"
    return "not_emitted"


def _record_projection(token: str, category: str) -> str:
    if token == "truncated_output":
        return "publication_blocked"
    if token == "not_evaluable":
        return "not_evaluable"
    if token in ("issue_diff", "issue_new"):
        return "issue_diff"
    if token == "format_lineage":
        return "annotation_copy"
    return "not_emitted"


def _accept_projection(token: str, category: str) -> str:
    if token == "mode_output_eligible":
        return "mode_output_eligible"
    if token == "cross_page_anchor_linked":
        return "annotation_copy"
    return "review_artifact"


# ---------------------------------------------------------------------------
# challenge executor
# ---------------------------------------------------------------------------

def execute_challenge(
    row: dict,
    contract: Optional[dict] = None,
    matrix: Optional[dict] = None,
    fixture_doc: Optional[dict] = None,
) -> ChallengeResult:
    """Build fixture → one replace → category validators → canonical result."""
    if contract is None:
        contract = contracts.contract_obj()
    if matrix is None:
        matrix = contracts.matrix_obj()

    challenge_id = row["challenge_id"]
    category = row["category"]
    mutation = row["single_mutation"]

    if fixture_doc is None:
        baseline_doc = fixtures.build_fixture(challenge_id, row)
    else:
        baseline_doc = fixture_doc

    mutated = apply_one_replace(baseline_doc, mutation)
    mutations_applied = 1

    mutation_ctx = {
        "path": mutation["path"],
        "baseline_value": row.get("baseline_value"),
        "value": mutation.get("value"),
        "challenge_id": challenge_id,
        "category": category,
    }
    findings = dispatch_validators(mutated, category, contract, matrix, mutation_ctx)
    cand = _cand(mutated)

    record_token = None
    accept_token = None
    if not any(f.blocking for f in findings):
        record_token = _classify_record(cand, category)
        if record_token is None:
            accept_token = _classify_accept(cand, category)

    outcome, error, projection, blocking = project_result(
        findings, category, cand, record_token, accept_token
    )
    return ChallengeResult(
        challenge_id=challenge_id,
        category=category,
        mutations_applied=mutations_applied,
        findings=findings,
        outcome=outcome,
        error=error,
        projection=projection,
        blocking=blocking,
        record_token=record_token,
        accept_token=accept_token,
    )


def execute_all(
    rows: Optional[Sequence[dict]] = None,
    contract: Optional[dict] = None,
    matrix: Optional[dict] = None,
) -> List[ChallengeResult]:
    """Execute every matrix row exactly once (deterministic id order)."""
    if contract is None:
        contract = contracts.contract_obj()
    if matrix is None:
        matrix = contracts.matrix_obj()
    if rows is None:
        rows = matrix["rows"]
    ordered = sorted(rows, key=lambda r: r["challenge_id"])
    return [execute_challenge(row, contract, matrix) for row in ordered]


def oracle_parity_report(
    rows: Optional[Sequence[dict]] = None,
    contract: Optional[dict] = None,
    matrix: Optional[dict] = None,
) -> dict:
    """Compare executor outputs to matrix metadata-oracle expectations."""
    if contract is None:
        contract = contracts.contract_obj()
    if matrix is None:
        matrix = contracts.matrix_obj()
    if rows is None:
        rows = matrix["rows"]
    mismatches = []
    results = []
    for row in sorted(rows, key=lambda r: r["challenge_id"]):
        result = execute_challenge(row, contract, matrix)
        results.append(result.as_dict())
        if (
            result.outcome != row["expected_outcome"]
            or result.error != row["expected_error"]
            or result.projection != row["expected_projection"]
            or result.mutations_applied != 1
        ):
            mismatches.append(
                {
                    "challenge_id": row["challenge_id"],
                    "expected": {
                        "outcome": row["expected_outcome"],
                        "error": row["expected_error"],
                        "projection": row["expected_projection"],
                    },
                    "actual": {
                        "outcome": result.outcome,
                        "error": result.error,
                        "projection": result.projection,
                        "mutations_applied": result.mutations_applied,
                        "findings": [f.as_dict() for f in result.findings],
                    },
                }
            )
    return {
        "row_count": len(rows),
        "mismatch_count": len(mismatches),
        "mismatches": mismatches,
        "results": results,
    }
