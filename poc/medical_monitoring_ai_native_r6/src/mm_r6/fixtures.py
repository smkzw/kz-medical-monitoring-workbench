"""Deterministic baseline fixture catalog for the R6 v0.1 challenge matrix.

Per the frozen ``fixture_binding`` of ``challenge_matrix.json``:

* ``fixture_id`` equals ``challenge_id``;
* before mutation, the JSON Pointer in ``single_mutation.path`` exists in the
  fixture and equals ``baseline_value``;
* every non-mutated field is frozen by the synthetic fixture.

Because nine pointers carry different ``baseline_value``s across different
rows (see :func:`mm_r6.contracts.contested_paths`), each of the 86 challenges
freezes its own complete candidate document rooted at the top-level key
``candidate``. A single canonical template supplies every frozen field; each
challenge fixture is the template with its row pointer set to the row
``baseline_value`` (a no-op where the template default already equals it).

Guarantees, verified by construction and re-checkable at runtime:

1. :func:`verify_pointer_preconditions` returns no violation for every row:
   the pointer exists and its value is exactly (type-aware) equal to
   ``baseline_value``;
2. freeze: the fixture with the row pointer stripped is deep-equal to the
   template with the same pointer stripped;
3. canonical bytes: :func:`canonical_bytes` is deterministic under any
   ``PYTHONHASHSEED`` and optimizer level (``-O``/``-OO``), so a two-pass
   catalog build produces identical bytes.

Synthetic data only. No real project, real report, OCR, model, or medical
conclusion is involved; every matrix row is ``test_metadata_only``.
"""

from __future__ import annotations

import copy
import json

from .contracts import sha256_hex

#: Synthetic project/run identity used across all frozen fixtures.
CONTRACT_ID = "medical_monitoring_r6_external_report_mode_output_contract"
CONTRACT_VERSION = "0.1"
CANDIDATE_ROOT = "candidate"

#: Canonical JSON serialization options: key-sorted, compact, non-ASCII kept
#: verbatim, UTF-8 encoded. Independent of dict hash order, hence independent
#: of ``PYTHONHASHSEED``.
_CANONICAL_JSON_OPTS = {"ensure_ascii": False, "sort_keys": True, "separators": (",", ":")}


class FixtureError(RuntimeError):
    """Raised when a fixture violates pointer preconditions or freeze rules."""


def canonical_bytes(obj) -> bytes:
    return json.dumps(obj, **_CANONICAL_JSON_OPTS).encode("utf-8")


# ---------------------------------------------------------------------------
# strict (type-aware) equality: distinguishes True/1 and False/0
# ---------------------------------------------------------------------------

def strict_eq(a, b) -> bool:
    if isinstance(a, bool) or isinstance(b, bool):
        return isinstance(a, bool) and isinstance(b, bool) and a is b
    if isinstance(a, (int, float)) and isinstance(b, (int, float)):
        return a == b
    if isinstance(a, list) and isinstance(b, list):
        return len(a) == len(b) and all(strict_eq(x, y) for x, y in zip(a, b))
    if isinstance(a, dict) and isinstance(b, dict):
        return a.keys() == b.keys() and all(strict_eq(a[k], b[k]) for k in a)
    return type(a) is type(b) and a == b


# ---------------------------------------------------------------------------
# RFC 6901 pointer operations (fail-closed)
# ---------------------------------------------------------------------------

def _pointer_tokens(pointer: str) -> list:
    if not pointer.startswith("/") or (len(pointer) > 1 and pointer.endswith("/")):
        raise FixtureError(f"invalid json pointer {pointer!r}")
    tokens = []
    for raw in pointer.split("/")[1:]:
        tokens.append(raw.replace("~1", "/").replace("~0", "~"))
    return tokens


def get_pointer(doc, pointer: str, default=None):
    """Return the value at ``pointer`` or ``default`` when absent."""
    node = doc
    for token in _pointer_tokens(pointer):
        if isinstance(node, list):
            try:
                idx = int(token)
            except ValueError:
                return default
            if not 0 <= idx < len(node):
                return default
            node = node[idx]
        elif isinstance(node, dict):
            if token not in node:
                return default
            node = node[token]
        else:
            return default
    return node


def pointer_exists(doc, pointer: str) -> bool:
    _sentinel = object()
    return get_pointer(doc, pointer, _sentinel) is not _sentinel


def set_pointer(doc, pointer: str, value):
    """Return a deep copy of ``doc`` with ``pointer`` set to ``value``.

    Fail-closed: raises :class:`FixtureError` when the pointer path does not
    already exist (no silent path creation).
    """
    out = copy.deepcopy(doc)
    tokens = _pointer_tokens(pointer)
    node = out
    for token in tokens[:-1]:
        if isinstance(node, list):
            idx = int(token)
            if not 0 <= idx < len(node):
                raise FixtureError(f"pointer path missing at {pointer!r}")
            node = node[idx]
        elif isinstance(node, dict):
            if token not in node:
                raise FixtureError(f"pointer path missing at {pointer!r} (segment {token!r})")
            node = node[token]
        else:
            raise FixtureError(f"pointer path missing at {pointer!r}")
    last = tokens[-1]
    if isinstance(node, dict):
        if last not in node:
            raise FixtureError(f"pointer path missing at {pointer!r} (segment {last!r})")
        node[last] = value
    elif isinstance(node, list):
        idx = int(last)
        if not 0 <= idx < len(node):
            raise FixtureError(f"pointer path missing at {pointer!r} (index {last!r})")
        node[idx] = value
    else:
        raise FixtureError(f"pointer path missing at {pointer!r}")
    return out


def strip_pointer(doc, pointer: str):
    """Return ``(copy_without_pointer, found)`` with the pointer removed."""
    _sentinel = object()

    def _remove(node, tokens):
        if not tokens:
            raise FixtureError("internal: empty token list")
        token = tokens[0]
        if isinstance(node, list):
            idx = int(token)
            if not 0 <= idx < len(node):
                return False
            if len(tokens) == 1:
                del node[idx]
                return True
            return _remove(node[idx], tokens[1:])
        if isinstance(node, dict):
            if token not in node:
                return False
            if len(tokens) == 1:
                del node[token]
                return True
            return _remove(node[token], tokens[1:])
        return False

    out = copy.deepcopy(doc)
    found = _remove(out, _pointer_tokens(pointer))
    return out, found


# ---------------------------------------------------------------------------
# canonical baseline template
#
# Every frozen field of every challenge fixture lives here. Template defaults
# for the nine contested pointers are documented in ``README.md``; per-challenge
# fixtures overwrite their row pointer with the row baseline_value.
#
# Numeric conventions (deterministic, per contract numeric_reconciliation_policy):
# * rate: numerator 5 / denominator 42 (denom-001) = 0.119047...;
#   reported_value 0.119 is the declared display value at precision 3
#   (display_rounding_rule). Exact rational recomputation stays authoritative
#   for raw-value verdicts (raw_value_rule).
# * count: numerator 42 subjects <= denominator 42 subjects (same population
#   population-safety, same cutoff) per count_semantics_rule.
# * risk: project_member_count 4 == len(member_ids); project_total 12 ==
#   sum(site_totals).
# ---------------------------------------------------------------------------

CANONICAL_TEMPLATE: dict = {
    CANDIDATE_ROOT: {
        "identity": {
            "project_id": "project-r6-synthetic",
            "run_id": "run-r6-001",
            "mode": "daily",
            "execution_basis": "full",
            "data_cutoff": "cutoff-2026-08-01",
            "source_revision_id": "report-source-revision-001",
            "report_lineage_id": "lineage-r6-001",
            "report_revision_id": "report-revision-001",
            "report_source_revision_id": "report-source-revision-001",
            "report_artifact_id": "artifact-r6-001",
            "source_content_hash": "sha256-source-r6-001",
            "media_types": ["docx", "pdf", "html"],
            "knowledge_pack_version": "kp-r6-001",
            "rule_activation_version": "ra-r6-001",
            "mapping_version": "map-r6-001",
            "identity_algorithm_version": "ia-r6-001",
            "identity_algorithm_digest": "ia-digest-r6-001",
            "schema_version": "r6-contract-v0.1",
        },
        "source_locators": [
            "body-page-1/p-1",
            "table-1/r-2/c-3",
            "figure-1/caption",
            "figure-1/legend-b",
            "page-2/footnote-1",
            "page-1/table-1",
            "table-1/page-2",
            "#claim-001",
        ],
        "ambiguous_locators": [
            "figure-1/legend-ambiguous",
        ],
        "stale_or_missing_locators": [
            "missing-after-dom-change",
        ],
        "evidence_registry": [
            {
                "evidence_id": "fact-body-001",
                "authority_class": "source_record",
                "snapshot_id": "snap-r6-001",
                "data_cutoff": "cutoff-2026-08-01",
                "locator": "body-page-1/p-1",
                "content_hash": "sha256-evidence-fact-body-001",
                "relation": "supports",
            },
            {
                "evidence_id": "risk-authority-001",
                "authority_class": "risk_instance",
                "snapshot_id": "snap-r6-001",
                "data_cutoff": "cutoff-2026-08-01",
                "locator": "risk-domain/r6-001",
                "content_hash": "sha256-evidence-risk-authority-001",
                "relation": "context_only",
            },
        ],
        "populations": [
            "population-all-treated",
            "population-safety",
            "population-randomized",
        ],
        "cutoff_registry": [
            "cutoff-2026-08-01",
            "cutoff-fixed-001",
        ],
        "claim_registry": [
            {"claim_id": "claim-body-001", "unit_ids": ["body-001"], "kind": "numeric"},
            {"claim_id": "claim-table-001", "unit_ids": ["table-001"], "kind": "numeric"},
            {"claim_id": "claim-figure-rate-001", "unit_ids": ["figure-001"], "kind": "numeric"},
            {"claim_id": "claim-figure-trend-001", "unit_ids": ["figure-001"], "kind": "trend"},
            {"claim_id": "claim-multi-001", "unit_ids": ["body-001"], "kind": "numeric"},
        ],
        "issue_registry": [
            {
                "issue_id": "issue-omitted-001",
                "issue_kind": "omitted",
                "severity": "high",
                "lifecycle_state": "open",
                "revision_diff_state": "new",
            },
            {
                "issue_id": "issue-r6-001",
                "issue_kind": "unsupported",
                "severity": "medium",
                "lifecycle_state": "open",
                "revision_diff_state": "unresolved",
            },
            {
                "issue_id": "issue-r6-002",
                "issue_kind": "partially_supported",
                "severity": "medium",
                "lifecycle_state": "open",
                "revision_diff_state": "unresolved",
            },
            {
                "issue_id": "issue-r6-003",
                "issue_kind": "unsupported",
                "severity": "medium",
                "lifecycle_state": "open",
                "revision_diff_state": "new",
            },
        ],
        "body": {
            "unit_id": "body-001",
            "unit_type": "body",
            "paragraph": {
                "locator_ref": "body-page-1/p-1",
                "extractability": "text",
                "claim": {
                    "claim_id": "claim-body-001",
                    "claim_kind": "numeric",
                    "locator_ref": "body-page-1/p-1",
                    "evidence_refs": ["fact-body-001"],
                    "evidence_state": "complete",
                    "status": "supported",
                },
            },
        },
        "table": {
            "unit_id": "table-001",
            "unit_type": "table",
            "locator_ref": "page-1/table-1",
            "continuation_ref": "table-1/page-2",
            "row": {
                "coverage_status": "claimed",
                "claim": {
                    "claim_id": "claim-table-001",
                    "locator_ref": "table-1/r-2/c-3",
                    "population_ref": "population-all-treated",
                },
            },
            "summary": {
                "denominator_ref": "denom-table-001",
            },
        },
        "figure": {
            "unit_id": "figure-001",
            "unit_type": "figure",
            "extractability": "image",
            "coverage_status": "claimed",
            "raw_rate": 0.3333,
            "series": {
                "unit": "percent",
            },
            "legend": {
                "locator_ref": "figure-1/legend-b",
            },
            "caption": {
                "claim": {
                    "locator_ref": "figure-1/caption",
                },
            },
        },
        "footnote": {
            "unit_id": "footnote-001",
            "unit_type": "footnote",
            "coverage_status": "claimed",
            "extractability": "image",
            "claim": {
                "locator_ref": "page-2/footnote-1",
            },
        },
        "coverage_units": {
            "body": ["body-001"],
            "table": ["table-001"],
            "figure": ["figure-001"],
            "footnote": ["footnote-1"],
            "denominator": ["denom-001"],
            "cutoff": ["cutoff-2026-08-01"],
        },
        "denominator": {
            "ref": "denom-001",
            "value": 42,
            "unit": "subjects",
            "population_ref": "population-safety",
        },
        "denominator_registry": {
            "denom-001": {
                "value": 42,
                "unit": "subjects",
                "population_ref": "population-safety",
            },
            "denom-table-001": {
                "value": 42,
                "unit": "subjects",
                "population_ref": "population-all-treated",
            },
            "exposure-denom-001": {
                "value": 180,
                "unit": "person-weeks",
                "population_ref": "population-all-treated",
            },
        },
        "numerator": {
            "ref": "numerator-001",
            "value": 42,
            "unit": "subjects",
            "population_ref": "population-safety",
        },
        "rate": {
            "reported_value": 0.119,
            "display_precision": 3,
            "numerator": 5,
            "denominator_ref": "denom-001",
        },
        "count": {
            "unit": "subjects",
        },
        "exposure_rate": {
            "exposure_denominator_ref": "exposure-denom-001",
            "reported_value": 0.083,
            "display_precision": 3,
        },
        "cutoff": {
            "ref": "cutoff-2026-08-01",
            "status": "declared",
        },
        "source_revision": {
            "id": "report-revision-001",
            "role": "prior_report",
            "state": "immutable_frozen",
            "content_hash": "sha256-source-r6-001",
        },
        "revision": {
            "parent_report_ref": "report-previous-001",
            "report_revision_id": "report-revision-001",
            "previous_report_revision_id": "report-previous-001",
        },
        "run": {
            "run_id": "run-r6-001",
            "mode": "daily",
            "revision_transition": "explicit_new_run",
            "mode_transition": "explicit_new_run",
            "carry_forward_source_run": "run-daily-001",
            "carry_forward_compatibility": "compatible",
        },
        "cross_page": {
            "anchor_state": "unique",
            "anchor_ref": "page-1/table-1",
            "continuation_ref": "table-1/page-2",
        },
        "source_page": {
            "page_locator": "page-2",
            "extractability": "image",
        },
        "annotation": {
            "anchor_validation": "valid",
            "locator_ref": "body-page-1/p-1",
        },
        "html": {
            "dom_anchor": "#claim-001",
            "anchor_fallback_policy": "none",
        },
        "revision_issue": {
            "issue_id": "issue-r6-001",
            "transition_refs": [],
            "diff_state": "unresolved",
            "coverage_closed": True,
            "parent_report_ref": "report-previous-001",
        },
        "original_report": {
            "state": "immutable",
            "report_revision_id": "report-revision-001",
            "content_hash": "sha256-source-r6-001",
        },
        "daily": {
            "output_scope": "change_summary_plus_current_full_risk",
            "output_kinds": ["change_summary", "current_full_risk"],
            "prior_baseline_ref": "run-daily-prior-001",
        },
        "pre_lock": {
            "execution_basis": "full",
            "output_kinds": [
                "full_risk",
                "revision_impact",
                "check_package",
                "query_revision_package",
            ],
        },
        "post_lock": {
            "output_cutoff_ref": "cutoff-fixed-001",
            "output_revision_ref": "revision-fixed-001",
            "output_kinds": [
                "full_project_report",
                "site_materials",
                "subject_materials",
                "checklist",
            ],
        },
        "numeric": {
            "reconciliation_state": "unverified",
            "authority_ref": "run-r6-001",
            "cutoff_ref": "cutoff-2026-08-01",
        },
        "risk": {
            "project_total": 12,
            "site_totals": [5, 4, 3],
            "project_member_count": 4,
            "member_ids": ["subject-r6-01", "subject-r6-02", "subject-r6-03", "subject-r6-04"],
            "authority_run_ref": "run-r6-001",
        },
        "output": {
            "claim_status": "unsupported",
            "producer_kind": "external_report_review",
        },
        "aggregation": {
            "not_evaluable_as_zero": False,
        },
        "derivative": {
            "parent_source_ref": None,
            "derivative_content_hash": "sha256-content-preserved",
            "lineage_ref": "lineage-docx-pdf-001",
            "output_format": "pdf",
            "annotation_mode": "in_place_copy",
            "output_hash": "sha256-output-001",
            "draft_marker": None,
        },
        "source_ref_registry": {
            "source-docx-001": {
                "media_type": "docx",
                "content_hash": "sha256-source-r6-001",
            },
        },
        "lineage_registry": {
            "lineage-docx-pdf-001": {
                "parent_source_ref": "source-docx-001",
                "output_format": "pdf",
            },
        },
        "annotation_copy": {
            "artifact_id": "artifact-annotation-001",
            "source_content_hash": "sha256-original-report",
            "annotation_mode_declared": True,
        },
        "clean_draft": {
            "artifact_id": "artifact-draft-001",
            "draft_marker": "DRAFT",
            "publish_state": "eligible",
        },
        "publication": {
            "coverage_closed": True,
            "full_report_reviewed_eligible": False,
            "coverage_status": "partial",
            "evidence_state": "complete",
            "analysis_state": "running",
        },
        "report_review_matrix": {
            "claim_unit_links": {
                "figure-001": {
                    "unit_id": "figure-001",
                    "claim_ids": ["claim-figure-rate-001"],
                },
                "claim-multi-001": {
                    "claim_id": "claim-multi-001",
                    "unit_ids": ["body-001"],
                },
            },
            "expected_review_surface": [
                {
                    "expectation_id": "expectation-accepted-risk-001",
                    "expectation_kind": "accepted_risk",
                    "authority_ref": "risk-authority-001",
                    "scope": "project",
                    "temporal_window": "cutoff-2026-08-01",
                },
            ],
            "reverse_coverage_links": [
                {
                    "expectation_id": "expectation-accepted-risk-001",
                    "claim_ids": [],
                    "issue_ids": ["issue-omitted-001"],
                    "not_evaluable_exception": None,
                    "evidence_refs": ["risk-authority-001"],
                },
            ],
        },
    }
}


def template_bytes() -> bytes:
    return canonical_bytes(CANONICAL_TEMPLATE)


def template_sha256() -> str:
    return sha256_hex(canonical_bytes(CANONICAL_TEMPLATE))


# ---------------------------------------------------------------------------
# pointer preconditions
# ---------------------------------------------------------------------------

def verify_pointer_preconditions(fixture_doc, row: dict) -> list:
    """Return violation strings for one challenge row (empty list = pass).

    Checks, per the frozen ``fixture_binding.baseline_rule``:
    * the ``single_mutation.path`` pointer exists in the fixture document;
    * its value is type-aware equal to ``baseline_value``.
    """
    violations = []
    pointer = row["single_mutation"]["path"]
    if not pointer_exists(fixture_doc, pointer):
        violations.append(f"pointer_missing:{pointer}")
        return violations
    value = get_pointer(fixture_doc, pointer)
    if not strict_eq(value, row["baseline_value"]):
        violations.append(
            "baseline_mismatch:"
            + pointer
            + ":actual="
            + json.dumps(value, sort_keys=True, ensure_ascii=False)
            + ":expected="
            + json.dumps(row["baseline_value"], sort_keys=True, ensure_ascii=False)
        )
    return violations


def verify_freeze(fixture_doc, template, row: dict) -> list:
    """Verify non-mutated fields equal the template (pointer stripped)."""
    violations = []
    pointer = row["single_mutation"]["path"]
    stripped_fixture, found = strip_pointer(fixture_doc, pointer)
    stripped_template, template_found = strip_pointer(template, pointer)
    if not found:
        violations.append(f"pointer_missing:{pointer}")
    if not template_found:
        violations.append(f"template_pointer_missing:{pointer}")
    elif not strict_eq(stripped_fixture, stripped_template):
        violations.append(f"freeze_violation:{pointer}")
    return violations


# ---------------------------------------------------------------------------
# fixture and catalog construction
# ---------------------------------------------------------------------------

def build_fixture(challenge_id: str, row: dict, template=None) -> dict:
    """Build the frozen candidate document for one challenge row.

    Raises :class:`FixtureError` if any pointer precondition or freeze check
    fails. The input template is never mutated.
    """
    if template is None:
        template = CANONICAL_TEMPLATE
    pointer = row["single_mutation"]["path"]
    doc = set_pointer(template, pointer, row["baseline_value"])
    violations = verify_pointer_preconditions(doc, row)
    violations += verify_freeze(doc, template, row)
    if violations:
        raise FixtureError(f"{challenge_id}: " + "; ".join(violations))
    return doc


def build_fixture_catalog(rows: list, template=None) -> dict:
    """Build the deterministic baseline fixture catalog for all rows.

    The returned manifest includes per-fixture canonical SHA-256 digests and
    a fixed-point ``catalog_sha256`` (hash of the manifest without that key),
    so two builds over the same rows are byte-identical.
    """
    if template is None:
        template = CANONICAL_TEMPLATE
    ordered = sorted(rows, key=lambda r: r["challenge_id"])
    fixtures = []
    for row in ordered:
        cid = row["challenge_id"]
        doc = build_fixture(cid, row, template)
        raw = canonical_bytes(doc)
        fixtures.append(
            {
                "fixture_id": cid,
                "challenge_id": cid,
                "pointer": row["single_mutation"]["path"],
                "baseline_value": row["baseline_value"],
                "document_sha256": sha256_hex(raw),
                "document_bytes": len(raw),
            }
        )
    from .contracts import contested_paths

    payload = {
        "catalog_id": "mm_r6_baseline_fixture_catalog",
        "catalog_version": "0.1",
        "contract_id": CONTRACT_ID,
        "contract_version": CONTRACT_VERSION,
        "fixture_count": len(fixtures),
        "template_sha256": sha256_hex(canonical_bytes(template)),
        "contested_paths": contested_paths(ordered),
        "fixtures": fixtures,
    }
    payload["catalog_sha256"] = sha256_hex(canonical_bytes(payload))
    return payload


def canonical_catalog_bytes(catalog: dict) -> bytes:
    return canonical_bytes(catalog)


def verify_fixture_catalog(catalog: dict, rows: list, template=None) -> list:
    """Independently re-verify a catalog against its rows (empty list = pass)."""
    if template is None:
        template = CANONICAL_TEMPLATE
    violations = []
    expected_ids = {row["challenge_id"] for row in rows}
    entries = catalog.get("fixtures", [])
    if catalog.get("fixture_count") != len(entries) != len(expected_ids):
        violations.append(
            f"catalog_count:fixture_count={catalog.get('fixture_count')} "
            f"entries={len(entries)} rows={len(expected_ids)}"
        )
    if {e.get("challenge_id") for e in entries} != expected_ids:
        violations.append("catalog_ids_mismatch")
    for entry in entries:
        row = next((r for r in rows if r["challenge_id"] == entry["challenge_id"]), None)
        if row is None:
            violations.append(f"unknown_fixture:{entry.get('fixture_id')}")
            continue
        doc = build_fixture(entry["challenge_id"], row, template)
        actual_sha = sha256_hex(canonical_bytes(doc))
        if actual_sha != entry.get("document_sha256"):
            violations.append(
                f"document_sha_mismatch:{entry['challenge_id']}"
                f":catalog={entry.get('document_sha256')}:rebuilt={actual_sha}"
            )
        if not strict_eq(entry.get("baseline_value"), row["baseline_value"]):
            violations.append(f"baseline_mismatch:{entry['challenge_id']}")
    if catalog.get("template_sha256") != sha256_hex(canonical_bytes(template)):
        violations.append("template_sha_mismatch")
    expected_sha = sha256_hex(
        canonical_bytes({k: v for k, v in catalog.items() if k != "catalog_sha256"})
    )
    if catalog.get("catalog_sha256") != expected_sha:
        violations.append(
            f"catalog_sha_mismatch:catalog={catalog.get('catalog_sha256')}:expected={expected_sha}"
        )
    return violations
