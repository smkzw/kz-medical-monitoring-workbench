"""R6 slice-02 report source/object runtime (synthetic/offline).

Implements the create-only source and object surface for the second R6
vertical slice:

* immutable ``ReportSourceRevision`` registration with raw-byte SHA-256,
  same-hash deduplication, and parent lineage;
* deterministic ``ReportUnit``, ``ReportClaim``, and ``ReviewIssue``
  construction (many-to-many unit/claim/issue identity);
* cross-identity checks that keep Run ``source_revision_id`` distinct from
  report ``report_source_revision_id``.

The coverage surface (worker_02) adds the ``ReportReviewMatrix`` builder,
the frozen expected review surface with exact reverse coverage links, the
``ClaimCoverageLedger`` builder, and the coverage-closed /
full-report-reviewed-eligible double gate. Stdlib only. No real reports,
OCR, models, or medical conclusions.
"""

from __future__ import annotations

import copy
import hashlib
import json
from typing import Any, Iterable, Mapping, Optional, Sequence, Tuple

# Canonical JSON options match fixtures.py: key-sorted, compact, UTF-8.
_CANONICAL_JSON_OPTS = {
    "ensure_ascii": False,
    "sort_keys": True,
    "separators": (",", ":"),
}

# Frozen enum sets from contract.json (do not invent synonyms).
REPORT_MEDIA_TYPES = frozenset({"docx", "pdf", "html", "other"})
REPORTED_CUTOFF_STATUSES = frozenset({"declared", "missing", "ambiguous"})
REPORT_UNIT_TYPES = frozenset(
    {
        "document",
        "page",
        "section",
        "body",
        "table",
        "figure",
        "footnote",
        "denominator",
        "cutoff",
    }
)
CLAIM_KINDS = frozenset(
    {
        "numeric",
        "categorical",
        "temporal",
        "trend",
        "comparison",
        "risk_statement",
        "scope_qualifier",
        "conclusion",
        "other",
    }
)
CLAIM_STATUSES = frozenset(
    {
        "supported",
        "partially_supported",
        "unsupported",
        "outdated_wrong_cutoff",
        "overstated",
        "understated",
        "internally_inconsistent",
        "not_evaluable",
    }
)
SCOPES = frozenset({"project", "site", "subject", "risk_domain", "other"})
ISSUE_KINDS = frozenset(
    {
        "unsupported",
        "partially_supported",
        "outdated_wrong_cutoff",
        "overstated",
        "understated",
        "internally_inconsistent",
        "omitted",
        "not_evaluable",
        "anchor_invalid",
        "coverage_gap",
        "source_revision_mismatch",
        "identity_mismatch",
        "unresolved_conflict",
    }
)
ISSUE_SEVERITIES = frozenset(
    {"info", "low", "medium", "high", "critical", "unknown"}
)
ISSUE_LIFECYCLE_STATES = frozenset(
    {
        "open",
        "partially_resolved",
        "resolved",
        "superseded",
        "not_evaluable",
        "reopened",
    }
)
ISSUE_REVISION_DIFF_STATES = frozenset(
    {
        "new",
        "unchanged",
        "unresolved",
        "partially_resolved",
        "resolved",
        "reopened",
        "superseded",
        "not_evaluable",
    }
)
EXTRACTABILITIES = frozenset(
    {"text", "table", "vector", "image", "ocr", "unextractable", "unknown"}
)
EVIDENCE_RELATIONS = frozenset(
    {"supports", "contradicts", "qualifies", "context_only"}
)

# Descriptor fields required to register a report source.
_DESCRIPTOR_REQUIRED = (
    "project_id",
    "media_type",
    "source_name",
    "reported_cutoff_status",
    "received_at",
    "source_scope",
    "report_lineage_id",
)

# Nullable descriptor fields (explicit null is allowed; silent default is not).
_DESCRIPTOR_NULLABLE = frozenset(
    {"reported_version_label", "reported_data_cutoff", "parent_report_revision_id"}
)

REPORT_SOURCE_REQUIRED = (
    "report_lineage_id",
    "report_revision_id",
    "source_revision_id",
    "report_source_revision_id",
    "report_artifact_id",
    "project_id",
    "media_type",
    "source_name",
    "reported_version_label",
    "reported_data_cutoff",
    "reported_cutoff_status",
    "received_at",
    "parent_report_revision_id",
    "source_scope",
    "immutable",
)

CLAIM_IDENTITY_KEY_FORMULA = (
    "project_id",
    "report_lineage_id",
    "scope",
    "normalized_claim_concept",
    "normalized_subject_or_site_scope",
    "normalized_temporal_window",
    "identity_algorithm_version",
    "identity_algorithm_digest",
)

ISSUE_IDENTITY_KEY_FORMULA = (
    "project_id",
    "report_lineage_id",
    "normalized_clinical_concept",
    "normalized_subject_or_site_scope",
    "normalized_temporal_window",
    "identity_algorithm_version",
    "identity_algorithm_digest",
)


class ReportReviewError(ValueError):
    """Fail-closed construction/registration error with a frozen failure code."""

    def __init__(self, failure_code: str, message: str) -> None:
        self.failure_code = failure_code
        super().__init__(f"{failure_code}: {message}")


def canonical_bytes(obj: Any) -> bytes:
    """Return deterministic UTF-8 canonical JSON bytes."""
    return json.dumps(obj, **_CANONICAL_JSON_OPTS).encode("utf-8")


def sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def raw_report_artifact_id(raw_bytes: bytes) -> str:
    """Content-addressed raw-byte identity for ``report_artifact_id``."""
    if not isinstance(raw_bytes, (bytes, bytearray, memoryview)):
        raise ReportReviewError(
            "source_revision_mismatch",
            "raw_bytes must be bytes-like; paths/filenames are not source identity",
        )
    return sha256_hex(bytes(raw_bytes))


def identity_key_digest(components: Sequence[Any], *, prefix: str) -> str:
    """SHA-256 over the ordered identity-key component tuple (canonical JSON)."""
    digest = sha256_hex(canonical_bytes(list(components)))
    return f"{prefix}-{digest}"


def _require_non_empty_str(value: Any, field: str, failure_code: str) -> str:
    if not isinstance(value, str) or value.strip() == "":
        raise ReportReviewError(
            failure_code, f"{field} must be a non-empty string"
        )
    return value


def _require_enum(value: Any, field: str, allowed: frozenset, failure_code: str) -> str:
    text = _require_non_empty_str(value, field, failure_code)
    if text not in allowed:
        raise ReportReviewError(
            failure_code,
            f"{field}={text!r} is not a frozen enum value",
        )
    return text


def _copy_mapping(obj: Mapping[str, Any]) -> dict:
    return copy.deepcopy(dict(obj))


def _normalize_list(values: Optional[Iterable[Any]], *, field: str) -> list:
    if values is None:
        return []
    if isinstance(values, (str, bytes, bytearray)):
        raise ReportReviewError(
            "identity_mismatch",
            f"{field} must be a list, not a string",
        )
    out = list(values)
    return out


def _stable_unique(values: Iterable[str]) -> Tuple[str, ...]:
    """Deduplicate while imposing a deterministic sorted order."""
    return tuple(sorted(set(values)))


def compute_claim_identity_key(
    *,
    project_id: str,
    report_lineage_id: str,
    scope: str,
    normalized_claim_concept: str,
    normalized_subject_or_site_scope: str,
    normalized_temporal_window: str,
    identity_algorithm_version: str,
    identity_algorithm_digest: str,
) -> str:
    """Deterministic cross-revision claim identity key (contract §3.3)."""
    components = [
        project_id,
        report_lineage_id,
        scope,
        normalized_claim_concept,
        normalized_subject_or_site_scope,
        normalized_temporal_window,
        identity_algorithm_version,
        identity_algorithm_digest,
    ]
    return identity_key_digest(components, prefix="cik")


def compute_issue_identity_key(
    *,
    project_id: str,
    report_lineage_id: str,
    normalized_clinical_concept: str,
    normalized_subject_or_site_scope: str,
    normalized_temporal_window: str,
    identity_algorithm_version: str,
    identity_algorithm_digest: str,
) -> str:
    """Deterministic cross-revision issue identity key (contract §3.3)."""
    components = [
        project_id,
        report_lineage_id,
        normalized_clinical_concept,
        normalized_subject_or_site_scope,
        normalized_temporal_window,
        identity_algorithm_version,
        identity_algorithm_digest,
    ]
    return identity_key_digest(components, prefix="iik")


def _derive_report_revision_id(
    project_id: str, report_lineage_id: str, report_artifact_id: str
) -> str:
    return identity_key_digest(
        [project_id, report_lineage_id, report_artifact_id],
        prefix="rr",
    )


def _derive_report_source_revision_id(report_artifact_id: str) -> str:
    # Content-addressed generic SourceRevision for the report bytes themselves.
    return f"rsr-{report_artifact_id}"


def _index_revisions(
    existing_revisions: Sequence[Mapping[str, Any]],
) -> dict[str, dict]:
    indexed: dict[str, dict] = {}
    for raw in existing_revisions:
        rev = _copy_mapping(raw)
        rid = rev.get("report_revision_id")
        if not isinstance(rid, str) or not rid:
            raise ReportReviewError(
                "source_revision_mismatch",
                "existing revision missing report_revision_id",
            )
        if rid in indexed:
            raise ReportReviewError(
                "source_revision_mismatch",
                f"duplicate report_revision_id in existing_revisions: {rid}",
            )
        indexed[rid] = rev
    return indexed


def _find_dedup_match(
    existing: Mapping[str, Mapping[str, Any]],
    *,
    project_id: str,
    report_lineage_id: str,
    report_artifact_id: str,
) -> Optional[dict]:
    matches = [
        rev
        for rev in existing.values()
        if rev.get("project_id") == project_id
        and rev.get("report_lineage_id") == report_lineage_id
        and rev.get("report_artifact_id") == report_artifact_id
    ]
    if not matches:
        return None
    # Prefer the earliest parent-chain head for stable return (same content).
    matches.sort(key=lambda r: str(r.get("report_revision_id")))
    return _copy_mapping(matches[0])


def _validate_descriptor(descriptor: Mapping[str, Any]) -> dict:
    if not isinstance(descriptor, Mapping):
        raise ReportReviewError(
            "source_revision_mismatch", "descriptor must be a mapping"
        )
    desc = _copy_mapping(descriptor)
    for field in _DESCRIPTOR_REQUIRED:
        if field not in desc:
            raise ReportReviewError(
                "source_revision_mismatch",
                f"descriptor missing required field {field}",
            )
        if field == "media_type":
            _require_enum(
                desc[field], field, REPORT_MEDIA_TYPES, "source_revision_mismatch"
            )
        elif field == "reported_cutoff_status":
            _require_enum(
                desc[field],
                field,
                REPORTED_CUTOFF_STATUSES,
                "source_revision_mismatch",
            )
        elif field == "source_scope":
            # source_scope may be a string or structured object; require non-empty.
            if desc[field] is None or desc[field] == "" or desc[field] == {}:
                raise ReportReviewError(
                    "source_revision_mismatch",
                    "source_scope must be present and non-empty",
                )
        else:
            _require_non_empty_str(desc[field], field, "source_revision_mismatch")

    # Explicit missing data — never invent current version/cutoff defaults.
    for field in _DESCRIPTOR_NULLABLE:
        if field not in desc:
            desc[field] = None
        elif desc[field] is not None and field != "parent_report_revision_id":
            if field == "reported_version_label" and desc[field] == "":
                desc[field] = None
            elif field == "reported_data_cutoff" and desc[field] == "":
                desc[field] = None

    if desc["reported_cutoff_status"] == "declared":
        if desc.get("reported_data_cutoff") in (None, ""):
            raise ReportReviewError(
                "source_revision_mismatch",
                "reported_cutoff_status=declared requires reported_data_cutoff",
            )
    if desc["reported_cutoff_status"] in {"missing", "ambiguous"}:
        # Keep whatever was supplied, but do not coerce to a run cutoff.
        pass

    # Optional Run binding for separation checks at registration time.
    if "run_source_revision_id" in desc and desc["run_source_revision_id"] is not None:
        _require_non_empty_str(
            desc["run_source_revision_id"],
            "run_source_revision_id",
            "identity_mismatch",
        )
    return desc


def register_report_source(
    raw_bytes: bytes,
    descriptor: Mapping[str, Any],
    existing_revisions: Sequence[Mapping[str, Any]] = (),
) -> dict:
    """Register immutable report bytes or return the existing same-hash revision.

    Returns a canonical-JSON-serializable dict::

        {
          "status": "registered" | "deduplicated",
          "report_artifact_id": <sha256 hex of raw_bytes>,
          "report_source_revision": {ReportSourceRevision...},
          "generic_source_revision": {
              "source_revision_id": <equals report_source_revision_id>,
              "content_hash": <report_artifact_id>,
              "immutable": true
          }
        }

    Inputs are never mutated. Same ``project_id`` + ``report_lineage_id`` +
    raw-byte hash is deduplicated and is not a new clinical revision. New
    content always creates new ``report_revision_id`` /
    ``report_source_revision_id`` with parent lineage when
    ``parent_report_revision_id`` is provided.
    """
    desc = _validate_descriptor(descriptor)
    artifact_id = raw_report_artifact_id(raw_bytes)
    indexed = _index_revisions(existing_revisions)

    existing_match = _find_dedup_match(
        indexed,
        project_id=desc["project_id"],
        report_lineage_id=desc["report_lineage_id"],
        report_artifact_id=artifact_id,
    )
    if existing_match is not None:
        if existing_match.get("immutable") is not True:
            raise ReportReviewError(
                "source_not_immutable",
                "existing same-hash revision is not immutable",
            )
        return {
            "status": "deduplicated",
            "report_artifact_id": artifact_id,
            "report_source_revision": existing_match,
            "generic_source_revision": {
                "source_revision_id": existing_match["report_source_revision_id"],
                "content_hash": artifact_id,
                "immutable": True,
            },
        }

    parent_id = desc.get("parent_report_revision_id")
    if parent_id is not None:
        parent_id = _require_non_empty_str(
            parent_id, "parent_report_revision_id", "source_revision_mismatch"
        )
        parent = indexed.get(parent_id)
        if parent is None:
            raise ReportReviewError(
                "source_revision_mismatch",
                f"parent_report_revision_id {parent_id!r} not in existing_revisions",
            )
        if parent.get("project_id") != desc["project_id"]:
            raise ReportReviewError(
                "identity_mismatch",
                "parent revision project_id does not match descriptor",
            )
        if parent.get("report_lineage_id") != desc["report_lineage_id"]:
            raise ReportReviewError(
                "source_revision_mismatch",
                "parent revision report_lineage_id does not match descriptor",
            )
        if parent.get("report_artifact_id") == artifact_id:
            # Same bytes should have taken the dedup path; defensive fail-closed.
            raise ReportReviewError(
                "source_revision_mismatch",
                "parent has identical report_artifact_id; use dedup path",
            )

    # Prefer caller-supplied revision IDs when present and well-formed; otherwise
    # derive content-addressed identities. report_source_revision_id MUST equal
    # the report's generic SourceRevision.source_revision_id.
    report_revision_id = desc.get("report_revision_id")
    if report_revision_id is None:
        report_revision_id = _derive_report_revision_id(
            desc["project_id"], desc["report_lineage_id"], artifact_id
        )
    else:
        report_revision_id = _require_non_empty_str(
            report_revision_id, "report_revision_id", "source_revision_mismatch"
        )
        if report_revision_id in indexed:
            raise ReportReviewError(
                "source_revision_mismatch",
                f"report_revision_id {report_revision_id!r} already registered",
            )

    rsr_id = desc.get("report_source_revision_id") or desc.get("source_revision_id")
    if rsr_id is None:
        rsr_id = _derive_report_source_revision_id(artifact_id)
    else:
        rsr_id = _require_non_empty_str(
            rsr_id, "report_source_revision_id", "source_revision_mismatch"
        )

    run_src = desc.get("run_source_revision_id")
    if run_src is not None and run_src == rsr_id:
        raise ReportReviewError(
            "identity_mismatch",
            "Run source_revision_id must not equal report_source_revision_id",
        )

    revision = {
        "report_lineage_id": desc["report_lineage_id"],
        "report_revision_id": report_revision_id,
        "source_revision_id": rsr_id,
        "report_source_revision_id": rsr_id,
        "report_artifact_id": artifact_id,
        "project_id": desc["project_id"],
        "media_type": desc["media_type"],
        "source_name": desc["source_name"],
        "reported_version_label": desc.get("reported_version_label"),
        "reported_data_cutoff": desc.get("reported_data_cutoff"),
        "reported_cutoff_status": desc["reported_cutoff_status"],
        "received_at": desc["received_at"],
        "parent_report_revision_id": parent_id,
        "source_scope": copy.deepcopy(desc["source_scope"]),
        "immutable": True,
    }
    _assert_report_source_shape(revision)

    return {
        "status": "registered",
        "report_artifact_id": artifact_id,
        "report_source_revision": revision,
        "generic_source_revision": {
            "source_revision_id": rsr_id,
            "content_hash": artifact_id,
            "immutable": True,
        },
    }


def _assert_report_source_shape(revision: Mapping[str, Any]) -> None:
    for field in REPORT_SOURCE_REQUIRED:
        if field not in revision:
            raise ReportReviewError(
                "source_revision_mismatch",
                f"ReportSourceRevision missing {field}",
            )
    if revision.get("immutable") is not True:
        raise ReportReviewError(
            "source_not_immutable",
            "immutable must be true after registration",
        )
    if revision["source_revision_id"] != revision["report_source_revision_id"]:
        raise ReportReviewError(
            "source_revision_mismatch",
            "report_source_revision_id must equal the report generic "
            "SourceRevision.source_revision_id",
        )


def build_report_unit(
    spec: Mapping[str, Any],
    report_source: Mapping[str, Any],
) -> dict:
    """Build a deterministic ``ReportUnit`` bound to ``report_source``.

    Does not mutate inputs. ``parent_unit_id`` must be null only for
    ``unit_type=document``.
    """
    src = _copy_mapping(report_source)
    _assert_report_source_shape(src)
    data = _copy_mapping(spec)

    unit_id = _require_non_empty_str(data.get("unit_id"), "unit_id", "identity_mismatch")
    unit_type = _require_enum(
        data.get("unit_type"), "unit_type", REPORT_UNIT_TYPES, "identity_mismatch"
    )
    if "required" not in data or not isinstance(data["required"], bool):
        raise ReportReviewError(
            "identity_mismatch", "required must be a boolean"
        )
    extractability = _require_enum(
        data.get("extractability"),
        "extractability",
        EXTRACTABILITIES,
        "identity_mismatch",
    )
    anchor_digest = _require_non_empty_str(
        data.get("anchor_digest"), "anchor_digest", "identity_mismatch"
    )
    locator = data.get("locator")
    if not isinstance(locator, Mapping) or not locator:
        raise ReportReviewError(
            "identity_mismatch", "locator must be a non-empty mapping"
        )
    locator = _copy_mapping(locator)
    if locator.get("report_revision_id") not in (None, src["report_revision_id"]):
        raise ReportReviewError(
            "revision_mismatch",
            "unit locator.report_revision_id disagrees with report_source",
        )
    locator.setdefault("report_revision_id", src["report_revision_id"])
    locator.setdefault("unit_id", unit_id)
    locator.setdefault("unit_type", unit_type)
    locator.setdefault("report_artifact_id", src["report_artifact_id"])

    parent_unit_id = data.get("parent_unit_id", None)
    if unit_type == "document":
        if parent_unit_id is not None:
            raise ReportReviewError(
                "identity_mismatch",
                "document unit must have parent_unit_id=null",
            )
    else:
        parent_unit_id = _require_non_empty_str(
            parent_unit_id, "parent_unit_id", "identity_mismatch"
        )

    unit = {
        "unit_id": unit_id,
        "unit_type": unit_type,
        "report_revision_id": src["report_revision_id"],
        "parent_unit_id": parent_unit_id,
        "required": data["required"],
        "locator": locator,
        "extractability": extractability,
        "anchor_digest": anchor_digest,
        "declared_cutoff": data.get("declared_cutoff"),
        "computed_cutoff": data.get("computed_cutoff"),
    }
    return unit


def _validate_evidence_refs(refs: Sequence[Any]) -> list:
    out = []
    for idx, raw in enumerate(refs):
        if not isinstance(raw, Mapping):
            raise ReportReviewError(
                "evidence_comparison_missing",
                f"evidence_refs[{idx}] must be a mapping",
            )
        ref = _copy_mapping(raw)
        for field in (
            "evidence_id",
            "authority_class",
            "snapshot_id",
            "data_cutoff",
            "locator",
            "content_hash",
            "relation",
        ):
            if field not in ref:
                raise ReportReviewError(
                    "evidence_comparison_missing",
                    f"evidence_refs[{idx}] missing {field}",
                )
        _require_enum(
            ref["relation"],
            "relation",
            EVIDENCE_RELATIONS,
            "evidence_comparison_missing",
        )
        has_src = bool(ref.get("source_revision_id"))
        has_art = bool(ref.get("authority_artifact_id"))
        if not has_src and not has_art:
            raise ReportReviewError(
                "evidence_comparison_missing",
                f"evidence_refs[{idx}] needs source_revision_id or "
                "authority_artifact_id",
            )
        out.append(ref)
    return out


def build_report_claim(
    spec: Mapping[str, Any],
    report_source: Mapping[str, Any],
    *,
    identity_algorithm_version: str,
    identity_algorithm_digest: str,
) -> dict:
    """Build a deterministic ``ReportClaim`` bound to ``report_source``."""
    src = _copy_mapping(report_source)
    _assert_report_source_shape(src)
    data = _copy_mapping(spec)

    claim_id = _require_non_empty_str(
        data.get("claim_id"), "claim_id", "identity_mismatch"
    )
    project_id = _require_non_empty_str(
        data.get("project_id", src["project_id"]),
        "project_id",
        "identity_mismatch",
    )
    if project_id != src["project_id"]:
        raise ReportReviewError(
            "identity_mismatch",
            "claim project_id disagrees with report_source",
        )
    run_id = _require_non_empty_str(data.get("run_id"), "run_id", "identity_mismatch")
    unit_ids = _normalize_list(data.get("unit_ids"), field="unit_ids")
    if not unit_ids:
        raise ReportReviewError("claim_without_unit", "unit_ids must be one_or_more")
    for uid in unit_ids:
        _require_non_empty_str(uid, "unit_ids[]", "claim_without_unit")
    claim_kind = _require_enum(
        data.get("claim_kind"), "claim_kind", CLAIM_KINDS, "claim_not_evaluable"
    )
    status = _require_enum(
        data.get("status"), "status", CLAIM_STATUSES, "claim_not_evaluable"
    )
    scope = _require_enum(data.get("scope"), "scope", SCOPES, "identity_mismatch")
    source_text = data.get("source_text")
    if not isinstance(source_text, str):
        raise ReportReviewError(
            "claim_not_evaluable", "source_text must be a string"
        )
    normalized_claim_concept = _require_non_empty_str(
        data.get("normalized_claim_concept"),
        "normalized_claim_concept",
        "identity_mismatch",
    )
    temporal_window = data.get("temporal_window")
    if temporal_window is None or temporal_window == "":
        raise ReportReviewError(
            "identity_mismatch", "temporal_window must be present"
        )
    report_cutoff_status = _require_enum(
        data.get("report_cutoff_status", src["reported_cutoff_status"]),
        "report_cutoff_status",
        REPORTED_CUTOFF_STATUSES,
        "cutoff_mismatch",
    )
    report_cutoff = data.get("report_cutoff", src.get("reported_data_cutoff"))
    if report_cutoff_status == "declared" and report_cutoff in (None, ""):
        raise ReportReviewError(
            "cutoff_mismatch",
            "declared report_cutoff_status requires report_cutoff",
        )

    subject_scope = data.get(
        "normalized_subject_or_site_scope",
        data.get("scope_detail", scope),
    )
    subject_scope = _require_non_empty_str(
        subject_scope,
        "normalized_subject_or_site_scope",
        "identity_mismatch",
    )
    temporal_norm = data.get("normalized_temporal_window", temporal_window)
    if not isinstance(temporal_norm, str) or not temporal_norm:
        # Allow structured temporal_window; normalize via canonical bytes.
        temporal_norm = sha256_hex(canonical_bytes(temporal_window))

    ia_ver = _require_non_empty_str(
        identity_algorithm_version,
        "identity_algorithm_version",
        "identity_mismatch",
    )
    ia_dig = _require_non_empty_str(
        identity_algorithm_digest,
        "identity_algorithm_digest",
        "identity_mismatch",
    )

    provided_key = data.get("claim_identity_key")
    computed_key = compute_claim_identity_key(
        project_id=project_id,
        report_lineage_id=src["report_lineage_id"],
        scope=scope,
        normalized_claim_concept=normalized_claim_concept,
        normalized_subject_or_site_scope=subject_scope,
        normalized_temporal_window=str(temporal_norm),
        identity_algorithm_version=ia_ver,
        identity_algorithm_digest=ia_dig,
    )
    if provided_key is not None and provided_key != computed_key:
        raise ReportReviewError(
            "identity_mismatch",
            "claim_identity_key does not match frozen formula",
        )

    locator = data.get("locator")
    if not isinstance(locator, Mapping) or not locator:
        raise ReportReviewError(
            "claim_not_evaluable", "locator must be a non-empty mapping"
        )
    locator = _copy_mapping(locator)
    if locator.get("report_revision_id") not in (None, src["report_revision_id"]):
        raise ReportReviewError(
            "revision_mismatch",
            "claim locator.report_revision_id disagrees with report_source",
        )
    locator.setdefault("report_revision_id", src["report_revision_id"])
    locator.setdefault("report_artifact_id", src["report_artifact_id"])

    evidence_refs = _validate_evidence_refs(
        _normalize_list(data.get("evidence_refs"), field="evidence_refs")
    )
    issue_ids = [
        _require_non_empty_str(x, "issue_ids[]", "identity_mismatch")
        for x in _normalize_list(data.get("issue_ids"), field="issue_ids")
    ]

    return {
        "claim_id": claim_id,
        "claim_identity_key": computed_key,
        "report_lineage_id": src["report_lineage_id"],
        "report_revision_id": src["report_revision_id"],
        "report_source_revision_id": src["report_source_revision_id"],
        "project_id": project_id,
        "run_id": run_id,
        "unit_ids": list(unit_ids),
        "claim_kind": claim_kind,
        "source_text": source_text,
        "normalized_claim_concept": normalized_claim_concept,
        "scope": scope,
        "temporal_window": copy.deepcopy(temporal_window),
        "report_cutoff": report_cutoff,
        "report_cutoff_status": report_cutoff_status,
        "status": status,
        "evidence_refs": evidence_refs,
        "issue_ids": issue_ids,
        "locator": locator,
        "normalized_subject_or_site_scope": subject_scope,
        "normalized_temporal_window": str(temporal_norm),
        "identity_algorithm_version": ia_ver,
        "identity_algorithm_digest": ia_dig,
    }


def build_review_issue(
    spec: Mapping[str, Any],
    report_source: Mapping[str, Any],
    *,
    identity_algorithm_version: str,
    identity_algorithm_digest: str,
) -> dict:
    """Build a deterministic ``ReviewIssue`` bound to ``report_source``."""
    src = _copy_mapping(report_source)
    _assert_report_source_shape(src)
    data = _copy_mapping(spec)

    issue_id = _require_non_empty_str(
        data.get("issue_id"), "issue_id", "issue_identity_invalid"
    )
    project_id = _require_non_empty_str(
        data.get("project_id", src["project_id"]),
        "project_id",
        "issue_identity_invalid",
    )
    if project_id != src["project_id"]:
        raise ReportReviewError(
            "identity_mismatch",
            "issue project_id disagrees with report_source",
        )
    run_id = _require_non_empty_str(
        data.get("run_id"), "run_id", "issue_identity_invalid"
    )
    issue_kind = _require_enum(
        data.get("issue_kind"), "issue_kind", ISSUE_KINDS, "issue_identity_invalid"
    )
    severity = _require_enum(
        data.get("severity"), "severity", ISSUE_SEVERITIES, "issue_identity_invalid"
    )
    lifecycle_state = _require_enum(
        data.get("lifecycle_state"),
        "lifecycle_state",
        ISSUE_LIFECYCLE_STATES,
        "issue_identity_invalid",
    )
    revision_diff_state = _require_enum(
        data.get("revision_diff_state"),
        "revision_diff_state",
        ISSUE_REVISION_DIFF_STATES,
        "issue_identity_invalid",
    )
    clinical_scope = data.get("clinical_or_document_scope")
    if clinical_scope is None or clinical_scope == "":
        raise ReportReviewError(
            "issue_identity_invalid",
            "clinical_or_document_scope must be present",
        )

    claim_ids = [
        _require_non_empty_str(x, "claim_ids[]", "issue_identity_invalid")
        for x in _normalize_list(data.get("claim_ids"), field="claim_ids")
    ]
    unit_ids = [
        _require_non_empty_str(x, "unit_ids[]", "issue_without_unit_or_evidence")
        for x in _normalize_list(data.get("unit_ids"), field="unit_ids")
    ]
    report_scope = data.get("report_scope")
    if not unit_ids and not report_scope:
        raise ReportReviewError(
            "issue_without_unit_or_evidence",
            "ReviewIssue requires unit_ids or report_scope",
        )
    if issue_kind == "omitted" and claim_ids:
        # Omission may have empty claim_ids; non-empty is allowed but unusual —
        # keep as-is (caller may link related claims). No coercion.
        pass

    evidence_refs = _validate_evidence_refs(
        _normalize_list(data.get("evidence_refs"), field="evidence_refs")
    )
    if issue_kind in {"omitted", "not_evaluable"} and not evidence_refs:
        raise ReportReviewError(
            "issue_without_unit_or_evidence",
            f"{issue_kind} issue requires one_or_more evidence_refs",
        )

    source_locators = _normalize_list(
        data.get("source_locators"), field="source_locators"
    )
    related_issue_ids = [
        _require_non_empty_str(x, "related_issue_ids[]", "issue_identity_invalid")
        for x in _normalize_list(
            data.get("related_issue_ids"), field="related_issue_ids"
        )
    ]
    transition_refs = _normalize_list(
        data.get("transition_refs"), field="transition_refs"
    )
    current_note = data.get("current_note", "")
    if not isinstance(current_note, str):
        raise ReportReviewError(
            "issue_identity_invalid", "current_note must be a string"
        )

    concept = _require_non_empty_str(
        data.get(
            "normalized_clinical_concept",
            data.get("normalized_claim_concept"),
        ),
        "normalized_clinical_concept",
        "issue_identity_invalid",
    )
    subject_scope = _require_non_empty_str(
        data.get("normalized_subject_or_site_scope", data.get("scope_detail")),
        "normalized_subject_or_site_scope",
        "issue_identity_invalid",
    )
    temporal = data.get("normalized_temporal_window", data.get("temporal_window", ""))
    if not isinstance(temporal, str) or not temporal:
        temporal = sha256_hex(canonical_bytes(temporal if temporal != "" else clinical_scope))

    ia_ver = _require_non_empty_str(
        identity_algorithm_version,
        "identity_algorithm_version",
        "issue_identity_invalid",
    )
    ia_dig = _require_non_empty_str(
        identity_algorithm_digest,
        "identity_algorithm_digest",
        "issue_identity_invalid",
    )
    computed_key = compute_issue_identity_key(
        project_id=project_id,
        report_lineage_id=src["report_lineage_id"],
        normalized_clinical_concept=concept,
        normalized_subject_or_site_scope=subject_scope,
        normalized_temporal_window=str(temporal),
        identity_algorithm_version=ia_ver,
        identity_algorithm_digest=ia_dig,
    )
    provided_key = data.get("issue_identity_key")
    if provided_key is not None and provided_key != computed_key:
        raise ReportReviewError(
            "issue_identity_invalid",
            "issue_identity_key does not match frozen formula",
        )

    issue = {
        "issue_id": issue_id,
        "issue_identity_key": computed_key,
        "project_id": project_id,
        "run_id": run_id,
        "report_lineage_id": src["report_lineage_id"],
        "report_revision_id": src["report_revision_id"],
        "report_source_revision_id": src["report_source_revision_id"],
        "issue_kind": issue_kind,
        "claim_ids": claim_ids,
        "unit_ids": unit_ids,
        "severity": severity,
        "clinical_or_document_scope": copy.deepcopy(clinical_scope),
        "evidence_refs": evidence_refs,
        "source_locators": copy.deepcopy(source_locators),
        "lifecycle_state": lifecycle_state,
        "revision_diff_state": revision_diff_state,
        "related_issue_ids": related_issue_ids,
        "transition_refs": copy.deepcopy(transition_refs),
        "current_note": current_note,
        "normalized_clinical_concept": concept,
        "normalized_subject_or_site_scope": subject_scope,
        "normalized_temporal_window": str(temporal),
        "identity_algorithm_version": ia_ver,
        "identity_algorithm_digest": ia_dig,
    }
    if report_scope is not None:
        issue["report_scope"] = copy.deepcopy(report_scope)
    return issue


def rebuild_parent_lineage(
    report_revision_id: str,
    revisions: Sequence[Mapping[str, Any]],
) -> Tuple[str, ...]:
    """Return the parent chain from root to ``report_revision_id`` (inclusive).

    Fail-closed on missing parents, cycles, or cross-lineage links.
    """
    indexed = _index_revisions(revisions)
    if report_revision_id not in indexed:
        raise ReportReviewError(
            "source_revision_mismatch",
            f"unknown report_revision_id {report_revision_id!r}",
        )
    chain: list[str] = []
    seen: set[str] = set()
    current: Optional[str] = report_revision_id
    while current is not None:
        if current in seen:
            raise ReportReviewError(
                "source_revision_mismatch",
                f"cycle in parent lineage at {current!r}",
            )
        seen.add(current)
        rev = indexed[current]
        chain.append(current)
        parent = rev.get("parent_report_revision_id")
        if parent is None:
            break
        if parent not in indexed:
            raise ReportReviewError(
                "source_revision_mismatch",
                f"missing parent {parent!r} while rebuilding lineage",
            )
        if indexed[parent]["report_lineage_id"] != rev["report_lineage_id"]:
            raise ReportReviewError(
                "source_revision_mismatch",
                "parent lineage crosses report_lineage_id",
            )
        if indexed[parent]["project_id"] != rev["project_id"]:
            raise ReportReviewError(
                "identity_mismatch",
                "parent lineage crosses project_id",
            )
        current = parent
    chain.reverse()
    return tuple(chain)


def validate_object_cross_identity(
    report_source: Mapping[str, Any],
    units: Sequence[Mapping[str, Any]],
    claims: Sequence[Mapping[str, Any]],
    issues: Sequence[Mapping[str, Any]],
    *,
    run_source_revision_id: Optional[str] = None,
) -> Tuple[str, ...]:
    """Return sorted unique frozen failure codes for object cross-identity.

    Accumulates every blocking reason (not first-error-only). Empty tuple means
    the unit/claim/issue set is cross-identity consistent with ``report_source``.
    """
    codes: list[str] = []

    def add(code: str) -> None:
        codes.append(code)

    try:
        src = _copy_mapping(report_source)
        _assert_report_source_shape(src)
    except ReportReviewError as exc:
        return _stable_unique([exc.failure_code])

    if src.get("immutable") is not True:
        add("source_not_immutable")

    if run_source_revision_id is not None:
        if not isinstance(run_source_revision_id, str) or not run_source_revision_id:
            add("identity_mismatch")
        elif run_source_revision_id == src["report_source_revision_id"]:
            add("identity_mismatch")
        elif run_source_revision_id == src["source_revision_id"]:
            # Same field pair — still a Run/report mix if caller reused the id.
            add("identity_mismatch")

    unit_by_id: dict[str, Mapping[str, Any]] = {}
    for unit in units:
        uid = unit.get("unit_id")
        if not isinstance(uid, str) or not uid:
            add("identity_mismatch")
            continue
        if uid in unit_by_id:
            add("duplicate_unit_entry")
            continue
        unit_by_id[uid] = unit
        if unit.get("report_revision_id") != src["report_revision_id"]:
            add("revision_mismatch")
        locator = unit.get("locator")
        if not isinstance(locator, Mapping) or locator.get("report_artifact_id") != src["report_artifact_id"]:
            add("identity_mismatch")
        parent = unit.get("parent_unit_id")
        ut = unit.get("unit_type")
        if ut == "document":
            if parent is not None:
                add("identity_mismatch")
        elif parent is None:
            add("identity_mismatch")
        elif parent not in unit_by_id and parent not in {
            u.get("unit_id") for u in units
        }:
            add("expected_unit_missing")

    # Second pass: parent resolution after full id set is known.
    unit_ids = set(unit_by_id)
    for unit in unit_by_id.values():
        parent = unit.get("parent_unit_id")
        if parent is not None and parent not in unit_ids:
            add("expected_unit_missing")

    claim_by_id: dict[str, Mapping[str, Any]] = {}
    for claim in claims:
        cid = claim.get("claim_id")
        if not isinstance(cid, str) or not cid:
            add("identity_mismatch")
            continue
        if cid in claim_by_id:
            add("identity_mismatch")
            continue
        claim_by_id[cid] = claim
        if claim.get("project_id") != src["project_id"]:
            add("identity_mismatch")
        if claim.get("report_lineage_id") != src["report_lineage_id"]:
            add("identity_mismatch")
        if claim.get("report_revision_id") != src["report_revision_id"]:
            add("revision_mismatch")
        if claim.get("report_source_revision_id") != src["report_source_revision_id"]:
            add("source_revision_mismatch")
        locator = claim.get("locator")
        if not isinstance(locator, Mapping) or locator.get("report_artifact_id") != src["report_artifact_id"]:
            add("identity_mismatch")
        unit_ids_claim = claim.get("unit_ids") or []
        if not unit_ids_claim:
            add("claim_without_unit")
        for uid in unit_ids_claim:
            if uid not in unit_ids:
                add("unit_claim_link_unknown")
        # Recompute identity key when algorithm fields are present.
        if all(
            claim.get(k)
            for k in (
                "normalized_claim_concept",
                "normalized_subject_or_site_scope",
                "normalized_temporal_window",
                "identity_algorithm_version",
                "identity_algorithm_digest",
                "scope",
            )
        ):
            expected_key = compute_claim_identity_key(
                project_id=src["project_id"],
                report_lineage_id=src["report_lineage_id"],
                scope=str(claim["scope"]),
                normalized_claim_concept=str(claim["normalized_claim_concept"]),
                normalized_subject_or_site_scope=str(
                    claim["normalized_subject_or_site_scope"]
                ),
                normalized_temporal_window=str(
                    claim["normalized_temporal_window"]
                ),
                identity_algorithm_version=str(
                    claim["identity_algorithm_version"]
                ),
                identity_algorithm_digest=str(
                    claim["identity_algorithm_digest"]
                ),
            )
            if claim.get("claim_identity_key") != expected_key:
                add("identity_mismatch")

    issue_by_id: dict[str, Mapping[str, Any]] = {}
    for issue in issues:
        iid = issue.get("issue_id")
        if not isinstance(iid, str) or not iid:
            add("issue_identity_invalid")
            continue
        if iid in issue_by_id:
            add("issue_identity_invalid")
            continue
        issue_by_id[iid] = issue
        if issue.get("project_id") != src["project_id"]:
            add("identity_mismatch")
        if issue.get("report_lineage_id") != src["report_lineage_id"]:
            add("identity_mismatch")
        if issue.get("report_revision_id") != src["report_revision_id"]:
            add("revision_mismatch")
        if issue.get("report_source_revision_id") != src["report_source_revision_id"]:
            add("source_revision_mismatch")
        i_units = issue.get("unit_ids") or []
        report_scope = issue.get("report_scope")
        if not i_units and not report_scope:
            add("issue_without_unit_or_evidence")
        for uid in i_units:
            if uid not in unit_ids:
                add("issue_without_unit_or_evidence")
        for cid in issue.get("claim_ids") or []:
            if cid not in claim_by_id:
                add("unit_claim_link_unknown")
        if issue.get("issue_kind") in {"omitted", "not_evaluable"}:
            if not (issue.get("evidence_refs") or []):
                add("issue_without_unit_or_evidence")
        if all(
            issue.get(k)
            for k in (
                "normalized_clinical_concept",
                "normalized_subject_or_site_scope",
                "normalized_temporal_window",
                "identity_algorithm_version",
                "identity_algorithm_digest",
            )
        ):
            expected_key = compute_issue_identity_key(
                project_id=src["project_id"],
                report_lineage_id=src["report_lineage_id"],
                normalized_clinical_concept=str(
                    issue["normalized_clinical_concept"]
                ),
                normalized_subject_or_site_scope=str(
                    issue["normalized_subject_or_site_scope"]
                ),
                normalized_temporal_window=str(
                    issue["normalized_temporal_window"]
                ),
                identity_algorithm_version=str(
                    issue["identity_algorithm_version"]
                ),
                identity_algorithm_digest=str(
                    issue["identity_algorithm_digest"]
                ),
            )
            if issue.get("issue_identity_key") != expected_key:
                add("issue_identity_invalid")

    # Bidirectional claim.issue_ids references.
    for claim in claim_by_id.values():
        for iid in claim.get("issue_ids") or []:
            if iid not in issue_by_id:
                add("unit_claim_link_unknown")

    return _stable_unique(codes)


def assert_inputs_unmodified(
    before_bytes: bytes, obj: Any, *, label: str = "input"
) -> None:
    """Helper for tests: fail if ``obj`` canonical bytes drifted."""
    after = canonical_bytes(obj)
    if after != before_bytes:
        raise ReportReviewError(
            "identity_mismatch", f"{label} was mutated in place"
        )


# Coverage accounting is kept separate from source/object construction.
from .report_review_coverage import *  # noqa: F401,F403,E402
