"""Workbook physical-integrity manifest reconciliation (C3 P0).

Source-to-profile completeness layer between the listing parse authority's
``WorkbookPhysicalManifest`` (attached to every ``ListingSheetPayload``) and
the admitted C1 structure profile.  It owns three contracts:

* :func:`validate_workbook_manifest_bundle` — strict, fail-closed schema
  validation of the stored manifest bundle.  The bundle pairs every staged
  admission file with the parse authority's manifest for that file:
  ``{"schema_version", "files": [{"source_file", "source_file_sha256",
  "manifest": {...}}]}`.  The per-file ``manifest`` is the parse authority's
  ``WorkbookPhysicalManifest`` payload (``evidence_version``
  ``workbook_physical_evidence_v1``): complete sheet list in workbook order
  with visibility, used range, ``content_kind`` (``empty`` / ``header_only``
  / ``data``), ``emitted`` flag, ``omission_reason``, hidden row/column and
  merged region counts, named-table counts and formula cache state.  Unknown
  fields are rejected so a silently extended manifest can never pass an
  older gate.  The evidence vocabulary mirrors
  ``services/api/app/listing_file_parser.py``; the two must move together.
* :func:`reconcile_source_to_profile` — deterministic reconciliation between
  the manifest (what physically exists in the source) and the admission
  record's profiled tables (what the C1 profile actually explains).  Every
  sheet must either back a profiled table or carry an explicit
  ``omission_reason``.  Data-bearing sheets that disappear without an
  explanation are blocking findings — omissions never auto-pass.
* :func:`enforce_source_to_profile_gate` — the fail-closed gate consumed by
  the mapping bridge.  Mapping (the dual-model entry point) may only run on
  an admission record whose manifest is present, valid, digest-bound to the
  staged files, and fully reconciled with the profile.

Severity policy: structural violations (schema, digest binding, file-set
mismatch, order gaps, contradictory claims) and silent omissions block the
gate.  A visible data sheet excluded with an explicit ``omission_reason`` is
an ``explained_data_exclusion`` finding — it does not block, but it is
carried into the harness input so downstream consumers see the exclusion
instead of silently missing data.  A hidden/veryHidden (or
visibility-unknown) sheet that carries data and is not emitted always
blocks: hidden clinical data must be surfaced into the profile, never
dropped behind a reason string.

This module never parses workbooks, never infers clinical meaning, and
touches no medical-writing route; it only reconciles two already-parsed
payloads.
"""

from __future__ import annotations

import re
from pathlib import PurePosixPath
from typing import Any, Mapping, Optional, Sequence

from ..intelligence.primitives import content_hash

__all__ = [
    "WORKBOOK_MANIFEST_SCHEMA_VERSION",
    "WORKBOOK_PHYSICAL_EVIDENCE_VERSION",
    "SOURCE_PROFILE_RECONCILIATION_SCHEMA_VERSION",
    "SOURCE_PROFILE_GATE_SCHEMA_VERSION",
    "MANIFEST_UNAVAILABLE",
    "WorkbookManifestError",
    "validate_workbook_manifest_bundle",
    "validate_workbook_manifest_file",
    "manifest_bundle_sha256",
    "reconcile_source_to_profile",
    "enforce_source_to_profile_gate",
    "manifest_unavailable_summary",
]


#: Version of the stored bundle wrapper built by the admission pipeline.
WORKBOOK_MANIFEST_SCHEMA_VERSION = "mm-workbook-physical-manifest-v1"
#: Parse-authority evidence contract this module reconciles against.  Must
#: stay aligned with ``WORKBOOK_PHYSICAL_EVIDENCE_VERSION`` in the listing
#: parser; a mismatch fails closed at validation time.
WORKBOOK_PHYSICAL_EVIDENCE_VERSION = "workbook_physical_evidence_v1"
SOURCE_PROFILE_RECONCILIATION_SCHEMA_VERSION = "mm-c3-source-profile-reconciliation-v1"
SOURCE_PROFILE_GATE_SCHEMA_VERSION = "mm-c3-source-profile-gate-v1"

#: Reconciliation status stored in an admission record with no manifest.
MANIFEST_UNAVAILABLE = "manifest_unavailable"

_VISIBILITIES = frozenset({"visible", "hidden", "veryHidden", "unknown"})
_CONTENT_KINDS = frozenset({"empty", "header_only", "data"})
_SHEET_NAME_MAX_LENGTH = 255

# Blocking finding codes — the gate refuses the record when any is present.
BLOCKING_FINDING_CODES = frozenset({
    "manifest_file_unmatched",
    "staged_file_without_manifest",
    "manifest_digest_mismatch",
    "sheet_order_invalid",
    "sheet_count_mismatch",
    "emitted_count_mismatch",
    "duplicate_sheet_name",
    "table_without_manifest_sheet",
    "emitted_sheet_without_table",
    "table_without_emitted_sheet",
    "empty_sheet_matched_to_table",
    "header_only_row_count_conflict",
    "silent_data_omission",
    "hidden_data_not_admitted",
    "unknown_visibility_data_omission",
    "unexplained_sheet_exclusion",
})

# Non-blocking finding codes — recorded and surfaced, never auto-silent.
EXPLAINED_FINDING_CODES = frozenset({
    "explained_data_exclusion",
    "explained_empty_sheet_exclusion",
    "explained_header_only_sheet_exclusion",
    "profiled_header_only_sheet",
    "profiled_hidden_sheet",
    "profiled_unknown_visibility_sheet",
})


class WorkbookManifestError(ValueError):
    """Fail-closed manifest or reconciliation violation.

    ``code`` is a stable machine-readable identifier; ``findings`` carries
    the blocking reconciliation findings when the gate refuses a record.
    """

    def __init__(
        self,
        code: str,
        message: str,
        findings: Optional[list[dict[str, Any]]] = None,
    ) -> None:
        self.code = str(code)
        self.findings = list(findings or [])
        super().__init__(message)


# ---------------------------------------------------------------------------
# Small validation helpers
# ---------------------------------------------------------------------------

def _require_mapping(value: Any, what: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise WorkbookManifestError("manifest_schema_invalid", f"{what} must be a mapping")
    return value


def _require_str(value: Any, what: str) -> str:
    if not isinstance(value, str):
        raise WorkbookManifestError("manifest_schema_invalid", f"{what} must be a string")
    return value


def _require_bool(value: Any, what: str) -> bool:
    if not isinstance(value, bool):
        raise WorkbookManifestError("manifest_schema_invalid", f"{what} must be a boolean")
    return value


def _require_int(value: Any, what: str, *, minimum: int = 0) -> int:
    if not isinstance(value, int) or isinstance(value, bool) or value < minimum:
        raise WorkbookManifestError(
            "manifest_schema_invalid",
            f"{what} must be an integer >= {minimum}",
        )
    return value


def _optional_int(value: Any, what: str, *, minimum: int = 0) -> Optional[int]:
    if value is None:
        return None
    return _require_int(value, what, minimum=minimum)


def _require_sha256(value: Any, what: str) -> str:
    text = _require_str(value, what)
    if not re.match(r"^[0-9a-f]{64}$", text):
        raise WorkbookManifestError(
            "manifest_schema_invalid",
            f"{what} must be a 64-char lowercase hex sha256",
        )
    return text


def _reject_unknown_keys(
    payload: Mapping[str, Any],
    allowed: frozenset[str],
    what: str,
) -> None:
    unknown = sorted(set(payload) - allowed)
    if unknown:
        raise WorkbookManifestError(
            "manifest_schema_invalid",
            f"{what} carries unknown fields {unknown}; the gate only accepts "
            "the parse authority's workbook physical evidence contract",
        )


_SHEET_ALLOWED_KEYS = frozenset({
    "sheet_index",
    "sheet_name",
    "visibility",
    "used_range",
    "used_row_count",
    "used_column_count",
    "content_kind",
    "emitted",
    "omission_reason",
    "hidden_row_count",
    "hidden_column_count",
    "merged_region_count",
    "named_table_count",
    "formula_cell_count",
    "uncached_formula_cell_count",
    "uncached_scan_truncated",
})

_MANIFEST_ALLOWED_KEYS = frozenset({
    "evidence_version",
    "parser_version",
    "source_format",
    "content_sha256",
    "sheet_count",
    "emitted_sheet_count",
    "sheets",
    "evidence_limitations",
})

_FILE_ALLOWED_KEYS = frozenset({
    "source_file",
    "source_file_sha256",
    "manifest",
})

_BUNDLE_ALLOWED_KEYS = frozenset({"schema_version", "files"})


# ---------------------------------------------------------------------------
# Manifest schema validation
# ---------------------------------------------------------------------------

def _validate_sheet_fact(payload: Any) -> dict[str, Any]:
    sheet = _require_mapping(payload, "manifest sheet fact")
    _reject_unknown_keys(sheet, _SHEET_ALLOWED_KEYS, "manifest sheet fact")
    sheet_name = _require_str(sheet.get("sheet_name"), "sheet_name").strip()
    if not sheet_name or len(sheet_name) > _SHEET_NAME_MAX_LENGTH:
        raise WorkbookManifestError(
            "manifest_schema_invalid",
            f"sheet_name must be a non-empty string (<= {_SHEET_NAME_MAX_LENGTH} chars)",
        )
    sheet_index = _require_int(sheet.get("sheet_index"), "sheet_index", minimum=1)
    visibility = _require_str(sheet.get("visibility"), "visibility")
    if visibility not in _VISIBILITIES:
        raise WorkbookManifestError(
            "manifest_schema_invalid",
            f"sheet {sheet_name!r} visibility must be one of "
            f"{sorted(_VISIBILITIES)}; got {visibility!r}",
        )
    content_kind = _require_str(sheet.get("content_kind"), "content_kind")
    if content_kind not in _CONTENT_KINDS:
        raise WorkbookManifestError(
            "manifest_schema_invalid",
            f"sheet {sheet_name!r} content_kind must be one of "
            f"{sorted(_CONTENT_KINDS)}; got {content_kind!r}",
        )
    emitted = _require_bool(sheet.get("emitted"), "emitted")
    omission_reason = sheet.get("omission_reason")
    if omission_reason is not None:
        omission_reason = _require_str(omission_reason, "omission_reason").strip()
    if emitted and omission_reason:
        raise WorkbookManifestError(
            "manifest_schema_invalid",
            f"sheet {sheet_name!r} is emitted but carries an omission_reason",
        )
    if not emitted and not omission_reason:
        raise WorkbookManifestError(
            "manifest_schema_invalid",
            f"sheet {sheet_name!r} is not emitted and must record an "
            "omission_reason",
        )
    uncached = _optional_int(
        sheet.get("uncached_formula_cell_count"),
        "uncached_formula_cell_count",
    )
    formula_total = _require_int(sheet.get("formula_cell_count"), "formula_cell_count")
    if uncached is not None and uncached > formula_total:
        raise WorkbookManifestError(
            "manifest_schema_invalid",
            f"sheet {sheet_name!r} uncached formula count exceeds the total",
        )
    return {
        "sheet_index": sheet_index,
        "sheet_name": sheet_name,
        "visibility": visibility,
        "used_range": (
            None
            if sheet.get("used_range") is None
            else _require_str(sheet.get("used_range"), "used_range")
        ),
        "used_row_count": _optional_int(sheet.get("used_row_count"), "used_row_count"),
        "used_column_count": _optional_int(
            sheet.get("used_column_count"), "used_column_count"
        ),
        "content_kind": content_kind,
        "emitted": emitted,
        "omission_reason": omission_reason or None,
        "hidden_row_count": _require_int(
            sheet.get("hidden_row_count"), "hidden_row_count"
        ),
        "hidden_column_count": _require_int(
            sheet.get("hidden_column_count"), "hidden_column_count"
        ),
        "merged_region_count": _require_int(
            sheet.get("merged_region_count"), "merged_region_count"
        ),
        "named_table_count": _require_int(
            sheet.get("named_table_count"), "named_table_count"
        ),
        "formula_cell_count": formula_total,
        "uncached_formula_cell_count": uncached,
        "uncached_scan_truncated": _require_bool(
            sheet.get("uncached_scan_truncated"), "uncached_scan_truncated"
        ),
    }


def validate_workbook_manifest_file(payload: Any) -> dict[str, Any]:
    """Strictly validate one staged-file manifest entry; fail closed."""

    entry = _require_mapping(payload, "workbook manifest file entry")
    _reject_unknown_keys(entry, _FILE_ALLOWED_KEYS, "workbook manifest file entry")
    source_file = _require_str(entry.get("source_file"), "source_file").strip()
    if not source_file or source_file in {".", ".."} or "\\" in source_file:
        raise WorkbookManifestError(
            "manifest_schema_invalid",
            f"source_file must be a non-empty relative path; got {source_file!r}",
        )
    source_sha = _require_sha256(entry.get("source_file_sha256"), "source_file_sha256")
    manifest = _require_mapping(entry.get("manifest"), "manifest payload")
    _reject_unknown_keys(manifest, _MANIFEST_ALLOWED_KEYS, "manifest payload")
    evidence_version = _require_str(manifest.get("evidence_version"), "evidence_version")
    if evidence_version != WORKBOOK_PHYSICAL_EVIDENCE_VERSION:
        raise WorkbookManifestError(
            "manifest_schema_invalid",
            f"evidence_version must be {WORKBOOK_PHYSICAL_EVIDENCE_VERSION!r}; got "
            f"{evidence_version!r}",
        )
    parser_version = _require_str(manifest.get("parser_version"), "parser_version").strip()
    if not parser_version:
        raise WorkbookManifestError(
            "manifest_schema_invalid",
            "parser_version must be a non-empty string",
        )
    source_format = _require_str(manifest.get("source_format"), "source_format").strip()
    if not source_format:
        raise WorkbookManifestError(
            "manifest_schema_invalid",
            "source_format must be a non-empty string",
        )
    content_sha = _require_sha256(manifest.get("content_sha256"), "content_sha256")
    sheet_count = _require_int(manifest.get("sheet_count"), "sheet_count", minimum=1)
    raw_sheets = manifest.get("sheets")
    if not isinstance(raw_sheets, list) or len(raw_sheets) != sheet_count:
        raise WorkbookManifestError(
            "manifest_schema_invalid",
            "manifest sheets must be a list whose length equals sheet_count",
        )
    sheets = [_validate_sheet_fact(item) for item in raw_sheets]
    names = [sheet["sheet_name"] for sheet in sheets]
    if len(names) != len(set(names)):
        raise WorkbookManifestError(
            "manifest_schema_invalid",
            f"manifest of {source_file!r} has duplicate sheet names",
        )
    emitted_count = sum(1 for sheet in sheets if sheet["emitted"])
    if emitted_count != _require_int(
        manifest.get("emitted_sheet_count"), "emitted_sheet_count"
    ):
        raise WorkbookManifestError(
            "manifest_schema_invalid",
            f"manifest of {source_file!r} emitted_sheet_count does not match "
            "the emitted sheet facts",
        )
    limitations = manifest.get("evidence_limitations")
    if not isinstance(limitations, list) or any(
        not isinstance(item, str) for item in limitations
    ):
        raise WorkbookManifestError(
            "manifest_schema_invalid",
            "evidence_limitations must be a list of strings",
        )
    return {
        "source_file": source_file,
        "source_file_sha256": source_sha,
        "manifest": {
            "evidence_version": evidence_version,
            "parser_version": parser_version,
            "source_format": source_format,
            "content_sha256": content_sha,
            "sheet_count": sheet_count,
            "emitted_sheet_count": emitted_count,
            "sheets": sheets,
            "evidence_limitations": list(limitations),
        },
    }


def validate_workbook_manifest_bundle(payload: Any) -> dict[str, Any]:
    """Validate a manifest bundle; a single file entry is accepted as-is."""

    bundle = _require_mapping(payload, "workbook manifest bundle")
    if "files" not in bundle:
        return {
            "schema_version": WORKBOOK_MANIFEST_SCHEMA_VERSION,
            "files": [validate_workbook_manifest_file(bundle)],
        }
    _reject_unknown_keys(bundle, _BUNDLE_ALLOWED_KEYS, "workbook manifest bundle")
    if bundle.get("schema_version") != WORKBOOK_MANIFEST_SCHEMA_VERSION:
        raise WorkbookManifestError(
            "manifest_schema_invalid",
            "bundle schema_version must be "
            f"{WORKBOOK_MANIFEST_SCHEMA_VERSION!r}; got {bundle.get('schema_version')!r}",
        )
    raw_files = bundle.get("files")
    if not isinstance(raw_files, list) or not raw_files:
        raise WorkbookManifestError(
            "manifest_schema_invalid",
            "bundle files must be a non-empty list",
        )
    return {
        "schema_version": WORKBOOK_MANIFEST_SCHEMA_VERSION,
        "files": [validate_workbook_manifest_file(item) for item in raw_files],
    }


def manifest_bundle_sha256(bundle: Mapping[str, Any]) -> str:
    """Deterministic content hash binding the harness input to the manifest."""

    return content_hash({
        "manifest_schema_version": WORKBOOK_MANIFEST_SCHEMA_VERSION,
        "manifest": bundle,
    })


# ---------------------------------------------------------------------------
# Source-to-profile reconciliation
# ---------------------------------------------------------------------------

def _finding(
    code: str,
    *,
    source_file: str = "",
    sheet_name: str = "",
    table_name: str = "",
    detail: str = "",
) -> dict[str, Any]:
    return {
        "code": code,
        "severity": (
            "blocking" if code in BLOCKING_FINDING_CODES else "explained"
        ),
        "source_file": source_file,
        "sheet_name": sheet_name,
        "table_name": table_name,
        "detail": detail,
    }


def _basenames(path: str) -> str:
    return PurePosixPath(str(path).replace("\\", "/")).name


def _matched_record_file(
    entry: Mapping[str, Any],
    technical_files: Sequence[Mapping[str, Any]],
) -> Optional[dict[str, Any]]:
    source_file = str(entry.get("source_file") or "")
    for item in technical_files:
        if str(item.get("path") or "") == source_file:
            return dict(item)
    basename_matches = [
        dict(item)
        for item in technical_files
        if _basenames(str(item.get("path") or "")) == _basenames(source_file)
    ]
    if len(basename_matches) == 1:
        return basename_matches[0]
    return None


def _tables_for_file(
    source_path: str,
    tables: Sequence[Mapping[str, Any]],
) -> list[Mapping[str, Any]]:
    exact = [
        table
        for table in tables
        if str(table.get("source_file") or "") == source_path
    ]
    if exact:
        return list(exact)
    basename = _basenames(source_path)
    return [
        table
        for table in tables
        if _basenames(str(table.get("source_file") or "")) == basename
    ]


def _table_name(table: Mapping[str, Any]) -> str:
    return str(table.get("name") or table.get("table_name") or "").strip()


def _table_row_count(table: Mapping[str, Any]) -> int:
    raw = table.get("row_count")
    if not isinstance(raw, int) or isinstance(raw, bool) or raw < 0:
        return -1
    return raw


def reconcile_source_to_profile(
    manifest_bundle: Mapping[str, Any],
    *,
    technical_files: Sequence[Mapping[str, Any]],
    tables: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    """Reconcile one validated manifest bundle against the admitted profile.

    Returns a bounded, JSON-ready summary whose ``complete`` flag is the
    fail-closed gate condition: ``complete`` is true only when no blocking
    finding exists.  Structural manifest violations must be caught earlier by
    :func:`validate_workbook_manifest_bundle`.
    """

    findings: list[dict[str, Any]] = []
    file_summaries: list[dict[str, Any]] = []
    matched_files: set[str] = set()

    for entry in manifest_bundle.get("files", []):
        source_file = str(entry.get("source_file") or "")
        manifest = entry.get("manifest") or {}
        record_file = _matched_record_file(entry, technical_files)
        if record_file is None:
            findings.append(_finding(
                "manifest_file_unmatched",
                source_file=source_file,
                detail=(
                    "manifest source_file does not match exactly one staged "
                    "admission file"
                ),
            ))
            continue
        matched_files.add(str(record_file.get("path") or ""))
        if str(record_file.get("sha256") or "") != str(entry.get("source_file_sha256") or ""):
            findings.append(_finding(
                "manifest_digest_mismatch",
                source_file=source_file,
                detail=(
                    "source_file_sha256 does not match the staged file digest"
                ),
            ))
        if str(manifest.get("content_sha256") or "") != str(
            entry.get("source_file_sha256") or ""
        ):
            findings.append(_finding(
                "manifest_digest_mismatch",
                source_file=source_file,
                detail=(
                    "manifest content_sha256 does not bind the staged file bytes"
                ),
            ))
        file_tables = _tables_for_file(str(record_file.get("path") or ""), tables)
        table_names = [_table_name(table) for table in file_tables]
        sheets = list(manifest.get("sheets") or [])
        profiled = 0
        excluded = 0
        explained_exclusions = 0
        hidden_profiled = 0
        for position, sheet in enumerate(sheets, start=1):
            sheet_name = str(sheet.get("sheet_name") or "")
            visibility = str(sheet.get("visibility") or "unknown")
            content_kind = str(sheet.get("content_kind") or "")
            emitted = bool(sheet.get("emitted"))
            omission_reason = str(sheet.get("omission_reason") or "")
            if int(sheet.get("sheet_index", -1)) != position:
                findings.append(_finding(
                    "sheet_order_invalid",
                    source_file=source_file,
                    sheet_name=sheet_name,
                    detail=(
                        f"sheet_index {sheet.get('sheet_index')!r} does not "
                        f"match the manifest position {position}"
                    ),
                ))
            matched_tables = [
                table for table in file_tables
                if _table_name(table) == sheet_name
            ]
            has_data = content_kind == "data"
            if matched_tables:
                profiled += 1
                if visibility in {"hidden", "veryHidden"}:
                    hidden_profiled += 1
                    findings.append(_finding(
                        "profiled_hidden_sheet",
                        source_file=source_file,
                        sheet_name=sheet_name,
                        detail=f"sheet profiled with visibility {visibility!r}",
                    ))
                elif visibility == "unknown":
                    findings.append(_finding(
                        "profiled_unknown_visibility_sheet",
                        source_file=source_file,
                        sheet_name=sheet_name,
                        detail="sheet profiled with unresolved visibility",
                    ))
                if not emitted:
                    findings.append(_finding(
                        "emitted_sheet_without_table",
                        source_file=source_file,
                        sheet_name=sheet_name,
                        detail=(
                            "manifest marks the sheet not emitted but the "
                            "profile carries a table with the same name"
                        ),
                    ))
                if content_kind == "empty":
                    findings.append(_finding(
                        "empty_sheet_matched_to_table",
                        source_file=source_file,
                        sheet_name=sheet_name,
                        detail="an empty sheet cannot back a profiled table",
                    ))
                elif content_kind == "header_only":
                    row_counts = {
                        _table_row_count(table) for table in matched_tables
                    }
                    if row_counts != {0}:
                        findings.append(_finding(
                            "header_only_row_count_conflict",
                            source_file=source_file,
                            sheet_name=sheet_name,
                            detail=(
                                "header-only sheet is profiled with row "
                                f"counts {sorted(row_counts)}"
                            ),
                        ))
                    else:
                        findings.append(_finding(
                            "profiled_header_only_sheet",
                            source_file=source_file,
                            sheet_name=sheet_name,
                            detail=(
                                "header-only sheet admitted as evidence table"
                            ),
                        ))
                continue
            # No table with this sheet name: the sheet must be explained.
            if emitted:
                findings.append(_finding(
                    "emitted_sheet_without_table",
                    source_file=source_file,
                    sheet_name=sheet_name,
                    detail=(
                        "manifest claims the sheet was emitted but the "
                        "profiled tables do not contain it"
                    ),
                ))
                continue
            excluded += 1
            if has_data and visibility in {"hidden", "veryHidden"}:
                findings.append(_finding(
                    "hidden_data_not_admitted",
                    source_file=source_file,
                    sheet_name=sheet_name,
                    detail=(
                        f"{visibility} sheet carries data but is not emitted; "
                        f"omission_reason={omission_reason!r}"
                    ),
                ))
                continue
            if has_data and visibility == "unknown":
                findings.append(_finding(
                    "unknown_visibility_data_omission",
                    source_file=source_file,
                    sheet_name=sheet_name,
                    detail=(
                        "sheet carries data with unresolved visibility and is "
                        f"not emitted; omission_reason={omission_reason!r}"
                    ),
                ))
                continue
            if has_data:
                if not omission_reason:
                    findings.append(_finding(
                        "silent_data_omission",
                        source_file=source_file,
                        sheet_name=sheet_name,
                        detail=(
                            "data sheet missing from the profile without an "
                            "omission_reason"
                        ),
                    ))
                    continue
                explained_exclusions += 1
                findings.append(_finding(
                    "explained_data_exclusion",
                    source_file=source_file,
                    sheet_name=sheet_name,
                    detail=f"omission_reason={omission_reason!r}",
                ))
                continue
            if not omission_reason:
                findings.append(_finding(
                    "unexplained_sheet_exclusion",
                    source_file=source_file,
                    sheet_name=sheet_name,
                    detail="sheet excluded without an omission_reason",
                ))
                continue
            findings.append(_finding(
                "explained_header_only_sheet_exclusion"
                if content_kind == "header_only"
                else "explained_empty_sheet_exclusion",
                source_file=source_file,
                sheet_name=sheet_name,
                detail=f"omission_reason={omission_reason!r}",
            ))
        emitted_names = {
            str(sheet.get("sheet_name") or "")
            for sheet in sheets
            if sheet.get("emitted")
        }
        for table_name in table_names:
            if table_name not in emitted_names:
                findings.append(_finding(
                    "table_without_emitted_sheet",
                    source_file=source_file,
                    table_name=table_name,
                    detail="profiled table has no emitted manifest sheet backing",
                ))
        file_summaries.append({
            "source_file": source_file,
            "source_file_sha256": str(entry.get("source_file_sha256") or ""),
            "sheet_count": int(manifest.get("sheet_count") or 0),
            "profiled_sheets": profiled,
            "excluded_sheets": excluded,
            "explained_data_exclusions": explained_exclusions,
            "profiled_hidden_sheets": hidden_profiled,
            "unmatched_table_count": len(table_names) - profiled,
        })

    for item in technical_files:
        path = str(item.get("path") or "")
        if path not in matched_files:
            findings.append(_finding(
                "staged_file_without_manifest",
                source_file=path,
                detail="staged admission file has no manifest entry",
            ))

    blocking = [item for item in findings if item["severity"] == "blocking"]
    explained = [item for item in findings if item["severity"] == "explained"]
    if blocking:
        status = "blocking"
    elif any(
        item["code"] == "explained_data_exclusion" for item in explained
    ):
        status = "explained_exclusions"
    else:
        status = "complete"
    return {
        "schema_version": SOURCE_PROFILE_RECONCILIATION_SCHEMA_VERSION,
        "manifest_schema_version": WORKBOOK_MANIFEST_SCHEMA_VERSION,
        "status": status,
        "complete": not blocking,
        "manifest_sha256": manifest_bundle_sha256(manifest_bundle),
        "files": file_summaries,
        "blocking_finding_codes": sorted({
            item["code"] for item in blocking
        }),
        "findings": findings,
    }


def manifest_unavailable_summary() -> dict[str, Any]:
    """Reconciliation summary stored when no manifest is available.

    The record stays admissible for human preview, and the gate treats the
    missing manifest as a hard failure so mapping never runs unexplained.
    """

    return {
        "schema_version": SOURCE_PROFILE_RECONCILIATION_SCHEMA_VERSION,
        "manifest_schema_version": WORKBOOK_MANIFEST_SCHEMA_VERSION,
        "status": MANIFEST_UNAVAILABLE,
        "complete": False,
        "manifest_sha256": None,
        "files": [],
        "blocking_finding_codes": [],
        "findings": [],
    }


# ---------------------------------------------------------------------------
# Fail-closed gate
# ---------------------------------------------------------------------------

def enforce_source_to_profile_gate(record: Mapping[str, Any]) -> dict[str, Any]:
    """Fail-closed source-to-profile gate for one admission record.

    Returns the recomputed reconciliation summary when the record may reach
    the dual-model mapping bridge.  Raises :class:`WorkbookManifestError`
    when the manifest is missing, no longer schema-valid, no longer matches
    the staged files, or carries any blocking finding.  The reconciliation is
    always recomputed from the stored manifest and record tables, and the
    reconciliation summary persisted at admission time must still describe
    the same manifest digest — a mutated record fails closed.
    """

    technical = record.get("technical_details")
    if not isinstance(technical, Mapping):
        raise WorkbookManifestError(
            "mapping_source_manifest_missing",
            "admission record has no technical_details",
        )
    stored_summary = technical.get("source_profile_reconciliation")
    if stored_summary is None or not isinstance(stored_summary, Mapping):
        raise WorkbookManifestError(
            "mapping_source_manifest_missing",
            "admission record carries no source-profile reconciliation",
        )
    manifest_bundle = technical.get("physical_manifest")
    if manifest_bundle is None:
        raise WorkbookManifestError(
            "mapping_source_manifest_missing",
            "admission record carries no physical workbook manifest; mapping "
            "refuses to run on an unexplained input",
        )
    try:
        bundle = validate_workbook_manifest_bundle(manifest_bundle)
    except WorkbookManifestError as exc:
        raise WorkbookManifestError(
            "mapping_source_manifest_invalid",
            f"stored physical manifest failed schema validation: {exc}",
        ) from exc
    technical_files = technical.get("files")
    if not isinstance(technical_files, list):
        raise WorkbookManifestError(
            "mapping_source_manifest_invalid",
            "admission record technical_details.files is malformed",
        )
    tables = record.get("tables")
    if not isinstance(tables, list):
        raise WorkbookManifestError(
            "mapping_source_manifest_invalid",
            "admission record tables are malformed",
        )
    reconciliation = reconcile_source_to_profile(
        bundle,
        technical_files=[item for item in technical_files if isinstance(item, Mapping)],
        tables=[table for table in tables if isinstance(table, Mapping)],
    )
    stored_digest = stored_summary.get("manifest_sha256")
    if stored_digest is not None and stored_digest != reconciliation["manifest_sha256"]:
        raise WorkbookManifestError(
            "mapping_source_manifest_invalid",
            "stored reconciliation digest does not match the stored manifest; "
            "the admission record was mutated after admission",
        )
    if not reconciliation["complete"]:
        raise WorkbookManifestError(
            "mapping_source_incomplete",
            "source-to-profile reconciliation found blocking findings: "
            f"{reconciliation['blocking_finding_codes']}",
            findings=reconciliation["findings"],
        )
    return reconciliation
