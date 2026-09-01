"""Read-only freshness revalidation for the MY009 source-token evidence seam.

The existing MY009 content scan intentionally concluded ``not_proven``: it did
not find the legacy token in its bounded candidate scan, but that absence is not
proof that the token never existed.  This module only reopens the persisted scan
artifact plus its source/archive inventory inputs, verifies bytes/SHA-256 and
recomputes the inventory-derived counts.  It never rescans or mutates the real
project and never synthesizes a token or grants B6/CAS/medical authority.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
import hashlib
import json
from pathlib import Path
import re
from typing import Any, Mapping


SOURCE_TOKEN_CONTENT_ARTIFACT_SCHEMA_VERSION = (
    "medical_monitoring_my009_source_token_content_revalidation_v1"
)
SOURCE_TOKEN_EVIDENCE_REVALIDATION_SCHEMA_VERSION = (
    "medical_monitoring_my009_source_token_evidence_revalidation_v1"
)
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
_ARTIFACT_KEYS = {
    "schema_version",
    "read_only",
    "legacy_source_token",
    "source_inventory_path",
    "source_inventory_sha256",
    "archive_inventory_path",
    "archive_inventory_sha256",
    "candidate_count",
    "candidate_extension_counts",
    "content_scan",
    "listing_shape_observation",
    "archive_observation",
    "source_token_revalidation_status",
    "source_token_synthesized",
    "write_permitted",
    "migration_ready",
    "conclusion",
}
_SOURCE_INVENTORY_KEYS = {
    "schema_version",
    "search_roots",
    "file_count",
    "listing_identity_candidates",
    "rows",
    "conclusion",
}
_ARCHIVE_INVENTORY_KEYS = {"schema_version", "mode", "archives", "conclusion"}


class MonitoringSourceTokenEvidenceRevalidationError(ValueError):
    """Raised when the source-token evidence cannot be evaluated safely."""


class MonitoringSourceTokenEvidenceRevalidationIssueCode(str, Enum):
    PAYLOAD_SHAPE_INVALID = "payload_shape_invalid"
    ARTIFACT_SCHEMA_INVALID = "artifact_schema_invalid"
    ARTIFACT_FIELD_INVALID = "artifact_field_invalid"
    AUTHORITY_FLAG_MISSING = "authority_flag_missing"
    AUTHORITY_FLAG_TRUE = "authority_flag_true"
    SOURCE_INVENTORY_INVALID = "source_inventory_invalid"
    SOURCE_INVENTORY_COUNT_MISMATCH = "source_inventory_count_mismatch"
    SOURCE_INVENTORY_CANDIDATE_MISMATCH = "source_inventory_candidate_mismatch"
    ARCHIVE_INVENTORY_INVALID = "archive_inventory_invalid"
    ARCHIVE_INVENTORY_COUNT_MISMATCH = "archive_inventory_count_mismatch"
    CONTENT_SUMMARY_MISMATCH = "content_summary_mismatch"
    CONTENT_SCAN_INVALID = "content_scan_invalid"
    LISTING_OBSERVATION_INVALID = "listing_observation_invalid"
    ARCHIVE_OBSERVATION_INVALID = "archive_observation_invalid"
    FILE_PATH_UNSAFE = "file_path_unsafe"
    FILE_MISSING = "file_missing"
    FILE_NOT_REGULAR = "file_not_regular"
    FILE_SYMLINK_UNSUPPORTED = "file_symlink_unsupported"
    FILE_BYTES_MISMATCH = "file_bytes_mismatch"
    FILE_SHA256_MISMATCH = "file_sha256_mismatch"
    FILE_JSON_INVALID = "file_json_invalid"


def _text(value: Any) -> str:
    return str(value or "").strip()


def _canonical(value: Any) -> str:
    try:
        return json.dumps(
            value, ensure_ascii=False, sort_keys=True, separators=(",", ":")
        )
    except (TypeError, ValueError) as exc:
        raise MonitoringSourceTokenEvidenceRevalidationError(
            "source-token evidence must be JSON-serializable"
        ) from exc


def _digest(value: Any) -> str:
    return hashlib.sha256(_canonical(value).encode("utf-8")).hexdigest()


def _valid_sha(value: Any) -> bool:
    return isinstance(value, str) and bool(_SHA256_RE.fullmatch(value))


def _non_negative_int(value: Any) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and value >= 0


@dataclass(frozen=True)
class MonitoringSourceTokenEvidenceRevalidationIssue:
    code: MonitoringSourceTokenEvidenceRevalidationIssueCode
    subject: str
    detail: str

    def __post_init__(self) -> None:
        subject = _text(self.subject)
        detail = _text(self.detail)
        if not subject or not detail:
            raise MonitoringSourceTokenEvidenceRevalidationError(
                "revalidation issue subject and detail are required"
            )
        object.__setattr__(self, "subject", subject)
        object.__setattr__(self, "detail", detail)

    def to_dict(self) -> dict[str, str]:
        return {"code": self.code.value, "subject": self.subject, "detail": self.detail}


@dataclass(frozen=True)
class MonitoringSourceTokenEvidenceRevalidationReport:
    """Freshness result with source-token status and every authority false."""

    status: str
    evidence_fresh: bool
    artifact_payload_valid: bool
    source_inventory_payload_valid: bool
    archive_inventory_payload_valid: bool
    content_summary_matches: bool
    artifact_file_checked: bool
    artifact_file_fresh: bool
    source_inventory_file_checked: bool
    source_inventory_file_fresh: bool
    archive_inventory_file_checked: bool
    archive_inventory_file_fresh: bool
    source_token_revalidation_status: str
    candidate_count: int
    archive_count: int
    member_count: int
    listing_like_member_count: int
    issue_count: int
    artifact_ref: str = ""
    source_inventory_path: str = ""
    archive_inventory_path: str = ""
    issues: tuple[MonitoringSourceTokenEvidenceRevalidationIssue, ...] = ()
    schema_version: str = SOURCE_TOKEN_EVIDENCE_REVALIDATION_SCHEMA_VERSION
    read_only: bool = True
    source_token_synthesized: bool = False
    write_permitted: bool = False
    migration_ready: bool = False
    authority_granted: bool = False
    release_ready: bool = False
    provider_permitted: bool = False
    runtime_write_permitted: bool = False
    medical_authority_granted: bool = False
    report_sha256: str = field(init=False)

    def __post_init__(self) -> None:
        if self.schema_version != SOURCE_TOKEN_EVIDENCE_REVALIDATION_SCHEMA_VERSION:
            raise MonitoringSourceTokenEvidenceRevalidationError(
                "unsupported source-token evidence revalidation schema"
            )
        if self.status not in {"fresh", "blocked"}:
            raise MonitoringSourceTokenEvidenceRevalidationError(
                "invalid revalidation status"
            )
        for name in ("read_only",):
            if getattr(self, name) is not True:
                raise MonitoringSourceTokenEvidenceRevalidationError(
                    f"{name} must remain true"
                )
        for name in (
            "source_token_synthesized",
            "write_permitted",
            "migration_ready",
            "authority_granted",
            "release_ready",
            "provider_permitted",
            "runtime_write_permitted",
            "medical_authority_granted",
        ):
            if getattr(self, name) is not False:
                raise MonitoringSourceTokenEvidenceRevalidationError(
                    f"{name} must remain false"
                )
        for name in (
            "evidence_fresh",
            "artifact_payload_valid",
            "source_inventory_payload_valid",
            "archive_inventory_payload_valid",
            "content_summary_matches",
            "artifact_file_checked",
            "artifact_file_fresh",
            "source_inventory_file_checked",
            "source_inventory_file_fresh",
            "archive_inventory_file_checked",
            "archive_inventory_file_fresh",
        ):
            if not isinstance(getattr(self, name), bool):
                raise MonitoringSourceTokenEvidenceRevalidationError(
                    f"{name} must be boolean"
                )
        for name in (
            "candidate_count",
            "archive_count",
            "member_count",
            "listing_like_member_count",
            "issue_count",
        ):
            if not _non_negative_int(getattr(self, name)):
                raise MonitoringSourceTokenEvidenceRevalidationError(
                    f"{name} must be a non-negative integer"
                )
        if self.issue_count != len(self.issues):
            raise MonitoringSourceTokenEvidenceRevalidationError(
                "issue_count must equal the number of issues"
            )
        if self.artifact_file_fresh and not self.artifact_file_checked:
            raise MonitoringSourceTokenEvidenceRevalidationError(
                "artifact_file_fresh requires artifact_file_checked"
            )
        if self.source_inventory_file_fresh and not self.source_inventory_file_checked:
            raise MonitoringSourceTokenEvidenceRevalidationError(
                "source_inventory_file_fresh requires source_inventory_file_checked"
            )
        if (
            self.archive_inventory_file_fresh
            and not self.archive_inventory_file_checked
        ):
            raise MonitoringSourceTokenEvidenceRevalidationError(
                "archive_inventory_file_fresh requires archive_inventory_file_checked"
            )
        if self.source_token_revalidation_status not in {"not_proven", "unknown"}:
            raise MonitoringSourceTokenEvidenceRevalidationError(
                "source_token_revalidation_status must remain not_proven or unknown"
            )
        issues = tuple(self.issues)
        if any(
            not isinstance(item, MonitoringSourceTokenEvidenceRevalidationIssue)
            for item in issues
        ):
            raise MonitoringSourceTokenEvidenceRevalidationError(
                "issues contain an invalid value"
            )
        expected_fresh = (
            not issues
            and self.artifact_payload_valid
            and self.source_inventory_payload_valid
            and self.archive_inventory_payload_valid
            and self.content_summary_matches
            and (not self.artifact_file_checked or self.artifact_file_fresh)
            and (
                not self.source_inventory_file_checked
                or self.source_inventory_file_fresh
            )
            and (
                not self.archive_inventory_file_checked
                or self.archive_inventory_file_fresh
            )
        )
        if (
            self.evidence_fresh != expected_fresh
            or (self.status == "fresh") != expected_fresh
        ):
            raise MonitoringSourceTokenEvidenceRevalidationError(
                "revalidation status does not match evidence state"
            )
        object.__setattr__(self, "artifact_ref", _text(self.artifact_ref))
        object.__setattr__(
            self, "source_inventory_path", _text(self.source_inventory_path)
        )
        object.__setattr__(
            self, "archive_inventory_path", _text(self.archive_inventory_path)
        )
        object.__setattr__(self, "issues", issues)
        object.__setattr__(self, "report_sha256", _digest(self._payload()))

    def _payload(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "status": self.status,
            "evidence_fresh": self.evidence_fresh,
            "artifact_payload_valid": self.artifact_payload_valid,
            "source_inventory_payload_valid": self.source_inventory_payload_valid,
            "archive_inventory_payload_valid": self.archive_inventory_payload_valid,
            "content_summary_matches": self.content_summary_matches,
            "artifact_file_checked": self.artifact_file_checked,
            "artifact_file_fresh": self.artifact_file_fresh,
            "source_inventory_file_checked": self.source_inventory_file_checked,
            "source_inventory_file_fresh": self.source_inventory_file_fresh,
            "archive_inventory_file_checked": self.archive_inventory_file_checked,
            "archive_inventory_file_fresh": self.archive_inventory_file_fresh,
            "source_token_revalidation_status": self.source_token_revalidation_status,
            "candidate_count": self.candidate_count,
            "archive_count": self.archive_count,
            "member_count": self.member_count,
            "listing_like_member_count": self.listing_like_member_count,
            "issue_count": self.issue_count,
            "artifact_ref": self.artifact_ref,
            "source_inventory_path": self.source_inventory_path,
            "archive_inventory_path": self.archive_inventory_path,
            "issues": [item.to_dict() for item in self.issues],
            "read_only": self.read_only,
            "source_token_synthesized": self.source_token_synthesized,
            "write_permitted": self.write_permitted,
            "migration_ready": self.migration_ready,
            "authority_granted": self.authority_granted,
            "release_ready": self.release_ready,
            "provider_permitted": self.provider_permitted,
            "runtime_write_permitted": self.runtime_write_permitted,
            "medical_authority_granted": self.medical_authority_granted,
        }

    def to_dict(self) -> dict[str, Any]:
        return {**self._payload(), "report_sha256": self.report_sha256}


def _issue(
    issues: list[MonitoringSourceTokenEvidenceRevalidationIssue],
    code: MonitoringSourceTokenEvidenceRevalidationIssueCode,
    subject: str,
    detail: str,
) -> None:
    issues.append(
        MonitoringSourceTokenEvidenceRevalidationIssue(
            code=code,
            subject=_text(subject) or "payload",
            detail=_text(detail) or "invalid evidence",
        )
    )


def _safe_relative_path(
    raw_path: Any,
    *,
    workspace_root: Path,
    issues: list[MonitoringSourceTokenEvidenceRevalidationIssue],
    subject: str,
) -> Path | None:
    text = raw_path.strip() if isinstance(raw_path, str) else ""
    path = Path(text) if text else Path(".")
    if (
        not text
        or path.is_absolute()
        or "\\" in text
        or any(part in {"", ".", ".."} for part in path.parts)
    ):
        _issue(
            issues,
            MonitoringSourceTokenEvidenceRevalidationIssueCode.FILE_PATH_UNSAFE,
            subject,
            "path must be a clean workspace-relative POSIX path",
        )
        return None
    current = workspace_root
    for part in path.parts:
        current = current / part
        if current.is_symlink():
            _issue(
                issues,
                MonitoringSourceTokenEvidenceRevalidationIssueCode.FILE_SYMLINK_UNSUPPORTED,
                subject,
                "path and parent components must not be symlinks",
            )
            return None
    try:
        candidate = workspace_root / path
        candidate.resolve(strict=False).relative_to(workspace_root.resolve())
    except (OSError, ValueError) as exc:
        _issue(
            issues,
            MonitoringSourceTokenEvidenceRevalidationIssueCode.FILE_PATH_UNSAFE,
            subject,
            f"path escapes workspace root: {exc}",
        )
        return None
    return candidate


def _blocked_report(
    issues: list[MonitoringSourceTokenEvidenceRevalidationIssue],
    *,
    artifact_ref: str = "",
    source_inventory_path: str = "",
    archive_inventory_path: str = "",
    artifact_payload_valid: bool = False,
    source_inventory_payload_valid: bool = False,
    archive_inventory_payload_valid: bool = False,
    content_summary_matches: bool = False,
    artifact_file_checked: bool = False,
    artifact_file_fresh: bool = False,
    source_inventory_file_checked: bool = False,
    source_inventory_file_fresh: bool = False,
    archive_inventory_file_checked: bool = False,
    archive_inventory_file_fresh: bool = False,
    source_token_revalidation_status: str = "unknown",
    candidate_count: int = 0,
    archive_count: int = 0,
    member_count: int = 0,
    listing_like_member_count: int = 0,
) -> MonitoringSourceTokenEvidenceRevalidationReport:
    return MonitoringSourceTokenEvidenceRevalidationReport(
        status="blocked",
        evidence_fresh=False,
        artifact_payload_valid=artifact_payload_valid,
        source_inventory_payload_valid=source_inventory_payload_valid,
        archive_inventory_payload_valid=archive_inventory_payload_valid,
        content_summary_matches=content_summary_matches,
        artifact_file_checked=artifact_file_checked,
        artifact_file_fresh=artifact_file_fresh,
        source_inventory_file_checked=source_inventory_file_checked,
        source_inventory_file_fresh=source_inventory_file_fresh,
        archive_inventory_file_checked=archive_inventory_file_checked,
        archive_inventory_file_fresh=archive_inventory_file_fresh,
        source_token_revalidation_status=source_token_revalidation_status,
        candidate_count=candidate_count,
        archive_count=archive_count,
        member_count=member_count,
        listing_like_member_count=listing_like_member_count,
        issue_count=len(issues),
        artifact_ref=artifact_ref,
        source_inventory_path=source_inventory_path,
        archive_inventory_path=archive_inventory_path,
        issues=tuple(issues),
    )


def _check_authority(
    payload: Mapping[str, Any],
    issues: list[MonitoringSourceTokenEvidenceRevalidationIssue],
) -> bool:
    expectations = {
        "read_only": True,
        "source_token_synthesized": False,
        "write_permitted": False,
        "migration_ready": False,
    }
    ok = True
    for name, expected in expectations.items():
        if name not in payload:
            ok = False
            _issue(
                issues,
                MonitoringSourceTokenEvidenceRevalidationIssueCode.AUTHORITY_FLAG_MISSING,
                name,
                "required read-only boundary flag is missing",
            )
        elif payload[name] is not expected:
            ok = False
            _issue(
                issues,
                MonitoringSourceTokenEvidenceRevalidationIssueCode.AUTHORITY_FLAG_TRUE,
                name,
                f"expected {expected!r}, observed {payload[name]!r}",
            )
    return ok


def _extension_counts(rows: list[Mapping[str, Any]]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for row in rows:
        if _text(row.get("exclusion")):
            continue
        extension = _text(row.get("extension"))
        counts[extension] = counts.get(extension, 0) + 1
    return dict(sorted(counts.items()))


def _inventory_summary(
    source: Mapping[str, Any],
    archive: Mapping[str, Any],
    artifact: Mapping[str, Any],
    issues: list[MonitoringSourceTokenEvidenceRevalidationIssue],
) -> tuple[bool, bool, dict[str, int]]:
    source_valid = True
    archive_valid = True
    source_unknown = sorted(set(source) - _SOURCE_INVENTORY_KEYS)
    if source_unknown:
        source_valid = False
        _issue(
            issues,
            MonitoringSourceTokenEvidenceRevalidationIssueCode.SOURCE_INVENTORY_INVALID,
            "source_inventory",
            f"unsupported fields: {source_unknown}",
        )
    if (
        source.get("schema_version")
        != "medical_monitoring_my009_source_inventory_recheck_v1"
    ):
        source_valid = False
        _issue(
            issues,
            MonitoringSourceTokenEvidenceRevalidationIssueCode.SOURCE_INVENTORY_INVALID,
            "source_inventory.schema_version",
            "unexpected inventory schema",
        )
    rows = source.get("rows")
    candidates = source.get("listing_identity_candidates")
    if not isinstance(rows, list) or not isinstance(candidates, list):
        source_valid = False
        _issue(
            issues,
            MonitoringSourceTokenEvidenceRevalidationIssueCode.SOURCE_INVENTORY_INVALID,
            "source_inventory.rows",
            "rows and listing_identity_candidates must be arrays",
        )
        rows = rows if isinstance(rows, list) else []
        candidates = candidates if isinstance(candidates, list) else []
    if source.get("file_count") != len(rows):
        source_valid = False
        _issue(
            issues,
            MonitoringSourceTokenEvidenceRevalidationIssueCode.SOURCE_INVENTORY_COUNT_MISMATCH,
            "source_inventory.file_count",
            f"declared={source.get('file_count')!r}, observed={len(rows)}",
        )
    candidate_rows = [
        row
        for row in rows
        if isinstance(row, Mapping) and not _text(row.get("exclusion"))
    ]
    candidate_paths = sorted(_text(row.get("path")) for row in candidate_rows)
    candidate_list = sorted(_text(value) for value in candidates)
    if candidate_paths != candidate_list:
        source_valid = False
        _issue(
            issues,
            MonitoringSourceTokenEvidenceRevalidationIssueCode.SOURCE_INVENTORY_CANDIDATE_MISMATCH,
            "source_inventory.listing_identity_candidates",
            "candidate paths differ from non-excluded inventory rows",
        )
    archive_unknown = sorted(set(archive) - _ARCHIVE_INVENTORY_KEYS)
    if archive_unknown:
        archive_valid = False
        _issue(
            issues,
            MonitoringSourceTokenEvidenceRevalidationIssueCode.ARCHIVE_INVENTORY_INVALID,
            "archive_inventory",
            f"unsupported fields: {archive_unknown}",
        )
    if (
        archive.get("schema_version")
        != "medical_monitoring_my009_archive_member_inventory_v1"
    ):
        archive_valid = False
        _issue(
            issues,
            MonitoringSourceTokenEvidenceRevalidationIssueCode.ARCHIVE_INVENTORY_INVALID,
            "archive_inventory.schema_version",
            "unexpected archive inventory schema",
        )
    archives = archive.get("archives")
    if not isinstance(archives, list):
        archive_valid = False
        _issue(
            issues,
            MonitoringSourceTokenEvidenceRevalidationIssueCode.ARCHIVE_INVENTORY_INVALID,
            "archive_inventory.archives",
            "archives must be an array",
        )
        archives = []
    member_count = 0
    listing_like_count = 0
    for index, item in enumerate(archives):
        if not isinstance(item, Mapping) or not isinstance(item.get("members"), list):
            archive_valid = False
            _issue(
                issues,
                MonitoringSourceTokenEvidenceRevalidationIssueCode.ARCHIVE_INVENTORY_INVALID,
                f"archive_inventory.archives[{index}]",
                "archive item and members must be objects/arrays",
            )
            continue
        if item.get("member_count") != len(item["members"]):
            archive_valid = False
            _issue(
                issues,
                MonitoringSourceTokenEvidenceRevalidationIssueCode.ARCHIVE_INVENTORY_COUNT_MISMATCH,
                f"archive_inventory.archives[{index}].member_count",
                f"declared={item.get('member_count')!r}, observed={len(item['members'])}",
            )
        member_count += len(item["members"])
        listing_like_count += sum(
            1
            for member in item["members"]
            if isinstance(member, Mapping) and member.get("listing_candidate") is True
        )
    expected_extensions = _extension_counts(candidate_rows)
    if (
        artifact.get("candidate_count") != len(candidate_rows)
        or artifact.get("candidate_extension_counts") != expected_extensions
    ):
        _issue(
            issues,
            MonitoringSourceTokenEvidenceRevalidationIssueCode.CONTENT_SUMMARY_MISMATCH,
            "candidate_summary",
            f"expected count/extensions={len(candidate_rows)!r}/{expected_extensions!r}, observed={artifact.get('candidate_count')!r}/{artifact.get('candidate_extension_counts')!r}",
        )
    archive_obs = artifact.get("archive_observation")
    if not isinstance(archive_obs, Mapping):
        _issue(
            issues,
            MonitoringSourceTokenEvidenceRevalidationIssueCode.ARCHIVE_OBSERVATION_INVALID,
            "archive_observation",
            "archive_observation must be an object",
        )
    else:
        expected_archive = {
            "archive_count": len(archives),
            "member_count": member_count,
            "listing_like_member_count": listing_like_count,
        }
        for name, expected in expected_archive.items():
            if archive_obs.get(name) != expected:
                _issue(
                    issues,
                    MonitoringSourceTokenEvidenceRevalidationIssueCode.CONTENT_SUMMARY_MISMATCH,
                    f"archive_observation.{name}",
                    f"expected={expected}, observed={archive_obs.get(name)!r}",
                )
    listing_obs = artifact.get("listing_shape_observation")
    if not isinstance(listing_obs, Mapping):
        _issue(
            issues,
            MonitoringSourceTokenEvidenceRevalidationIssueCode.LISTING_OBSERVATION_INVALID,
            "listing_shape_observation",
            "listing_shape_observation must be an object",
        )
    elif _text(listing_obs.get("path")) not in candidate_paths:
        _issue(
            issues,
            MonitoringSourceTokenEvidenceRevalidationIssueCode.LISTING_OBSERVATION_INVALID,
            "listing_shape_observation.path",
            "listing path is not one of the current candidate rows",
        )
    return (
        source_valid,
        archive_valid,
        {
            "candidate_count": len(candidate_rows),
            "archive_count": len(archives),
            "member_count": member_count,
            "listing_like_member_count": listing_like_count,
        },
    )


def revalidate_source_token_payload(
    payload: Mapping[str, Any],
    *,
    source_inventory: Mapping[str, Any] | None,
    archive_inventory: Mapping[str, Any] | None,
    artifact_ref: str = "",
    source_inventory_path: str = "",
    archive_inventory_path: str = "",
    artifact_file_checked: bool = False,
    artifact_file_fresh: bool = False,
    source_inventory_file_checked: bool = False,
    source_inventory_file_fresh: bool = False,
    archive_inventory_file_checked: bool = False,
    archive_inventory_file_fresh: bool = False,
    initial_issues: list[MonitoringSourceTokenEvidenceRevalidationIssue] | None = None,
) -> MonitoringSourceTokenEvidenceRevalidationReport:
    issues = list(initial_issues or ())
    if not isinstance(payload, Mapping):
        _issue(
            issues,
            MonitoringSourceTokenEvidenceRevalidationIssueCode.PAYLOAD_SHAPE_INVALID,
            "artifact",
            "artifact JSON root must be an object",
        )
        return _blocked_report(
            issues,
            artifact_ref=artifact_ref,
            artifact_file_checked=artifact_file_checked,
            artifact_file_fresh=artifact_file_fresh,
        )
    unknown = sorted(set(payload) - _ARTIFACT_KEYS)
    if unknown:
        _issue(
            issues,
            MonitoringSourceTokenEvidenceRevalidationIssueCode.ARTIFACT_FIELD_INVALID,
            "artifact",
            f"unsupported fields: {unknown}",
        )
    if payload.get("schema_version") != SOURCE_TOKEN_CONTENT_ARTIFACT_SCHEMA_VERSION:
        _issue(
            issues,
            MonitoringSourceTokenEvidenceRevalidationIssueCode.ARTIFACT_SCHEMA_INVALID,
            "schema_version",
            "unexpected source-token artifact schema",
        )
    _check_authority(payload, issues)
    if not _valid_sha(payload.get("source_inventory_sha256")) or not _valid_sha(
        payload.get("archive_inventory_sha256")
    ):
        _issue(
            issues,
            MonitoringSourceTokenEvidenceRevalidationIssueCode.ARTIFACT_FIELD_INVALID,
            "inventory_sha256",
            "inventory hashes must be lowercase SHA-256",
        )
    status = _text(payload.get("source_token_revalidation_status")) or "unknown"
    if status != "not_proven":
        _issue(
            issues,
            MonitoringSourceTokenEvidenceRevalidationIssueCode.ARTIFACT_FIELD_INVALID,
            "source_token_revalidation_status",
            f"expected 'not_proven', observed {status!r}",
        )
    content_scan = payload.get("content_scan")
    if not isinstance(content_scan, Mapping):
        _issue(
            issues,
            MonitoringSourceTokenEvidenceRevalidationIssueCode.CONTENT_SCAN_INVALID,
            "content_scan",
            "content_scan must be an object",
        )
    else:
        hit_counts: list[int] = []
        for name in (
            "raw_utf8_token_hits",
            "raw_utf16le_token_hits",
            "raw_utf16be_token_hits",
            "zip_member_token_hits",
        ):
            if not _non_negative_int(content_scan.get(name)):
                _issue(
                    issues,
                    MonitoringSourceTokenEvidenceRevalidationIssueCode.CONTENT_SCAN_INVALID,
                    f"content_scan.{name}",
                    "hit count must be a non-negative integer",
                )
            else:
                hit_counts.append(content_scan[name])
        if any(hit_counts):
            _issue(
                issues,
                MonitoringSourceTokenEvidenceRevalidationIssueCode.CONTENT_SCAN_INVALID,
                "content_scan.hit_counts",
                "non-zero token hits require a new source-bound review; they cannot remain a not_proven fixture",
            )
        if content_scan.get("direct_token_evidence") is not False:
            _issue(
                issues,
                MonitoringSourceTokenEvidenceRevalidationIssueCode.CONTENT_SCAN_INVALID,
                "content_scan.direct_token_evidence",
                "direct_token_evidence must remain false",
            )
    source_valid = False
    archive_valid = False
    summary_matches = False
    counts = {
        "candidate_count": 0,
        "archive_count": 0,
        "member_count": 0,
        "listing_like_member_count": 0,
    }
    if isinstance(source_inventory, Mapping) and isinstance(archive_inventory, Mapping):
        source_valid, archive_valid, counts = _inventory_summary(
            source_inventory, archive_inventory, payload, issues
        )
        listing_obs = payload.get("listing_shape_observation")
        archive_obs = payload.get("archive_observation")
        summary_matches = (
            payload.get("candidate_count") == counts["candidate_count"]
            and isinstance(archive_obs, Mapping)
            and archive_obs.get("archive_count") == counts["archive_count"]
            and archive_obs.get("member_count") == counts["member_count"]
            and archive_obs.get("listing_like_member_count")
            == counts["listing_like_member_count"]
            and isinstance(listing_obs, Mapping)
            and listing_obs.get("source_token_present") is False
            and listing_obs.get("provenance_status") == "not_proven"
        )
        if not summary_matches:
            _issue(
                issues,
                MonitoringSourceTokenEvidenceRevalidationIssueCode.CONTENT_SUMMARY_MISMATCH,
                "summary",
                "persisted content summary differs from inventory-derived counts or status",
            )
    else:
        _issue(
            issues,
            MonitoringSourceTokenEvidenceRevalidationIssueCode.SOURCE_INVENTORY_INVALID,
            "inventories",
            "source and archive inventories must be objects",
        )
    artifact_valid = not any(
        item.code
        in {
            MonitoringSourceTokenEvidenceRevalidationIssueCode.PAYLOAD_SHAPE_INVALID,
            MonitoringSourceTokenEvidenceRevalidationIssueCode.ARTIFACT_SCHEMA_INVALID,
            MonitoringSourceTokenEvidenceRevalidationIssueCode.ARTIFACT_FIELD_INVALID,
            MonitoringSourceTokenEvidenceRevalidationIssueCode.AUTHORITY_FLAG_MISSING,
            MonitoringSourceTokenEvidenceRevalidationIssueCode.AUTHORITY_FLAG_TRUE,
            MonitoringSourceTokenEvidenceRevalidationIssueCode.CONTENT_SCAN_INVALID,
        }
        for item in issues
    )
    return MonitoringSourceTokenEvidenceRevalidationReport(
        status="fresh"
        if artifact_valid
        and source_valid
        and archive_valid
        and summary_matches
        and not issues
        else "blocked",
        evidence_fresh=artifact_valid
        and source_valid
        and archive_valid
        and summary_matches
        and not issues,
        artifact_payload_valid=artifact_valid,
        source_inventory_payload_valid=source_valid,
        archive_inventory_payload_valid=archive_valid,
        content_summary_matches=summary_matches,
        artifact_file_checked=artifact_file_checked,
        artifact_file_fresh=artifact_file_fresh,
        source_inventory_file_checked=source_inventory_file_checked,
        source_inventory_file_fresh=source_inventory_file_fresh,
        archive_inventory_file_checked=archive_inventory_file_checked,
        archive_inventory_file_fresh=archive_inventory_file_fresh,
        source_token_revalidation_status=status,
        candidate_count=counts["candidate_count"],
        archive_count=counts["archive_count"],
        member_count=counts["member_count"],
        listing_like_member_count=counts["listing_like_member_count"],
        issue_count=len(issues),
        artifact_ref=artifact_ref,
        source_inventory_path=source_inventory_path,
        archive_inventory_path=archive_inventory_path,
        issues=tuple(issues),
    )


def _read_json(
    path: Path,
    subject: str,
    issues: list[MonitoringSourceTokenEvidenceRevalidationIssue],
) -> Mapping[str, Any] | None:
    try:
        value = json.loads(path.read_bytes().decode("utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        _issue(
            issues,
            MonitoringSourceTokenEvidenceRevalidationIssueCode.FILE_JSON_INVALID,
            subject,
            str(exc),
        )
        return None
    if not isinstance(value, Mapping):
        _issue(
            issues,
            MonitoringSourceTokenEvidenceRevalidationIssueCode.PAYLOAD_SHAPE_INVALID,
            subject,
            "JSON root must be an object",
        )
        return None
    return value


def _read_checked(
    path: Path | None,
    *,
    subject: str,
    expected_bytes: int | None,
    expected_sha256: str | None,
    issues: list[MonitoringSourceTokenEvidenceRevalidationIssue],
) -> tuple[Mapping[str, Any] | None, bool]:
    if path is None:
        return None, False
    if path.is_symlink():
        _issue(
            issues,
            MonitoringSourceTokenEvidenceRevalidationIssueCode.FILE_SYMLINK_UNSUPPORTED,
            subject,
            "file must not be a symlink",
        )
        return None, False
    if not path.exists():
        _issue(
            issues,
            MonitoringSourceTokenEvidenceRevalidationIssueCode.FILE_MISSING,
            subject,
            "file does not exist",
        )
        return None, False
    if not path.is_file():
        _issue(
            issues,
            MonitoringSourceTokenEvidenceRevalidationIssueCode.FILE_NOT_REGULAR,
            subject,
            "path is not a regular file",
        )
        return None, False
    raw = path.read_bytes()
    actual_sha = hashlib.sha256(raw).hexdigest()
    fresh = True
    if expected_bytes is not None and len(raw) != expected_bytes:
        fresh = False
        _issue(
            issues,
            MonitoringSourceTokenEvidenceRevalidationIssueCode.FILE_BYTES_MISMATCH,
            subject,
            f"expected={expected_bytes}, observed={len(raw)}",
        )
    if expected_sha256 is not None and actual_sha != expected_sha256:
        fresh = False
        _issue(
            issues,
            MonitoringSourceTokenEvidenceRevalidationIssueCode.FILE_SHA256_MISMATCH,
            subject,
            f"expected={expected_sha256}, observed={actual_sha}",
        )
    return _read_json(path, subject, issues), fresh


def revalidate_source_token_file(
    artifact_ref: str,
    *,
    expected_bytes: int,
    expected_sha256: str,
    source_inventory_bytes: int,
    source_inventory_sha256: str,
    archive_inventory_bytes: int,
    archive_inventory_sha256: str,
    workspace_root: str | Path,
) -> MonitoringSourceTokenEvidenceRevalidationReport:
    issues: list[MonitoringSourceTokenEvidenceRevalidationIssue] = []
    try:
        root = Path(workspace_root)
    except TypeError as exc:
        raise MonitoringSourceTokenEvidenceRevalidationError(
            "workspace_root must be path-like"
        ) from exc
    artifact = _safe_relative_path(
        artifact_ref, workspace_root=root, issues=issues, subject="artifact_ref"
    )
    if artifact is None:
        return _blocked_report(
            issues, artifact_ref=_text(artifact_ref), artifact_file_checked=True
        )
    if not _non_negative_int(expected_bytes) or not _valid_sha(expected_sha256):
        _issue(
            issues,
            MonitoringSourceTokenEvidenceRevalidationIssueCode.ARTIFACT_FIELD_INVALID,
            "artifact_expected",
            "artifact expected bytes/SHA are invalid",
        )
    if not _non_negative_int(source_inventory_bytes) or not _valid_sha(
        source_inventory_sha256
    ):
        _issue(
            issues,
            MonitoringSourceTokenEvidenceRevalidationIssueCode.ARTIFACT_FIELD_INVALID,
            "source_inventory_expected",
            "source inventory expected bytes/SHA are invalid",
        )
    if not _non_negative_int(archive_inventory_bytes) or not _valid_sha(
        archive_inventory_sha256
    ):
        _issue(
            issues,
            MonitoringSourceTokenEvidenceRevalidationIssueCode.ARTIFACT_FIELD_INVALID,
            "archive_inventory_expected",
            "archive inventory expected bytes/SHA are invalid",
        )
    payload, artifact_fresh = _read_checked(
        artifact,
        subject="artifact_ref",
        expected_bytes=expected_bytes,
        expected_sha256=expected_sha256,
        issues=issues,
    )
    if payload is None:
        return _blocked_report(
            issues,
            artifact_ref=_text(artifact_ref),
            artifact_file_checked=True,
            artifact_file_fresh=artifact_fresh,
        )
    source_rel = _text(payload.get("source_inventory_path"))
    archive_rel = _text(payload.get("archive_inventory_path"))
    source_path = _safe_relative_path(
        source_rel, workspace_root=root, issues=issues, subject="source_inventory_path"
    )
    archive_path = _safe_relative_path(
        archive_rel,
        workspace_root=root,
        issues=issues,
        subject="archive_inventory_path",
    )
    source_payload, source_fresh = _read_checked(
        source_path,
        subject="source_inventory_path",
        expected_bytes=source_inventory_bytes,
        expected_sha256=source_inventory_sha256,
        issues=issues,
    )
    archive_payload, archive_fresh = _read_checked(
        archive_path,
        subject="archive_inventory_path",
        expected_bytes=archive_inventory_bytes,
        expected_sha256=archive_inventory_sha256,
        issues=issues,
    )
    return revalidate_source_token_payload(
        payload,
        source_inventory=source_payload,
        archive_inventory=archive_payload,
        artifact_ref=_text(artifact_ref),
        source_inventory_path=source_rel,
        archive_inventory_path=archive_rel,
        artifact_file_checked=True,
        artifact_file_fresh=artifact_fresh,
        source_inventory_file_checked=source_path is not None,
        source_inventory_file_fresh=source_fresh,
        archive_inventory_file_checked=archive_path is not None,
        archive_inventory_file_fresh=archive_fresh,
        initial_issues=issues,
    )


__all__ = [
    "SOURCE_TOKEN_CONTENT_ARTIFACT_SCHEMA_VERSION",
    "SOURCE_TOKEN_EVIDENCE_REVALIDATION_SCHEMA_VERSION",
    "MonitoringSourceTokenEvidenceRevalidationError",
    "MonitoringSourceTokenEvidenceRevalidationIssue",
    "MonitoringSourceTokenEvidenceRevalidationIssueCode",
    "MonitoringSourceTokenEvidenceRevalidationReport",
    "revalidate_source_token_file",
    "revalidate_source_token_payload",
]
