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
