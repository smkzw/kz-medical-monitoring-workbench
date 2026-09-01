"""R6 slice-03 ReportReviewBundle / annotated-projection runtime (synthetic/offline).

Work item 1 (worker_01): shared identity envelope, annotated projection with
sidecar-or-proven ``in_place_copy``, original-byte hash retention, matrix /
anchor-map hashes, and verified-anchor fail-closed gates.

Work item 2 (worker_02): optional DRAFT clean-draft provenance, IssueTransition
(reclassified/merge/split), and cross-revision issue diff with not_evaluable
when identity/cutoff/revision are incomparable.

Canonical JSON objects only. No DOCX/PDF/HTML parse or render. Stdlib only.
Does not mutate inputs. Does not invent or delete issues independently of the
matrix authority.
"""

from __future__ import annotations

import copy
import re
from typing import Any, Iterable, Mapping, Optional, Sequence, Tuple

from mm_r6.report_review import (
    ANCHOR_STATUSES,
    BUNDLE_STATES,
    COMMON_BINDING_REQUIRED,
    EVIDENCE_RELATIONS,
    EXECUTION_BASES,
    ISSUE_KINDS,
    ISSUE_REVISION_DIFF_STATES,
    MODES,
    canonical_bytes,
    sha256_hex,
    validate_report_review_matrix,
)

# Frozen three_piece_bundle.shared_identity_fields (contract.json) — 18 fields.
SHARED_IDENTITY_FIELDS: Tuple[str, ...] = (
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
    "report_lineage_id",
    "report_revision_id",
    "report_source_revision_id",
    "report_artifact_id",
    "coverage_ledger_id",
    "issue_set_hash",
)

ANNOTATION_MODES = frozenset({"sidecar", "in_place_copy"})
_ANCHORS_VERIFIED = frozenset({"verified", "not_applicable"})
_POSITIONAL_LOCATOR_FIELDS = frozenset(
    {
        "page",
        "page_number",
        "display_order",
        "order",
        "index",
        "report_revision_id",
        "report_artifact_id",
        "unit_type",
    }
)
_CONTENT_LOCATOR_FIELDS = frozenset(
    {
        "path",
        "json_pointer",
        "xpath",
        "unit_id",
        "anchor_digest",
        "content_hash",
        "section",
        "table",
        "figure",
        "footnote",
        "paragraph",
        "cell_range",
        "char_range",
    }
)
_ORDINAL_LOCATOR_FIELDS = frozenset(
    {"section", "table", "figure", "footnote", "paragraph"}
)

DRAFT_LABEL = "DRAFT"
ISSUE_TRANSITION_KINDS = frozenset({"reclassified", "merge", "split"})
_UNRESOLVED_LIFECYCLES = frozenset({"open", "partially_resolved", "reopened", "not_evaluable"})
_COMPARABILITY_FIELDS = (
    "project_id",
    "report_lineage_id",
    "identity_algorithm_version",
    "identity_algorithm_digest",
    "data_cutoff",
    "source_revision_id",
    "knowledge_pack_version",
    "rule_activation_version",
    "mapping_version",
)

ANNOTATED_PROJECTION_REQUIRED = (
    "artifact_type",
    "annotated_artifact_id",
    "annotation_mode",
    "source_bytes_hash",
    "matrix_content_hash",
    "annotations",
    "anchor_map",
    "anchor_map_hash",
    "anchor_status",
    "shared_identity",
    "blocking_reasons",
    "projection_state",
    "lossless_in_place_proven",
    "is_original_bytes_preserved",
    "is_in_place_source_mutation",
)

REPORT_REVIEW_BUNDLE_REQUIRED = (
    "bundle_id",
    "project_id",
    "run_id",
    "mode",
    "data_cutoff",
    "source_revision_id",
    "report_lineage_id",
    "report_revision_id",
    "report_source_revision_id",
    "report_artifact_id",
    "matrix_artifact_id",
    "annotated_artifact_id",
    "clean_draft_artifact_id",
    "matrix_content_hash",
    "annotation_map_hash",
    "issue_set_hash",
    "coverage_ledger_id",
    "bundle_state",
    "execution_basis",
    "knowledge_pack_version",
    "rule_activation_version",
    "mapping_version",
    "identity_algorithm_version",
    "identity_algorithm_digest",
    "schema_version",
    "shared_identity",
    "blocking_reasons",
)


class ReportBundleError(ValueError):
    """Fail-closed construction error with a frozen failure code."""

    def __init__(self, failure_code: str, message: str) -> None:
        self.failure_code = failure_code
        super().__init__(f"{failure_code}: {message}")


def _copy_mapping(obj: Mapping[str, Any]) -> dict:
    return copy.deepcopy(dict(obj))


def _stable_unique(values: Iterable[str]) -> Tuple[str, ...]:
    return tuple(sorted(set(values)))


def _content_id(prefix: str, payload: Any) -> str:
    return f"{prefix}-{sha256_hex(canonical_bytes(payload))}"


def _meaningful(value: Any) -> bool:
    return bool(value.strip()) if isinstance(value, str) else bool(value)


def compute_issue_set_hash(issues: Sequence[Mapping[str, Any]]) -> str:
    """Deterministic hash over the matrix issue set (ids + identity keys)."""
    rows = []
    for issue in issues or []:
        if not isinstance(issue, Mapping):
            continue
        rows.append(
            {
                "issue_id": issue.get("issue_id"),
                "issue_identity_key": issue.get("issue_identity_key"),
                "issue_kind": issue.get("issue_kind"),
                "lifecycle_state": issue.get("lifecycle_state"),
                "evidence_refs": copy.deepcopy(issue.get("evidence_refs") or []),
                "source_locators": copy.deepcopy(issue.get("source_locators") or []),
            }
        )
    rows.sort(key=lambda row: str(row.get("issue_id") or ""))
    return sha256_hex(canonical_bytes(rows))


def compute_matrix_content_hash(matrix: Mapping[str, Any]) -> str:
    """Hash the matrix authority payload (excludes derived matrix_id if present)."""
    payload = _copy_mapping(matrix)
    payload.pop("matrix_id", None)
    return sha256_hex(canonical_bytes(payload))


def extract_shared_identity(
    matrix: Mapping[str, Any],
    report_source: Optional[Mapping[str, Any]] = None,
    *,
    issue_set_hash: Optional[str] = None,
) -> dict:
    """Build the 18-field shared identity envelope from matrix (+ optional source).

    Does not invent identity: every field is copied from matrix run_binding /
    source_identity / coverage_ledger_id / computed issue_set_hash.
    """
    if not isinstance(matrix, Mapping):
        raise ReportBundleError("bundle_identity_mismatch", "matrix must be a mapping")
    binding = matrix.get("run_binding")
    source = matrix.get("source_identity")
    if not isinstance(binding, Mapping) or not isinstance(source, Mapping):
        raise ReportBundleError(
            "bundle_identity_mismatch",
            "matrix.run_binding and matrix.source_identity are required",
        )
    src = _copy_mapping(source)
    if report_source is not None:
        if not isinstance(report_source, Mapping):
            raise ReportBundleError(
                "bundle_identity_mismatch", "report_source must be a mapping"
            )
        # Prefer explicit report_source when provided; must agree with matrix.
        explicit = _copy_mapping(report_source)
        for field in (
            "project_id",
            "report_lineage_id",
            "report_revision_id",
            "report_source_revision_id",
            "report_artifact_id",
        ):
            if field in explicit and explicit.get(field) != src.get(field):
                raise ReportBundleError(
                    "bundle_identity_mismatch",
                    f"report_source.{field} disagrees with matrix.source_identity",
                )
        src.update({k: explicit[k] for k in explicit if k in src or k in (
            "project_id",
            "report_lineage_id",
            "report_revision_id",
            "report_source_revision_id",
            "report_artifact_id",
            "source_revision_id",
        )})

    issues = matrix.get("issues") if isinstance(matrix.get("issues"), list) else []
    computed_issue_hash = (
        issue_set_hash
        if isinstance(issue_set_hash, str) and issue_set_hash
        else compute_issue_set_hash(issues)
    )
    envelope = {
        "project_id": binding.get("project_id"),
        "run_id": binding.get("run_id"),
        "mode": binding.get("mode"),
        "execution_basis": binding.get("execution_basis"),
        "data_cutoff": binding.get("data_cutoff"),
        "source_revision_id": binding.get("source_revision_id"),
        "knowledge_pack_version": binding.get("knowledge_pack_version"),
        "rule_activation_version": binding.get("rule_activation_version"),
        "mapping_version": binding.get("mapping_version"),
        "identity_algorithm_version": binding.get("identity_algorithm_version"),
        "identity_algorithm_digest": binding.get("identity_algorithm_digest"),
        "schema_version": binding.get("schema_version"),
        "report_lineage_id": src.get("report_lineage_id"),
        "report_revision_id": src.get("report_revision_id"),
        "report_source_revision_id": src.get("report_source_revision_id"),
        "report_artifact_id": src.get("report_artifact_id"),
        "coverage_ledger_id": matrix.get("coverage_ledger_id"),
        "issue_set_hash": computed_issue_hash,
    }
    return envelope


def _locator_fingerprint(locator: Mapping[str, Any]) -> str:
    return sha256_hex(canonical_bytes(_copy_mapping(locator)))


def _locator_has_content_anchor(locator: Mapping[str, Any]) -> bool:
    for key in _CONTENT_LOCATOR_FIELDS:
        value = locator.get(key)
        if not _meaningful(value):
            continue
        if key in {"path", "json_pointer", "xpath"}:
            path = str(value).strip().lower().replace(" ", "")
            if re.fullmatch(
                r"(?:/+)?(?:page|pg|p)(?::|/|_|#|-)?\d+|"
                r"(?:/+)?(?:page|pg|p)\[\d+\]|\d+",
                path,
            ):
                continue
        if key in _ORDINAL_LOCATOR_FIELDS and re.fullmatch(
            r"\d+(?:\.\d+)*", str(value).strip()
        ):
            continue
        return True
    return False


def _index_verified_locators(matrix: Mapping[str, Any]) -> dict[str, dict]:
    """Map locator fingerprints to unit/issue provenance when anchors are verified."""
    indexed: dict[str, dict] = {}
    units = matrix.get("units") if isinstance(matrix.get("units"), list) else []
    entries = matrix.get("entries") if isinstance(matrix.get("entries"), list) else []
    entry_anchor = {
        str(entry.get("unit_id")): entry.get("anchor_status")
        for entry in entries
        if isinstance(entry, Mapping)
    }
    for unit in units:
        if not isinstance(unit, Mapping):
            continue
        locator = unit.get("locator")
        if (
            not isinstance(locator, Mapping)
            or not locator
            or not _locator_has_content_anchor(locator)
        ):
            continue
        unit_id = str(unit.get("unit_id") or "")
        status = unit.get("anchor_status")
        if status is None:
            status = entry_anchor.get(unit_id, "unverified")
        indexed[_locator_fingerprint(locator)] = {
            "kind": "unit",
            "unit_id": unit_id,
            "anchor_status": status,
            "locator": _copy_mapping(locator),
        }

    issues = matrix.get("issues") if isinstance(matrix.get("issues"), list) else []
    for issue in issues:
        if not isinstance(issue, Mapping):
            continue
        for locator in issue.get("source_locators") or []:
            if (
                not isinstance(locator, Mapping)
                or not locator
                or not _locator_has_content_anchor(locator)
            ):
                continue
            # Issue locators inherit verification from linked units when present.
            linked_statuses = []
            for unit_id in issue.get("unit_ids") or []:
                for meta in indexed.values():
                    if meta.get("kind") == "unit" and meta.get("unit_id") == str(unit_id):
                        linked_statuses.append(meta.get("anchor_status"))
            if linked_statuses and all(s in _ANCHORS_VERIFIED for s in linked_statuses):
                status = "verified"
            elif linked_statuses:
                status = next(
                    (s for s in linked_statuses if s not in _ANCHORS_VERIFIED),
                    "unverified",
                )
            else:
                status = "unverified"
            indexed[_locator_fingerprint(locator)] = {
                "kind": "issue",
                "issue_id": issue.get("issue_id"),
                "anchor_status": status,
                "locator": _copy_mapping(locator),
            }
    return indexed


def _validate_annotation_bindings(
    annotations: Sequence[Mapping[str, Any]],
    matrix: Mapping[str, Any],
    report_source: Mapping[str, Any],
    matrix_hash: str,
) -> Tuple[list[dict], list[dict], Tuple[str, ...]]:
    """Return normalized annotations, anchor_map rows, and frozen blocker codes."""
    codes: list[str] = []
    issue_index = {
        str(issue.get("issue_id")): issue
        for issue in (matrix.get("issues") or [])
        if isinstance(issue, Mapping) and issue.get("issue_id")
    }
    locator_index = _index_verified_locators(matrix)
    source_revision = report_source.get("report_revision_id")
    source_rsr = report_source.get("report_source_revision_id")
    source_artifact = report_source.get("report_artifact_id")

    normalized: list[dict] = []
    anchor_map: list[dict] = []

    for raw in annotations or []:
        if not isinstance(raw, Mapping):
            codes.append("annotation_anchor_invalid")
            continue
        ann = _copy_mapping(raw)
        annotation_id = ann.get("annotation_id")
        issue_id = ann.get("issue_id")
        locator = ann.get("locator")
        anchor_status = ann.get("anchor_status", "unverified")

        if not _meaningful(annotation_id):
            codes.append("annotation_anchor_invalid")
            continue
        if not _meaningful(issue_id) or str(issue_id) not in issue_index:
            # Projection cannot invent issues; unknown or missing issue fails closed.
            codes.append("annotation_anchor_invalid")
            continue
        if (
            not isinstance(locator, Mapping)
            or not locator
            or not _locator_has_content_anchor(locator)
        ):
            codes.append("annotation_anchor_invalid")
            continue
        if anchor_status not in ANCHOR_STATUSES:
            codes.append("annotation_anchor_invalid")
            continue

        locator = _copy_mapping(locator)
        # Bind revision / artifact onto locator when absent; disagree → fail closed.
        for field, expected in (
            ("report_revision_id", source_revision),
            ("report_artifact_id", source_artifact),
        ):
            if field in locator and locator.get(field) not in (None, expected):
                codes.append("annotation_anchor_invalid")
            else:
                locator.setdefault(field, expected)

        fp = _locator_fingerprint(locator)
        known = locator_index.get(fp)
        if known is None:
            codes.append("annotation_anchor_invalid")
            verified = False
        else:
            known_status = known.get("anchor_status")
            verified = (
                anchor_status in _ANCHORS_VERIFIED
                and known_status in _ANCHORS_VERIFIED
            )
            if not verified:
                codes.append("annotation_anchor_invalid")

        # Each annotation must declare matrix hash + source revision bindings.
        declared_matrix_hash = ann.get("matrix_content_hash", matrix_hash)
        declared_revision = ann.get("report_revision_id", source_revision)
        declared_rsr = ann.get("report_source_revision_id", source_rsr)
        if declared_matrix_hash != matrix_hash:
            codes.append("annotation_anchor_invalid")
        if declared_revision != source_revision or declared_rsr != source_rsr:
            codes.append("annotation_anchor_invalid")

        authoritative_evidence = copy.deepcopy(
            issue_index[str(issue_id)].get("evidence_refs") or []
        )
        if "evidence_refs" in ann and canonical_bytes(
            ann.get("evidence_refs") or []
        ) != canonical_bytes(authoritative_evidence):
            codes.append("annotation_anchor_invalid")

        bound = {
            "annotation_id": annotation_id,
            "issue_id": str(issue_id),
            "locator": locator,
            "anchor_status": anchor_status if verified else (
                anchor_status if anchor_status in ANCHOR_STATUSES else "unverified"
            ),
            "anchor_verified": bool(verified),
            "matrix_content_hash": matrix_hash,
            "report_revision_id": source_revision,
            "report_source_revision_id": source_rsr,
            "report_artifact_id": source_artifact,
            "evidence_refs": authoritative_evidence,
            "note": ann.get("note"),
        }
        # Preserve optional caller fields that are not identity-critical.
        for extra in ("markup", "sidecar_offset"):
            if extra in ann:
                bound[extra] = copy.deepcopy(ann[extra])
        normalized.append(bound)
        anchor_map.append(
            {
                "annotation_id": annotation_id,
                "issue_id": str(issue_id),
                "locator": locator,
                "locator_fingerprint": fp,
                "anchor_status": bound["anchor_status"],
                "anchor_verified": bound["anchor_verified"],
            }
        )

    normalized.sort(key=lambda row: str(row.get("annotation_id") or ""))
    anchor_map.sort(key=lambda row: str(row.get("annotation_id") or ""))
    return normalized, anchor_map, _stable_unique(codes)


def _aggregate_anchor_status(anchor_map: Sequence[Mapping[str, Any]]) -> str:
    if not anchor_map:
        return "not_applicable"
    statuses = [row.get("anchor_status") for row in anchor_map]
    if any(status == "broken" for status in statuses):
        return "broken"
    if any(status == "unverified" for status in statuses):
        return "unverified"
    if all(status in _ANCHORS_VERIFIED for status in statuses):
        if all(status == "not_applicable" for status in statuses):
            return "not_applicable"
        return "verified"
    return "unverified"


def build_annotated_projection(
    matrix: Mapping[str, Any],
    report_source: Mapping[str, Any],
    annotations: Sequence[Mapping[str, Any]],
    *,
    lossless_in_place_proven: bool,
) -> dict:
    """Build the required ``report_annotated_copy`` projection.

    ``lossless_in_place_proven`` must be an explicit caller assertion. When it is
    false, or when any annotation anchor fails verification, ``annotation_mode``
    is forced to ``sidecar`` and is never described as an in-place source edit.
    Original ``source_bytes_hash`` always equals ``report_artifact_id``.
    """
    if not isinstance(matrix, Mapping):
        raise ReportBundleError("bundle_identity_mismatch", "matrix must be a mapping")
    if not isinstance(report_source, Mapping):
        raise ReportBundleError(
            "bundle_identity_mismatch",
            "report_source must be a mapping",
        )
    if not isinstance(lossless_in_place_proven, bool):
        raise ReportBundleError(
            "annotation_anchor_invalid",
            "lossless_in_place_proven must be an explicit bool",
        )
    if isinstance(annotations, (str, bytes, bytearray)) or annotations is None:
        raise ReportBundleError(
            "annotation_anchor_invalid", "annotations must be a sequence of mappings"
        )

    matrix_copy = _copy_mapping(matrix)
    source_copy = _copy_mapping(report_source)
    shared = extract_shared_identity(matrix_copy, source_copy)
    matrix_hash = compute_matrix_content_hash(matrix_copy)
    source_bytes_hash = source_copy.get("report_artifact_id")
    if not _meaningful(source_bytes_hash):
        raise ReportBundleError(
            "bundle_identity_mismatch",
            "report_source.report_artifact_id is the retained source_bytes_hash",
        )

    # Identity agreement between matrix source and explicit report_source.
    identity_codes: list[str] = []
    for field in (
        "project_id",
        "report_lineage_id",
        "report_revision_id",
        "report_source_revision_id",
        "report_artifact_id",
    ):
        if matrix_copy.get("source_identity", {}).get(field) != source_copy.get(field):
            identity_codes.append("bundle_identity_mismatch")
    for field in COMMON_BINDING_REQUIRED:
        # COMMON_BINDING fields occupy the first 12 shared-identity slots.
        if field in shared and not _meaningful(shared.get(field)):
            identity_codes.append("bundle_identity_mismatch")
    if shared.get("mode") not in MODES or shared.get("execution_basis") not in EXECUTION_BASES:
        identity_codes.append("bundle_identity_mismatch")
    if shared.get("source_revision_id") in {
        shared.get("report_source_revision_id"),
        source_copy.get("source_revision_id"),
    }:
        # Run source_revision_id must stay distinct from report source revision.
        identity_codes.append("bundle_identity_mismatch")

    bound_annotations, anchor_map, anchor_codes = _validate_annotation_bindings(
        list(annotations),
        matrix_copy,
        source_copy,
        matrix_hash,
    )
    # Annotations may not invent or drop matrix issues: every annotation issue
    # is already checked for membership; unresolved matrix issues remain.
    matrix_issue_ids = {
        str(issue.get("issue_id"))
        for issue in (matrix_copy.get("issues") or [])
        if isinstance(issue, Mapping) and issue.get("issue_id")
    }
    annotated_issue_ids = {str(row.get("issue_id")) for row in bound_annotations}
    annotation_ids = [str(row.get("annotation_id")) for row in bound_annotations]
    if annotated_issue_ids != matrix_issue_ids or len(annotation_ids) != len(
        set(annotation_ids)
    ):
        identity_codes.append("annotation_anchor_invalid")

    aggregate_status = _aggregate_anchor_status(anchor_map)
    # Unproven lossless in-place → mandatory sidecar (not optional).
    annotation_mode = "sidecar"
    if lossless_in_place_proven:
        # Slice-03 has no byte/container fidelity proof artifact. A caller bool
        # is intent, not deterministic proof, so in-place remains unavailable.
        identity_codes.append("annotation_anchor_invalid")

    blocking = _stable_unique([*identity_codes, *anchor_codes])
    if annotation_mode == "in_place_copy" and not lossless_in_place_proven:
        # Defensive: never emit in_place_copy without the explicit proof flag.
        annotation_mode = "sidecar"
        blocking = _stable_unique([*blocking, "annotation_anchor_invalid"])

    anchor_map_hash = sha256_hex(canonical_bytes(anchor_map))
    projection_state = "qc_passed" if not blocking else "qc_blocked"
    payload = {
        "artifact_type": "report_annotated_copy",
        "payload_role": "projection",
        "annotation_mode": annotation_mode,
        "lossless_in_place_proven": bool(lossless_in_place_proven),
        "is_original_bytes_preserved": True,
        "is_in_place_source_mutation": False,
        "not_in_place_edit_of_original": annotation_mode == "sidecar",
        "source_bytes_hash": source_bytes_hash,
        "matrix_content_hash": matrix_hash,
        "annotations": bound_annotations,
        "anchor_map": anchor_map,
        "anchor_map_hash": anchor_map_hash,
        "anchor_status": aggregate_status,
        "shared_identity": shared,
        "issue_ids": sorted(matrix_issue_ids),
        "blocking_reasons": list(blocking),
        "projection_state": projection_state,
    }
    # Embed the 18 shared fields at the top level for envelope consumers.
    for field in SHARED_IDENTITY_FIELDS:
        payload[field] = shared.get(field)
    payload["annotated_artifact_id"] = _content_id("ann", payload)
    return payload


def _piece_shared_identity(piece: Mapping[str, Any]) -> Optional[dict]:
    if not isinstance(piece, Mapping):
        return None
    if isinstance(piece.get("shared_identity"), Mapping):
        env = _copy_mapping(piece["shared_identity"])
        # Fill from top-level when the nested envelope omitted a field.
        for field in SHARED_IDENTITY_FIELDS:
            if field not in env and field in piece:
                env[field] = piece.get(field)
        return env
    env = {}
    for field in SHARED_IDENTITY_FIELDS:
        if field in piece:
            env[field] = piece.get(field)
    return env if len(env) == len(SHARED_IDENTITY_FIELDS) else env


def _compare_shared_identity(
    expected: Mapping[str, Any],
    actual: Optional[Mapping[str, Any]],
    *,
    codes: list[str],
) -> None:
    if not isinstance(actual, Mapping):
        codes.append("bundle_identity_mismatch")
        return
    for field in SHARED_IDENTITY_FIELDS:
        if expected.get(field) != actual.get(field):
            codes.append("bundle_identity_mismatch")
            return


def build_report_review_bundle(
    matrix: Mapping[str, Any],
    annotated_projection: Mapping[str, Any],
    clean_draft: Optional[Mapping[str, Any]] = None,
) -> dict:
    """Assemble the ReportReviewBundle shared identity envelope.

    ``bundle_state`` is ``qc_passed`` only when matrix coverage/output gates,
    shared identity, annotation anchors, and projection integrity all pass.
    When a clean draft is supplied, DRAFT semantics (R6-C-DRAFT-001) are
    validated as well.
    """
    if not isinstance(matrix, Mapping):
        raise ReportBundleError("bundle_identity_mismatch", "matrix must be a mapping")
    if not isinstance(annotated_projection, Mapping):
        raise ReportBundleError(
            "bundle_identity_mismatch", "annotated_projection must be a mapping"
        )
    if clean_draft is not None and not isinstance(clean_draft, Mapping):
        raise ReportBundleError("bundle_identity_mismatch", "clean_draft must be a mapping")

    matrix_copy = _copy_mapping(matrix)
    projection = _copy_mapping(annotated_projection)
    draft = _copy_mapping(clean_draft) if clean_draft is not None else None

    shared = extract_shared_identity(matrix_copy)
    matrix_hash = compute_matrix_content_hash(matrix_copy)
    annotation_map_hash = projection.get("anchor_map_hash")
    matrix_artifact_id = matrix_copy.get("matrix_id") or _content_id("matrix", matrix_copy)
    annotated_artifact_id = projection.get("annotated_artifact_id")
    clean_draft_artifact_id = None
    if draft is not None:
        clean_draft_artifact_id = draft.get("clean_draft_artifact_id") or draft.get(
            "artifact_id"
        )

    bundle = {
        **shared,
        "bundle_id": "provisional",
        "matrix_artifact_id": matrix_artifact_id,
        "annotated_artifact_id": annotated_artifact_id,
        "clean_draft_artifact_id": clean_draft_artifact_id,
        "matrix_content_hash": matrix_hash,
        "annotation_map_hash": annotation_map_hash,
        "bundle_state": "assembled",
        "shared_identity": shared,
        "blocking_reasons": [],
        "producer_kind": "external_report_review",
        "pieces": {
            "report_review_matrix": True,
            "report_annotated_copy": True,
            "report_clean_draft": draft is not None,
        },
    }
    blockers = list(
        validate_report_review_bundle(bundle, matrix_copy, projection, draft)
    )
    bundle["blocking_reasons"] = list(blockers)
    bundle["bundle_state"] = "qc_passed" if not blockers else "qc_blocked"
    if bundle["bundle_state"] not in BUNDLE_STATES:
        bundle["bundle_state"] = "qc_blocked"
    # Content-address after state settles; provisional id is excluded from the digest.
    stamped = {key: value for key, value in bundle.items() if key != "bundle_id"}
    bundle["bundle_id"] = _content_id("bundle", stamped)
    return bundle


def validate_report_review_bundle(
    bundle: Mapping[str, Any],
    matrix: Mapping[str, Any],
    annotated_projection: Mapping[str, Any],
    clean_draft: Optional[Mapping[str, Any]] = None,
) -> Tuple[str, ...]:
    """Return all deterministic bundle blockers (never first-error-only).

    Uses frozen codes ``bundle_identity_mismatch`` and
    ``annotation_anchor_invalid`` plus adjacent matrix coverage codes when the
    matrix gate is already blocked.
    """
    codes: list[str] = []

    if not isinstance(bundle, Mapping):
        return ("bundle_identity_mismatch",)
    if not isinstance(matrix, Mapping) or not isinstance(annotated_projection, Mapping):
        return ("bundle_identity_mismatch",)
    if clean_draft is not None and not isinstance(clean_draft, Mapping):
        return ("bundle_identity_mismatch",)

    try:
        expected = extract_shared_identity(matrix)
    except ReportBundleError:
        return ("bundle_identity_mismatch",)

    # Matrix coverage / output gate — retain frozen adjacent codes.
    matrix_codes = validate_report_review_matrix(matrix)
    codes.extend(matrix_codes)

    # Bundle required fields.
    for field in REPORT_REVIEW_BUNDLE_REQUIRED:
        if field == "bundle_id" and bundle.get(field) == "provisional":
            continue
        if field == "clean_draft_artifact_id":
            continue
        if field not in bundle:
            codes.append("bundle_identity_mismatch")
    for field in (
        "bundle_id",
        "project_id",
        "run_id",
        "mode",
        "data_cutoff",
        "source_revision_id",
        "report_lineage_id",
        "report_revision_id",
        "report_source_revision_id",
        "report_artifact_id",
        "matrix_artifact_id",
        "annotated_artifact_id",
        "matrix_content_hash",
        "annotation_map_hash",
        "issue_set_hash",
        "coverage_ledger_id",
        "bundle_state",
    ):
        if field == "bundle_id" and bundle.get(field) == "provisional":
            continue
        if not _meaningful(bundle.get(field)):
            codes.append("bundle_identity_mismatch")
    if not isinstance(bundle.get("shared_identity"), Mapping) or not isinstance(
        bundle.get("blocking_reasons"), (list, tuple)
    ):
        codes.append("bundle_identity_mismatch")

    if bundle.get("bundle_state") not in BUNDLE_STATES:
        codes.append("bundle_identity_mismatch")

    # 18 shared identity fields on the envelope must match matrix.
    for field in SHARED_IDENTITY_FIELDS:
        if bundle.get(field) != expected.get(field):
            codes.append("bundle_identity_mismatch")
            break
    nested = bundle.get("shared_identity")
    if isinstance(nested, Mapping):
        for field in SHARED_IDENTITY_FIELDS:
            if nested.get(field) != expected.get(field):
                codes.append("bundle_identity_mismatch")
                break
    else:
        codes.append("bundle_identity_mismatch")

    # Annotated projection integrity.
    projection = annotated_projection
    for field in (
        "source_bytes_hash",
        "matrix_content_hash",
        "annotations",
        "anchor_map_hash",
        "anchor_status",
        "annotation_mode",
    ):
        if field not in projection:
            codes.append("annotation_anchor_invalid")

    if projection.get("annotation_mode") not in ANNOTATION_MODES:
        codes.append("annotation_anchor_invalid")
    if projection.get("payload_role") != "projection":
        codes.append("bundle_identity_mismatch")

    source = matrix.get("source_identity") if isinstance(matrix.get("source_identity"), Mapping) else {}
    if projection.get("source_bytes_hash") != source.get("report_artifact_id"):
        codes.append("bundle_identity_mismatch")
    if projection.get("is_original_bytes_preserved") is not True:
        codes.append("bundle_identity_mismatch")
    if projection.get("is_in_place_source_mutation") is not False:
        # Original must never be mutated; fail closed.
        codes.append("bundle_identity_mismatch")

    expected_matrix_hash = compute_matrix_content_hash(matrix)
    if projection.get("matrix_content_hash") != expected_matrix_hash:
        codes.append("bundle_identity_mismatch")
    if bundle.get("matrix_content_hash") not in (None, expected_matrix_hash):
        if bundle.get("matrix_content_hash") != expected_matrix_hash:
            codes.append("bundle_identity_mismatch")

    if bundle.get("annotation_map_hash") != projection.get("anchor_map_hash"):
        codes.append("bundle_identity_mismatch")

    expected_matrix_artifact_id = matrix.get("matrix_id") or _content_id(
        "matrix", matrix
    )
    if bundle.get("matrix_artifact_id") != expected_matrix_artifact_id:
        codes.append("bundle_identity_mismatch")
    projection_payload = {
        key: value for key, value in projection.items() if key != "annotated_artifact_id"
    }
    expected_projection_id = _content_id("ann", projection_payload)
    if projection.get("annotated_artifact_id") != expected_projection_id:
        codes.append("bundle_identity_mismatch")
    if bundle.get("annotated_artifact_id") != projection.get("annotated_artifact_id"):
        codes.append("bundle_identity_mismatch")

    # Shared identity across projection.
    _compare_shared_identity(
        expected, _piece_shared_identity(projection), codes=codes
    )

    # Anchor verification gate.
    annotations = projection.get("annotations")
    anchor_map = projection.get("anchor_map")
    if not isinstance(annotations, list) or not isinstance(anchor_map, list):
        codes.append("annotation_anchor_invalid")
    else:
        recomputed_hash = sha256_hex(canonical_bytes(anchor_map))
        if projection.get("anchor_map_hash") != recomputed_hash:
            codes.append("annotation_anchor_invalid")
        issue_ids = {
            str(issue.get("issue_id"))
            for issue in (matrix.get("issues") or [])
            if isinstance(issue, Mapping) and issue.get("issue_id")
        }
        projected_issue_ids = {
            str(issue_id)
            for issue_id in (projection.get("issue_ids") or [])
            if _meaningful(issue_id)
        }
        annotated_issue_ids: set[str] = set()
        annotation_ids: list[str] = []
        expected_anchor_map: list[dict] = []
        locator_index = _index_verified_locators(matrix)
        for ann in annotations:
            if not isinstance(ann, Mapping):
                codes.append("annotation_anchor_invalid")
                continue
            if str(ann.get("issue_id")) not in issue_ids:
                codes.append("annotation_anchor_invalid")
            else:
                annotated_issue_ids.add(str(ann.get("issue_id")))
            if not _meaningful(ann.get("annotation_id")):
                codes.append("annotation_anchor_invalid")
            else:
                annotation_ids.append(str(ann.get("annotation_id")))
            if ann.get("matrix_content_hash") != expected_matrix_hash:
                codes.append("annotation_anchor_invalid")
            if ann.get("report_revision_id") != source.get("report_revision_id"):
                codes.append("annotation_anchor_invalid")
            if ann.get("report_source_revision_id") != source.get(
                "report_source_revision_id"
            ):
                codes.append("annotation_anchor_invalid")
            if not ann.get("anchor_verified"):
                codes.append("annotation_anchor_invalid")
            if ann.get("anchor_status") not in _ANCHORS_VERIFIED:
                codes.append("annotation_anchor_invalid")
            locator = ann.get("locator")
            if not isinstance(locator, Mapping):
                codes.append("annotation_anchor_invalid")
                continue
            fingerprint = _locator_fingerprint(locator)
            known = locator_index.get(fingerprint)
            if not known or known.get("anchor_status") not in _ANCHORS_VERIFIED:
                codes.append("annotation_anchor_invalid")
            matrix_issue = next(
                (
                    issue
                    for issue in (matrix.get("issues") or [])
                    if isinstance(issue, Mapping)
                    and str(issue.get("issue_id")) == str(ann.get("issue_id"))
                ),
                None,
            )
            if matrix_issue is None or canonical_bytes(
                ann.get("evidence_refs") or []
            ) != canonical_bytes(matrix_issue.get("evidence_refs") or []):
                codes.append("annotation_anchor_invalid")
            expected_anchor_map.append(
                {
                    "annotation_id": ann.get("annotation_id"),
                    "issue_id": str(ann.get("issue_id")),
                    "locator": _copy_mapping(locator),
                    "locator_fingerprint": fingerprint,
                    "anchor_status": ann.get("anchor_status"),
                    "anchor_verified": ann.get("anchor_verified"),
                }
            )

        expected_anchor_map.sort(
            key=lambda row: str(row.get("annotation_id") or "")
        )
        if projected_issue_ids != issue_ids or annotated_issue_ids != issue_ids:
            codes.append("annotation_anchor_invalid")
        if len(annotation_ids) != len(set(annotation_ids)):
            codes.append("annotation_anchor_invalid")
        if canonical_bytes(anchor_map) != canonical_bytes(expected_anchor_map):
            codes.append("annotation_anchor_invalid")

        aggregate = projection.get("anchor_status")
        if annotations and aggregate not in _ANCHORS_VERIFIED:
            codes.append("annotation_anchor_invalid")

    # Unproven in-place must not claim in_place_copy.
    if (
        projection.get("annotation_mode") == "in_place_copy"
        or projection.get("lossless_in_place_proven") is True
    ):
        codes.append("annotation_anchor_invalid")
    if projection.get("annotation_mode") == "sidecar" and projection.get(
        "not_in_place_edit_of_original"
    ) is not True:
        codes.append("annotation_anchor_invalid")

    # Optional clean draft: shared identity + R6-C-DRAFT-001 semantics.
    if clean_draft is not None:
        draft_identity = _piece_shared_identity(clean_draft)
        _compare_shared_identity(expected, draft_identity, codes=codes)
        draft_hash = clean_draft.get("source_bytes_hash")
        if draft_hash != source.get("report_artifact_id"):
            codes.append("bundle_identity_mismatch")
        # Bundle nullable clean_draft_artifact_id must agree when both set.
        draft_id = clean_draft.get("clean_draft_artifact_id") or clean_draft.get(
            "artifact_id"
        )
        if bundle.get("clean_draft_artifact_id") != draft_id:
            codes.append("bundle_identity_mismatch")
        draft_payload = {
            key: value
            for key, value in clean_draft.items()
            if key != "clean_draft_artifact_id"
        }
        if draft_id != _content_id("draft", draft_payload):
            codes.append("bundle_identity_mismatch")
        if clean_draft.get("matrix_content_hash") != expected_matrix_hash:
            codes.append("bundle_identity_mismatch")
        if clean_draft.get("is_original_bytes_preserved") is not True:
            codes.append("bundle_identity_mismatch")
        if clean_draft.get("is_in_place_source_mutation") is not False:
            codes.append("bundle_identity_mismatch")

        # Visible DRAFT + non-final / non-user-confirmed.
        if clean_draft.get("draft_label") != DRAFT_LABEL:
            codes.append("draft_identity_invalid")
        if clean_draft.get("is_final") is not False:
            codes.append("draft_identity_invalid")
        if clean_draft.get("is_user_confirmed") is not False:
            codes.append("draft_identity_invalid")
        if clean_draft.get("artifact_type") not in (None, "report_clean_draft"):
            codes.append("draft_identity_invalid")
        if clean_draft.get("payload_role") != "projection":
            codes.append("draft_identity_invalid")
        for required in (
            "before_after_provenance",
            "issue_ids",
            "unresolved_conflicts",
            "source_bytes_hash",
        ):
            if required not in clean_draft:
                codes.append("draft_identity_invalid")

        matrix_issue_ids = {
            str(issue.get("issue_id"))
            for issue in (matrix.get("issues") or [])
            if isinstance(issue, Mapping) and issue.get("issue_id")
        }
        draft_issue_ids = {
            str(iid)
            for iid in (clean_draft.get("issue_ids") or [])
            if iid not in (None, "")
        }
        if matrix_issue_ids - draft_issue_ids:
            codes.append("unresolved_issue_dropped")

        unresolved_matrix = {
            str(issue.get("issue_id"))
            for issue in (matrix.get("issues") or [])
            if isinstance(issue, Mapping)
            and issue.get("issue_id")
            and issue.get("lifecycle_state") in _UNRESOLVED_LIFECYCLES
        }
        if unresolved_matrix - draft_issue_ids:
            codes.append("unresolved_issue_dropped")

        matrix_conflicts = matrix.get("unresolved_conflicts") or []
        draft_conflicts = clean_draft.get("unresolved_conflicts")
        if not isinstance(draft_conflicts, list):
            codes.append("unresolved_issue_dropped")
        elif canonical_bytes(draft_conflicts) != canonical_bytes(matrix_conflicts):
            codes.append("unresolved_issue_dropped")

        expected_unresolved = [
            _copy_mapping(issue)
            for issue in (matrix.get("issues") or [])
            if isinstance(issue, Mapping)
            and issue.get("lifecycle_state") in _UNRESOLVED_LIFECYCLES
        ]
        if canonical_bytes(clean_draft.get("unresolved_issues") or []) != canonical_bytes(
            expected_unresolved
        ):
            codes.append("unresolved_issue_dropped")
        expected_not_evaluable = _not_evaluable_units(matrix)
        if canonical_bytes(clean_draft.get("not_evaluable_units") or []) != canonical_bytes(
            expected_not_evaluable
        ):
            codes.append("unresolved_issue_dropped")
        expected_gaps = _missing_cutoff_or_version_notes(matrix)
        if canonical_bytes(clean_draft.get("cutoff_or_version_gaps") or []) != canonical_bytes(
            expected_gaps
        ):
            codes.append("unresolved_issue_dropped")

        # Modifications must cite matrix issues and carry before/after.
        provenance = clean_draft.get("before_after_provenance") or []
        if isinstance(provenance, list):
            for row in provenance:
                if not isinstance(row, Mapping):
                    codes.append("draft_identity_invalid")
                    continue
                linked = {
                    str(iid)
                    for iid in (row.get("issue_ids") or [])
                    if iid not in (None, "")
                }
                if not linked or linked - matrix_issue_ids:
                    codes.append("draft_identity_invalid")
                if "before" not in row or "after" not in row:
                    codes.append("draft_identity_invalid")

        # Blocked coverage cannot claim draft_exportable / exported.
        draft_blocked = bool(
            validate_report_review_matrix(matrix)
            or expected_unresolved
            or matrix_conflicts
            or expected_not_evaluable
            or expected_gaps
        )
        if draft_blocked and clean_draft.get("draft_exportable") is True:
            codes.append("draft_identity_invalid")
        if clean_draft.get("draft_state") == "exported":
            codes.append("draft_identity_invalid")

    # qc_passed claim requires empty blockers from projection itself.
    if (
        bundle.get("bundle_state") == "qc_passed"
        and projection.get("projection_state") == "qc_blocked"
    ):
        codes.append("annotation_anchor_invalid")

    # qc_passed is only legal when no blockers remain — checked by caller via
    # returned codes; do not self-add a loop on stored blocking_reasons.

    stable_codes = _stable_unique(codes)
    if bundle.get("bundle_id") not in (None, "provisional"):
        bundle_payload = {
            key: value for key, value in bundle.items() if key != "bundle_id"
        }
        if bundle.get("bundle_id") != _content_id("bundle", bundle_payload):
            stable_codes = _stable_unique(
                [*stable_codes, "bundle_identity_mismatch"]
            )
    if bundle.get("bundle_state") == "qc_passed":
        if stable_codes or bundle.get("blocking_reasons") not in ([], ()):
            stable_codes = _stable_unique(
                [*stable_codes, "bundle_identity_mismatch"]
            )
    elif bundle.get("bundle_state") == "qc_blocked":
        stored = _stable_unique(bundle.get("blocking_reasons") or [])
        if not stable_codes or stored != stable_codes:
            stable_codes = _stable_unique(
                [*stable_codes, "bundle_identity_mismatch"]
            )

    return stable_codes


# ---------------------------------------------------------------------------
# Worker_02: clean draft / IssueTransition / revision diff
# ---------------------------------------------------------------------------


def _matrix_issues(matrix: Mapping[str, Any]) -> list[dict]:
    raw = matrix.get("issues") if isinstance(matrix, Mapping) else None
    if not isinstance(raw, list):
        return []
    return [_copy_mapping(issue) for issue in raw if isinstance(issue, Mapping)]


def _index_issues_by_id(issues: Sequence[Mapping[str, Any]]) -> dict[str, dict]:
    indexed: dict[str, dict] = {}
    for issue in issues:
        if not isinstance(issue, Mapping):
            continue
        issue_id = issue.get("issue_id")
        if _meaningful(issue_id):
            indexed[str(issue_id)] = _copy_mapping(issue)
    return indexed


def _index_issues_by_identity_key(
    issues: Sequence[Mapping[str, Any]],
) -> dict[str, list[dict]]:
    indexed: dict[str, list[dict]] = {}
    for issue in issues:
        if not isinstance(issue, Mapping):
            continue
        key = issue.get("issue_identity_key")
        if not _meaningful(key):
            continue
        indexed.setdefault(str(key), []).append(_copy_mapping(issue))
    return indexed


def _normalize_id_list(values: Any, *, field: str, code: str) -> list[str]:
    if values is None:
        return []
    if isinstance(values, (str, bytes, bytearray)) or not isinstance(values, Sequence):
        raise ReportBundleError(code, f"{field} must be a sequence of ids")
    out: list[str] = []
    for item in values:
        if not _meaningful(item):
            raise ReportBundleError(code, f"{field} contains an empty id")
        out.append(str(item))
    return out


def _normalize_evidence_refs(values: Any, *, code: str) -> list[Any]:
    if values is None:
        return []
    if isinstance(values, (str, bytes, bytearray)) or not isinstance(values, Sequence):
        raise ReportBundleError(code, "evidence_refs must be a sequence")
    out: list[dict] = []
    required = (
        "evidence_id",
        "authority_class",
        "snapshot_id",
        "data_cutoff",
        "locator",
        "content_hash",
        "relation",
    )
    for item in values:
        if not isinstance(item, Mapping):
            raise ReportBundleError(code, "each evidence_ref must be a mapping")
        ref = _copy_mapping(item)
        if any(not _meaningful(ref.get(field)) for field in required):
            raise ReportBundleError(code, "evidence_ref is missing a required field")
        if ref.get("relation") not in EVIDENCE_RELATIONS:
            raise ReportBundleError(code, "evidence_ref relation is not canonical")
        if not (
            _meaningful(ref.get("source_revision_id"))
            or _meaningful(ref.get("authority_artifact_id"))
        ):
            raise ReportBundleError(
                code,
                "evidence_ref needs source_revision_id or authority_artifact_id",
            )
        out.append(ref)
    return out


def _not_evaluable_units(matrix: Mapping[str, Any]) -> list[dict]:
    rows: list[dict] = []
    for unit in matrix.get("units") or []:
        if not isinstance(unit, Mapping):
            continue
        if unit.get("coverage_status") == "not_evaluable" or unit.get(
            "anchor_status"
        ) in {"broken", "unverified"}:
            rows.append(
                {
                    "unit_id": unit.get("unit_id"),
                    "coverage_status": unit.get("coverage_status"),
                    "anchor_status": unit.get("anchor_status"),
                    "coverage_reason": unit.get("coverage_reason") or unit.get("reason"),
                }
            )
    for entry in matrix.get("entries") or []:
        if not isinstance(entry, Mapping):
            continue
        if entry.get("coverage_status") == "not_evaluable":
            rows.append(
                {
                    "unit_id": entry.get("unit_id"),
                    "coverage_status": entry.get("coverage_status"),
                    "anchor_status": entry.get("anchor_status"),
                    "coverage_reason": entry.get("reason"),
                }
            )
    rows.sort(key=lambda row: str(row.get("unit_id") or ""))
    return rows


def _missing_cutoff_or_version_notes(matrix: Mapping[str, Any]) -> list[dict]:
    notes: list[dict] = []
    binding = matrix.get("run_binding") if isinstance(matrix.get("run_binding"), Mapping) else {}
    source = (
        matrix.get("source_identity")
        if isinstance(matrix.get("source_identity"), Mapping)
        else {}
    )
    if not _meaningful(binding.get("data_cutoff")):
        notes.append({"kind": "missing_data_cutoff", "retained": True})
    if not _meaningful(binding.get("source_revision_id")):
        notes.append({"kind": "missing_source_revision_id", "retained": True})
    if not _meaningful(source.get("report_revision_id")):
        notes.append({"kind": "missing_report_revision_id", "retained": True})
    reported = source.get("reported_cutoff_status")
    if reported in {"missing", "unknown", None} and "reported_cutoff_status" in source:
        notes.append(
            {
                "kind": "reported_cutoff_gap",
                "reported_cutoff_status": reported,
                "retained": True,
            }
        )
    return notes


def _matrices_comparable(
    previous_matrix: Mapping[str, Any],
    current_matrix: Mapping[str, Any],
) -> Tuple[bool, str]:
    """Return (comparable, reason). Incompatible identity/cutoff → not_evaluable."""
    try:
        prev = extract_shared_identity(previous_matrix)
        curr = extract_shared_identity(current_matrix)
    except ReportBundleError as exc:
        return False, str(exc)
    for field in _COMPARABILITY_FIELDS:
        if prev.get(field) != curr.get(field):
            return False, f"incomparable_{field}"
    # Same lineage required for cross-revision issue identity continuity.
    if prev.get("report_lineage_id") != curr.get("report_lineage_id"):
        return False, "incomparable_report_lineage_id"
    return True, ""


def _substantive_issue_fingerprint(issue: Mapping[str, Any]) -> str:
    payload = {
        "issue_kind": issue.get("issue_kind"),
        "lifecycle_state": issue.get("lifecycle_state"),
        "claim_ids": copy.deepcopy(issue.get("claim_ids") or []),
        "unit_ids": copy.deepcopy(issue.get("unit_ids") or []),
        "evidence_refs": copy.deepcopy(issue.get("evidence_refs") or []),
        "source_locators": copy.deepcopy(issue.get("source_locators") or []),
        "current_note": issue.get("current_note"),
        "severity": issue.get("severity"),
    }
    return sha256_hex(canonical_bytes(payload))


def _derive_diff_state(
    previous: Optional[Mapping[str, Any]],
    current: Optional[Mapping[str, Any]],
    *,
    comparable: bool,
    via_transition: Optional[str] = None,
    resolution_proven: bool = False,
) -> str:
    if not comparable:
        return "not_evaluable"
    if previous is None and current is not None:
        return "new"
    if previous is not None and current is None:
        # Absent without a transition cannot be resolved; retain as not_evaluable.
        return "not_evaluable"
    if previous is None or current is None:
        return "not_evaluable"
    lifecycle = current.get("lifecycle_state")
    declared = current.get("revision_diff_state")
    if lifecycle == "not_evaluable":
        return "not_evaluable"
    if lifecycle == "superseded" or via_transition in {"merge", "split"} and lifecycle == "superseded":
        return "superseded"
    if lifecycle == "resolved":
        return "resolved" if resolution_proven else "not_evaluable"
    if lifecycle == "reopened":
        return "reopened"
    if lifecycle == "partially_resolved":
        return "partially_resolved"
    if lifecycle in {"open", "partially_resolved", "reopened"}:
        if _substantive_issue_fingerprint(previous) == _substantive_issue_fingerprint(
            current
        ):
            return "unchanged"
        return "unresolved"
    if declared in ISSUE_REVISION_DIFF_STATES and declared != "resolved":
        return str(declared)
    return "unresolved"


def _resolution_proven(
    previous: Mapping[str, Any],
    current: Mapping[str, Any],
    previous_matrix: Mapping[str, Any],
    current_matrix: Mapping[str, Any],
) -> bool:
    """Require changed evidence and a measurable open-to-closed correction."""
    if validate_report_review_matrix(current_matrix):
        return False
    eligibility = current_matrix.get("output_eligibility")
    if not isinstance(eligibility, Mapping) or eligibility.get("eligible") is not True:
        return False
    try:
        current_evidence = _normalize_evidence_refs(
            current.get("evidence_refs"), code="issue_transition_invalid"
        )
    except ReportBundleError:
        return False
    if not current_evidence:
        return False
    if canonical_bytes(current_evidence) == canonical_bytes(
        previous.get("evidence_refs") or []
    ):
        return False

    binding = current_matrix.get("run_binding")
    source = current_matrix.get("source_identity")
    if not isinstance(binding, Mapping) or not isinstance(source, Mapping):
        return False
    if any(ref.get("data_cutoff") != binding.get("data_cutoff") for ref in current_evidence):
        return False
    locators = current.get("source_locators")
    if not isinstance(locators, list) or not locators:
        return False
    if any(
        not isinstance(locator, Mapping)
        or not _locator_has_content_anchor(locator)
        or locator.get("report_revision_id") != source.get("report_revision_id")
        or locator.get("report_artifact_id") != source.get("report_artifact_id")
        for locator in locators
    ):
        return False

    issue_kind = current.get("issue_kind")
    if issue_kind in {"omitted", "coverage_gap"}:
        previous_unit_ids = {
            str(unit_id) for unit_id in (previous.get("unit_ids") or [])
        }
        linked_units = {str(unit_id) for unit_id in (current.get("unit_ids") or [])}
        previous_entries = {
            str(entry.get("unit_id")): entry
            for entry in (previous_matrix.get("entries") or [])
            if isinstance(entry, Mapping) and entry.get("unit_id")
        }
        current_entries = {
            str(entry.get("unit_id")): entry
            for entry in (current_matrix.get("entries") or [])
            if isinstance(entry, Mapping) and entry.get("unit_id")
        }
        was_open = bool(previous_unit_ids) and all(
            unit_id in previous_entries
            and (
                previous_entries[unit_id].get("coverage_status") != "claimed"
                or not previous_entries[unit_id].get("claim_ids")
            )
            for unit_id in previous_unit_ids
        )
        is_closed = (
            bool(linked_units)
            and previous_unit_ids.issubset(linked_units)
            and all(
                unit_id in current_entries
                and current_entries[unit_id].get("coverage_status") == "claimed"
                and bool(current_entries[unit_id].get("claim_ids"))
                for unit_id in linked_units
            )
            and all(
                unit_id in current_entries
                and current_entries[unit_id].get("coverage_status") == "claimed"
                and bool(current_entries[unit_id].get("claim_ids"))
                for unit_id in previous_unit_ids
            )
        )
        return was_open and is_closed

    previous_claim_ids = {
        str(claim_id) for claim_id in (previous.get("claim_ids") or [])
    }
    linked_claims = {str(claim_id) for claim_id in (current.get("claim_ids") or [])}
    previous_claims = {
        str(claim.get("claim_id")): claim
        for claim in (previous_matrix.get("claims") or [])
        if isinstance(claim, Mapping) and claim.get("claim_id")
    }
    current_claims = {
        str(claim.get("claim_id")): claim
        for claim in (current_matrix.get("claims") or [])
        if isinstance(claim, Mapping) and claim.get("claim_id")
    }
    was_open = bool(previous_claim_ids) and all(
        claim_id in previous_claims
        and previous_claims[claim_id].get("status") != "supported"
        for claim_id in previous_claim_ids
    )
    is_closed = (
        bool(linked_claims)
        and previous_claim_ids.issubset(linked_claims)
        and all(
            claim_id in current_claims
            and current_claims[claim_id].get("status") == "supported"
            for claim_id in linked_claims
        )
        and all(
            claim_id in current_claims
            and current_claims[claim_id].get("status") == "supported"
            for claim_id in previous_claim_ids
        )
    )
    return was_open and is_closed


def build_clean_draft(
    matrix: Mapping[str, Any],
    report_source: Mapping[str, Any],
    modifications: Sequence[Mapping[str, Any]],
    *,
    requested: bool,
) -> Optional[dict]:
    """Build optional ``report_clean_draft`` only when ``requested`` is true.

    Always stamps visible ``DRAFT``, ``is_final=false``, and
    ``is_user_confirmed=false``. Every modification must cite matrix issue ids
    and before/after provenance. Unresolved issues, conflicts, not_evaluable
    units, and cutoff/version gaps are retained — never deleted.
    """
    if not requested:
        return None
    if not isinstance(matrix, Mapping):
        raise ReportBundleError("draft_identity_invalid", "matrix must be a mapping")
    if not isinstance(report_source, Mapping):
        raise ReportBundleError(
            "draft_identity_invalid", "report_source must be a mapping"
        )
    if isinstance(modifications, (str, bytes, bytearray)) or modifications is None:
        raise ReportBundleError(
            "draft_identity_invalid", "modifications must be a sequence of mappings"
        )

    matrix_copy = _copy_mapping(matrix)
    source_copy = _copy_mapping(report_source)
    shared = extract_shared_identity(matrix_copy, source_copy)
    matrix_hash = compute_matrix_content_hash(matrix_copy)
    source_bytes_hash = source_copy.get("report_artifact_id")
    if not _meaningful(source_bytes_hash):
        raise ReportBundleError(
            "draft_identity_invalid",
            "report_source.report_artifact_id is the retained source_bytes_hash",
        )

    issues = _matrix_issues(matrix_copy)
    matrix_issue_ids = {
        str(issue.get("issue_id"))
        for issue in issues
        if issue.get("issue_id")
    }
    unresolved_issues = [
        _copy_mapping(issue)
        for issue in issues
        if issue.get("lifecycle_state") in _UNRESOLVED_LIFECYCLES
    ]
    unresolved_conflicts = copy.deepcopy(matrix_copy.get("unresolved_conflicts") or [])
    if not isinstance(unresolved_conflicts, list):
        unresolved_conflicts = []

    provenance: list[dict] = []
    for raw in modifications:
        if not isinstance(raw, Mapping):
            raise ReportBundleError(
                "draft_identity_invalid", "each modification must be a mapping"
            )
        mod = _copy_mapping(raw)
        modification_id = mod.get("modification_id")
        if not _meaningful(modification_id):
            raise ReportBundleError(
                "draft_identity_invalid", "modification_id is required"
            )
        linked = _normalize_id_list(
            mod.get("issue_ids"), field="issue_ids", code="draft_identity_invalid"
        )
        if not linked:
            raise ReportBundleError(
                "draft_identity_invalid",
                "every modification must map to one or more issue_ids",
            )
        unknown = [iid for iid in linked if iid not in matrix_issue_ids]
        if unknown:
            raise ReportBundleError(
                "draft_identity_invalid",
                f"modification cites unknown issue_ids: {unknown}",
            )
        if "before" not in mod or "after" not in mod:
            raise ReportBundleError(
                "draft_identity_invalid",
                "modification requires before/after provenance",
            )
        row = {
            "modification_id": str(modification_id),
            "issue_ids": linked,
            "before": copy.deepcopy(mod["before"]),
            "after": copy.deepcopy(mod["after"]),
            "scope": mod.get("scope"),
            "note": mod.get("note"),
            "retained_unresolved": bool(mod.get("retained_unresolved", False)),
        }
        provenance.append(row)

    provenance.sort(key=lambda row: str(row.get("modification_id") or ""))
    matrix_codes = validate_report_review_matrix(matrix_copy)
    not_evaluable_units = _not_evaluable_units(matrix_copy)
    cutoff_or_version_gaps = _missing_cutoff_or_version_notes(matrix_copy)
    draft_exportable = not bool(
        matrix_codes
        or unresolved_issues
        or unresolved_conflicts
        or not_evaluable_units
        or cutoff_or_version_gaps
    )
    # Even when exportable flag is true, creation is never final / user-confirmed.
    blocking: list[str] = []
    if matrix_codes:
        blocking.extend(matrix_codes)
        blocking.append("draft_identity_invalid")

    payload = {
        "artifact_type": "report_clean_draft",
        "payload_role": "projection",
        "draft_label": DRAFT_LABEL,
        "is_final": False,
        "is_user_confirmed": False,
        "draft_exportable": bool(draft_exportable),
        "draft_state": "internal_draft" if not draft_exportable else "draft_ready",
        "source_bytes_hash": source_bytes_hash,
        "matrix_content_hash": matrix_hash,
        "before_after_provenance": provenance,
        "modifications": copy.deepcopy(provenance),
        "issue_ids": sorted(matrix_issue_ids),
        "unresolved_issues": unresolved_issues,
        "unresolved_conflicts": unresolved_conflicts,
        "not_evaluable_units": not_evaluable_units,
        "cutoff_or_version_gaps": cutoff_or_version_gaps,
        "shared_identity": shared,
        "blocking_reasons": list(_stable_unique(blocking)),
        "is_original_bytes_preserved": True,
        "is_in_place_source_mutation": False,
        "producer_kind": "external_report_review",
    }
    for field in SHARED_IDENTITY_FIELDS:
        payload[field] = shared.get(field)
    payload["clean_draft_artifact_id"] = _content_id("draft", payload)
    return payload


def build_issue_transition(
    spec: Mapping[str, Any],
    from_issues: Sequence[Mapping[str, Any]],
    to_issues: Sequence[Mapping[str, Any]],
) -> dict:
    """Build an explicit IssueTransition (reclassified | merge | split).

    Every source and target issue id is preserved. Reclassification keeps the
    stable ``issue_identity_key`` and records before/after kind and evidence
    relation. Inputs are not mutated.
    """
    if not isinstance(spec, Mapping):
        raise ReportBundleError("issue_transition_invalid", "spec must be a mapping")
    if isinstance(from_issues, (str, bytes, bytearray)) or from_issues is None:
        raise ReportBundleError(
            "issue_transition_invalid", "from_issues must be a sequence"
        )
    if isinstance(to_issues, (str, bytes, bytearray)) or to_issues is None:
        raise ReportBundleError(
            "issue_transition_invalid", "to_issues must be a sequence"
        )

    data = _copy_mapping(spec)
    kind = data.get("transition_kind")
    if kind not in ISSUE_TRANSITION_KINDS:
        raise ReportBundleError(
            "issue_transition_invalid",
            f"transition_kind must be one of {sorted(ISSUE_TRANSITION_KINDS)}",
        )

    from_index = _index_issues_by_id(list(from_issues))
    to_index = _index_issues_by_id(list(to_issues))

    source_ids = _normalize_id_list(
        data.get("source_issue_ids"),
        field="source_issue_ids",
        code="issue_transition_invalid",
    )
    target_ids = _normalize_id_list(
        data.get("target_issue_ids"),
        field="target_issue_ids",
        code="issue_transition_invalid",
    )
    if not source_ids or not target_ids:
        raise ReportBundleError(
            "issue_transition_invalid",
            "source_issue_ids and target_issue_ids are required and non-empty",
        )
    if len(source_ids) != len(set(source_ids)) or len(target_ids) != len(
        set(target_ids)
    ):
        raise ReportBundleError(
            "issue_transition_invalid",
            "source_issue_ids and target_issue_ids must not contain duplicates",
        )
    missing_sources = [iid for iid in source_ids if iid not in from_index]
    missing_targets = [iid for iid in target_ids if iid not in to_index]
    if missing_sources or missing_targets:
        raise ReportBundleError(
            "issue_transition_invalid",
            "transition cites issue ids absent from from_issues/to_issues",
        )

    reason = data.get("reason")
    if not _meaningful(reason):
        raise ReportBundleError("issue_transition_invalid", "reason is required")
    evidence_refs = _normalize_evidence_refs(
        data.get("evidence_refs"), code="issue_transition_invalid"
    )
    if not evidence_refs:
        raise ReportBundleError(
            "issue_transition_invalid", "evidence_refs must be non-empty"
        )

    from_rev = data.get("from_report_revision_id")
    to_rev = data.get("to_report_revision_id")
    if not _meaningful(from_rev) or not _meaningful(to_rev):
        raise ReportBundleError(
            "issue_transition_invalid",
            "from_report_revision_id and to_report_revision_id are required",
        )

    source_issues = [from_index[iid] for iid in source_ids]
    target_issues = [to_index[iid] for iid in target_ids]
    if any(issue.get("report_revision_id") != from_rev for issue in source_issues):
        raise ReportBundleError(
            "issue_transition_invalid",
            "source issue revision does not match from_report_revision_id",
        )
    if any(issue.get("report_revision_id") != to_rev for issue in target_issues):
        raise ReportBundleError(
            "issue_transition_invalid",
            "target issue revision does not match to_report_revision_id",
        )

    before_kind = None
    after_kind = None
    before_relation = data.get("before_evidence_relation")
    after_relation = data.get("after_evidence_relation")

    if kind == "reclassified":
        if len(source_ids) != 1 or len(target_ids) != 1:
            raise ReportBundleError(
                "issue_transition_invalid",
                "reclassified requires exactly one source and one target issue",
            )
        src_issue = source_issues[0]
        tgt_issue = target_issues[0]
        if not _meaningful(src_issue.get("issue_identity_key")) or src_issue.get(
            "issue_identity_key"
        ) != tgt_issue.get("issue_identity_key"):
            raise ReportBundleError(
                "issue_transition_invalid",
                "reclassified must preserve issue_identity_key",
            )
        before_kind = data.get("before_issue_kind", src_issue.get("issue_kind"))
        after_kind = data.get("after_issue_kind", tgt_issue.get("issue_kind"))
        if before_kind not in ISSUE_KINDS or after_kind not in ISSUE_KINDS:
            raise ReportBundleError(
                "issue_transition_invalid",
                "reclassified before/after issue_kind must be canonical",
            )
        if before_kind == after_kind and before_relation == after_relation:
            # Still allow explicit no-op only when caller forces; prefer real change.
            if data.get("allow_noop") is not True:
                raise ReportBundleError(
                    "issue_transition_invalid",
                    "reclassified requires a kind or evidence_relation change",
                )
        for rel in (before_relation, after_relation):
            if rel is not None and rel not in EVIDENCE_RELATIONS:
                raise ReportBundleError(
                    "issue_transition_invalid",
                    "evidence_relation must be a frozen relation enum or null",
                )
    elif kind == "merge":
        if len(source_ids) < 2 or len(target_ids) != 1:
            raise ReportBundleError(
                "issue_transition_invalid",
                "merge requires >=2 source_issue_ids and exactly one target_issue_id",
            )
    elif kind == "split":
        if len(source_ids) != 1 or len(target_ids) < 2:
            raise ReportBundleError(
                "issue_transition_invalid",
                "split requires exactly one source and >=2 target_issue_ids",
            )

    # Preserve every listed id (already validated present); stamp stable order.
    preserved_sources = list(_stable_unique(source_ids))
    preserved_targets = list(_stable_unique(target_ids))

    transition = {
        "transition_kind": kind,
        "source_issue_ids": preserved_sources,
        "target_issue_ids": preserved_targets,
        "from_report_revision_id": str(from_rev),
        "to_report_revision_id": str(to_rev),
        "reason": str(reason),
        "evidence_refs": evidence_refs,
        "before_issue_kind": before_kind,
        "after_issue_kind": after_kind,
        "before_evidence_relation": before_relation,
        "after_evidence_relation": after_relation,
        "source_issue_identity_keys": [
            from_index[iid].get("issue_identity_key") for iid in preserved_sources
        ],
        "target_issue_identity_keys": [
            to_index[iid].get("issue_identity_key") for iid in preserved_targets
        ],
        "lifecycle_states_before": [
            from_index[iid].get("lifecycle_state") for iid in preserved_sources
        ],
        "lifecycle_states_after": [
            to_index[iid].get("lifecycle_state") for iid in preserved_targets
        ],
    }
    declared_id = data.get("transition_id")
    if _meaningful(declared_id):
        transition["transition_id"] = str(declared_id)
    else:
        transition["transition_id"] = _content_id("itr", transition)
    return transition


def build_revision_diff(
    previous_matrix: Mapping[str, Any],
    current_matrix: Mapping[str, Any],
    transitions: Sequence[Mapping[str, Any]] = (),
) -> list:
    """Diff issues across two report-review matrices.

    Emits one row per stable identity / transition group. When project/lineage/
    identity-algorithm/cutoff/source-revision are incompatible, every row is
    ``not_evaluable`` (never disguised as ``resolved``). Prior issues are never
    silently omitted.
    """
    if not isinstance(previous_matrix, Mapping) or not isinstance(current_matrix, Mapping):
        raise ReportBundleError(
            "issue_transition_invalid",
            "previous_matrix and current_matrix must be mappings",
        )
    if isinstance(transitions, (str, bytes, bytearray)) or transitions is None:
        raise ReportBundleError(
            "issue_transition_invalid", "transitions must be a sequence"
        )

    prev_issues = _matrix_issues(previous_matrix)
    curr_issues = _matrix_issues(current_matrix)
    prev_by_id = _index_issues_by_id(prev_issues)
    curr_by_id = _index_issues_by_id(curr_issues)
    prev_by_key = _index_issues_by_identity_key(prev_issues)
    curr_by_key = _index_issues_by_identity_key(curr_issues)

    comparable, incomparable_reason = _matrices_comparable(
        previous_matrix, current_matrix
    )
    prev_src = (
        previous_matrix.get("source_identity")
        if isinstance(previous_matrix.get("source_identity"), Mapping)
        else {}
    )
    curr_src = (
        current_matrix.get("source_identity")
        if isinstance(current_matrix.get("source_identity"), Mapping)
        else {}
    )
    from_rev = prev_src.get("report_revision_id")
    to_rev = curr_src.get("report_revision_id")

    consumed_prev: set[str] = set()
    consumed_curr: set[str] = set()
    rows: list[dict] = []

    normalized_transitions: list[dict] = []
    for raw in transitions:
        if not isinstance(raw, Mapping):
            raise ReportBundleError(
                "issue_transition_invalid", "each transition must be a mapping"
            )
        transition = build_issue_transition(raw, prev_issues, curr_issues)
        if transition.get("from_report_revision_id") != from_rev or transition.get(
            "to_report_revision_id"
        ) != to_rev:
            raise ReportBundleError(
                "issue_transition_invalid",
                "transition revisions must match the compared matrices",
            )
        normalized_transitions.append(transition)

    for transition in normalized_transitions:
        source_ids = [str(x) for x in transition["source_issue_ids"]]
        target_ids = [str(x) for x in transition["target_issue_ids"]]
        kind = str(transition["transition_kind"])
        if consumed_prev.intersection(source_ids) or consumed_curr.intersection(
            target_ids
        ):
            raise ReportBundleError(
                "issue_transition_invalid",
                "an issue cannot participate in multiple transitions in one diff",
            )
        prev_sample = prev_by_id[source_ids[0]]
        curr_sample = curr_by_id[target_ids[0]]
        resolution_proven = all(
            _resolution_proven(
                prev_by_id[source_id],
                curr_by_id[target_id],
                previous_matrix,
                current_matrix,
            )
            for source_id in source_ids
            for target_id in target_ids
        )
        state = _derive_diff_state(
            prev_sample,
            curr_sample,
            comparable=comparable,
            via_transition=kind,
            resolution_proven=resolution_proven,
        )
        if kind in {"merge", "split"} and comparable:
            # Merge/split are occurrence changes; lifecycle of targets drives state,
            # but never upgrade incomparable comparisons.
            lifecycles = {
                curr_by_id[iid].get("lifecycle_state") for iid in target_ids
            }
            if lifecycles == {"resolved"}:
                state = "resolved" if resolution_proven else "not_evaluable"
            elif lifecycles == {"superseded"} or any(
                prev_by_id[iid].get("lifecycle_state") == "superseded"
                for iid in source_ids
            ):
                state = "superseded"
            elif "partially_resolved" in lifecycles:
                state = "partially_resolved"
            elif "reopened" in lifecycles:
                state = "reopened"
            elif "not_evaluable" in lifecycles or not comparable:
                state = "not_evaluable"
            else:
                state = "unresolved"
        if not comparable:
            state = "not_evaluable"
        rows.append(
            {
                "issue_identity_key": prev_sample.get("issue_identity_key")
                or curr_sample.get("issue_identity_key"),
                "source_issue_ids": list(_stable_unique(source_ids)),
                "target_issue_ids": list(_stable_unique(target_ids)),
                "from_report_revision_id": from_rev,
                "to_report_revision_id": to_rev,
                "revision_diff_state": state,
                "lifecycle_state_before": [
                    prev_by_id[iid].get("lifecycle_state") for iid in source_ids
                ],
                "lifecycle_state_after": [
                    curr_by_id[iid].get("lifecycle_state") for iid in target_ids
                ],
                "transition_refs": [
                    transition.get("transition_id")
                    or _content_id("itr", transition)
                ],
                "transition_kind": kind,
                "reason": transition.get("reason")
                or (incomparable_reason if not comparable else kind),
                "evidence_refs": copy.deepcopy(transition.get("evidence_refs") or []),
                "comparable": comparable,
                "incomparable_reason": None if comparable else incomparable_reason,
            }
        )
        consumed_prev.update(source_ids)
        consumed_curr.update(target_ids)

    # Identity-key matches not covered by an explicit transition.
    for key, prev_group in sorted(prev_by_key.items()):
        curr_group = curr_by_key.get(key, [])
        remaining_prev = [
            issue
            for issue in prev_group
            if str(issue.get("issue_id")) not in consumed_prev
        ]
        remaining_curr = [
            issue
            for issue in curr_group
            if str(issue.get("issue_id")) not in consumed_curr
        ]
        if not remaining_prev and not remaining_curr:
            continue
        if len(remaining_prev) > 1 or len(remaining_curr) > 1:
            ambiguous = [(item, "source") for item in remaining_prev] + [
                (item, "target") for item in remaining_curr
            ]
            for issue, side in ambiguous:
                issue_id = str(issue.get("issue_id"))
                rows.append(
                    {
                        "issue_identity_key": key,
                        "source_issue_ids": [issue_id] if side == "source" else [],
                        "target_issue_ids": [issue_id] if side == "target" else [],
                        "from_report_revision_id": from_rev,
                        "to_report_revision_id": to_rev,
                        "revision_diff_state": "not_evaluable",
                        "lifecycle_state_before": [issue.get("lifecycle_state")]
                        if side == "source"
                        else [],
                        "lifecycle_state_after": [issue.get("lifecycle_state")]
                        if side == "target"
                        else [],
                        "transition_refs": [],
                        "transition_kind": None,
                        "reason": "ambiguous_identity_requires_transition",
                        "evidence_refs": copy.deepcopy(
                            issue.get("evidence_refs") or []
                        ),
                        "comparable": False,
                        "incomparable_reason": "ambiguous_identity_requires_transition",
                    }
                )
                (consumed_prev if side == "source" else consumed_curr).add(
                    issue_id
                )
            continue
        # Pair by order within the identity key; unpaired retained explicitly.
        paired = min(len(remaining_prev), len(remaining_curr))
        for idx in range(paired):
            prev_issue = remaining_prev[idx]
            curr_issue = remaining_curr[idx]
            state = _derive_diff_state(
                prev_issue,
                curr_issue,
                comparable=comparable,
                resolution_proven=_resolution_proven(
                    prev_issue,
                    curr_issue,
                    previous_matrix,
                    current_matrix,
                ),
            )
            if not comparable:
                state = "not_evaluable"
            rows.append(
                {
                    "issue_identity_key": key,
                    "source_issue_ids": [str(prev_issue.get("issue_id"))],
                    "target_issue_ids": [str(curr_issue.get("issue_id"))],
                    "from_report_revision_id": from_rev,
                    "to_report_revision_id": to_rev,
                    "revision_diff_state": state,
                    "lifecycle_state_before": [prev_issue.get("lifecycle_state")],
                    "lifecycle_state_after": [curr_issue.get("lifecycle_state")],
                    "transition_refs": [],
                    "transition_kind": None,
                    "reason": incomparable_reason
                    if not comparable
                    else f"identity_match:{state}",
                    "evidence_refs": copy.deepcopy(
                        curr_issue.get("evidence_refs") or []
                    ),
                    "comparable": comparable,
                    "incomparable_reason": None if comparable else incomparable_reason,
                }
            )
            consumed_prev.add(str(prev_issue.get("issue_id")))
            consumed_curr.add(str(curr_issue.get("issue_id")))
        for prev_issue in remaining_prev[paired:]:
            state = "not_evaluable" if not comparable else "not_evaluable"
            rows.append(
                {
                    "issue_identity_key": key,
                    "source_issue_ids": [str(prev_issue.get("issue_id"))],
                    "target_issue_ids": [],
                    "from_report_revision_id": from_rev,
                    "to_report_revision_id": to_rev,
                    "revision_diff_state": state,
                    "lifecycle_state_before": [prev_issue.get("lifecycle_state")],
                    "lifecycle_state_after": [],
                    "transition_refs": [],
                    "transition_kind": None,
                    "reason": incomparable_reason
                    if not comparable
                    else "prior_issue_absent_without_transition",
                    "evidence_refs": copy.deepcopy(
                        prev_issue.get("evidence_refs") or []
                    ),
                    "comparable": comparable,
                    "incomparable_reason": None
                    if comparable
                    else incomparable_reason,
                }
            )
            consumed_prev.add(str(prev_issue.get("issue_id")))
        for curr_issue in remaining_curr[paired:]:
            state = "not_evaluable" if not comparable else "new"
            rows.append(
                {
                    "issue_identity_key": key,
                    "source_issue_ids": [],
                    "target_issue_ids": [str(curr_issue.get("issue_id"))],
                    "from_report_revision_id": from_rev,
                    "to_report_revision_id": to_rev,
                    "revision_diff_state": state,
                    "lifecycle_state_before": [],
                    "lifecycle_state_after": [curr_issue.get("lifecycle_state")],
                    "transition_refs": [],
                    "transition_kind": None,
                    "reason": incomparable_reason
                    if not comparable
                    else "new_issue",
                    "evidence_refs": copy.deepcopy(
                        curr_issue.get("evidence_refs") or []
                    ),
                    "comparable": comparable,
                    "incomparable_reason": None
                    if comparable
                    else incomparable_reason,
                }
            )
            consumed_curr.add(str(curr_issue.get("issue_id")))

    # Issues lacking identity keys still must not disappear.
    for issue in prev_issues:
        iid = str(issue.get("issue_id") or "")
        if not iid or iid in consumed_prev:
            continue
        state = "not_evaluable"
        rows.append(
            {
                "issue_identity_key": issue.get("issue_identity_key"),
                "source_issue_ids": [iid],
                "target_issue_ids": [],
                "from_report_revision_id": from_rev,
                "to_report_revision_id": to_rev,
                "revision_diff_state": state,
                "lifecycle_state_before": [issue.get("lifecycle_state")],
                "lifecycle_state_after": [],
                "transition_refs": [],
                "transition_kind": None,
                "reason": incomparable_reason
                if not comparable
                else "prior_issue_retained_without_identity_match",
                "evidence_refs": copy.deepcopy(issue.get("evidence_refs") or []),
                "comparable": comparable,
                "incomparable_reason": None if comparable else incomparable_reason,
            }
        )
        consumed_prev.add(iid)
    for issue in curr_issues:
        iid = str(issue.get("issue_id") or "")
        if not iid or iid in consumed_curr:
            continue
        state = "not_evaluable" if not comparable else "new"
        rows.append(
            {
                "issue_identity_key": issue.get("issue_identity_key"),
                "source_issue_ids": [],
                "target_issue_ids": [iid],
                "from_report_revision_id": from_rev,
                "to_report_revision_id": to_rev,
                "revision_diff_state": state,
                "lifecycle_state_before": [],
                "lifecycle_state_after": [issue.get("lifecycle_state")],
                "transition_refs": [],
                "transition_kind": None,
                "reason": incomparable_reason if not comparable else "new_issue",
                "evidence_refs": copy.deepcopy(issue.get("evidence_refs") or []),
                "comparable": comparable,
                "incomparable_reason": None if comparable else incomparable_reason,
            }
        )
        consumed_curr.add(iid)

    # Never emit resolved when incomparable.
    for row in rows:
        if not row.get("comparable") and row.get("revision_diff_state") == "resolved":
            row["revision_diff_state"] = "not_evaluable"
        if row.get("revision_diff_state") not in ISSUE_REVISION_DIFF_STATES:
            row["revision_diff_state"] = "not_evaluable"

    rows.sort(
        key=lambda row: (
            str(row.get("issue_identity_key") or ""),
            ",".join(row.get("source_issue_ids") or []),
            ",".join(row.get("target_issue_ids") or []),
        )
    )
    return rows
