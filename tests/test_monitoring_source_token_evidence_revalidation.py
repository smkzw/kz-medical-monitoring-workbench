from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from services.api.app.monitoring_source_token_evidence_revalidation import (
    MonitoringSourceTokenEvidenceRevalidationIssueCode,
    revalidate_source_token_file,
    revalidate_source_token_payload,
)


def _inventories() -> tuple[dict, dict]:
    candidate = "/synthetic/MY009/listing.xlsx"
    source = {
        "schema_version": "medical_monitoring_my009_source_inventory_recheck_v1",
        "search_roots": ["/synthetic/MY009"],
        "file_count": 2,
        "listing_identity_candidates": [candidate],
        "rows": [
            {
                "path": candidate,
                "relative_to_langlai": "MY009/listing.xlsx",
                "extension": ".xlsx",
                "bytes": 100,
                "sha256": "1" * 64,
                "candidate_type": "workbook_or_document",
                "exclusion": "",
            },
            {
                "path": "/synthetic/MY009/~$listing.xlsx",
                "relative_to_langlai": "MY009/~$listing.xlsx",
                "extension": ".xlsx",
                "bytes": 10,
                "sha256": "2" * 64,
                "candidate_type": "workbook_or_document",
                "exclusion": "temporary_office_lock_file",
            },
        ],
        "conclusion": "synthetic inventory fixture",
    }
    archive = {
        "schema_version": "medical_monitoring_my009_archive_member_inventory_v1",
        "mode": "read_only_member_listing_and_ooxml_metadata",
        "archives": [
            {
                "path": "/synthetic/MY009/archive.rar",
                "bytes": 200,
                "sha256": "3" * 64,
                "listing_tool": "7z",
                "member_count": 1,
                "members": [
                    {
                        "path": "protocol.docx",
                        "bytes": 50,
                        "crc32": "ABCDEF01",
                        "classification": "protocol_document",
                        "listing_candidate": False,
                    }
                ],
            }
        ],
        "conclusion": {
            "listing_like_member_count": 0,
            "provenance_complete_legacy_snapshot_found": False,
        },
    }
    return source, archive


def _payload(source: dict, archive: dict) -> dict:
    return {
        "schema_version": "medical_monitoring_my009_source_token_content_revalidation_v1",
        "read_only": True,
        "legacy_source_token": "2ef9c8d72d74",
        "source_inventory_path": "source_inventory.json",
        "source_inventory_sha256": hashlib.sha256(_raw(source)).hexdigest(),
        "archive_inventory_path": "archive_inventory.json",
        "archive_inventory_sha256": hashlib.sha256(_raw(archive)).hexdigest(),
        "candidate_count": 1,
        "candidate_extension_counts": {".xlsx": 1},
        "content_scan": {
            "raw_utf8_token_hits": 0,
            "raw_utf16le_token_hits": 0,
            "raw_utf16be_token_hits": 0,
            "zip_member_token_hits": 0,
            "direct_token_evidence": False,
            "method": "synthetic bounded scan",
        },
        "listing_shape_observation": {
            "path": "/synthetic/MY009/listing.xlsx",
            "sheet_count": 2,
            "header_markers": ["USUBJID", "SITEID"],
            "source_token_present": False,
            "provenance_status": "not_proven",
        },
        "archive_observation": {
            "archive_count": 1,
            "member_count": 1,
            "listing_like_member_count": 0,
        },
        "source_token_revalidation_status": "not_proven",
        "source_token_synthesized": False,
        "write_permitted": False,
        "migration_ready": False,
        "conclusion": "synthetic evidence fixture; not a source-token conclusion",
    }


def _raw(value: dict) -> bytes:
    return json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode()


def _write(path: Path, value: dict) -> tuple[int, str]:
    raw = _raw(value)
    path.write_bytes(raw)
    return len(raw), hashlib.sha256(raw).hexdigest()


def test_payload_revalidation_is_fresh_but_keeps_token_not_proven() -> None:
    source, archive = _inventories()
    report = revalidate_source_token_payload(
        _payload(source, archive),
        source_inventory=source,
        archive_inventory=archive,
        artifact_ref="artifact.json",
        source_inventory_path="source_inventory.json",
        archive_inventory_path="archive_inventory.json",
    )

    assert report.status == "fresh"
    assert report.evidence_fresh is True
    assert report.source_token_revalidation_status == "not_proven"
    assert report.candidate_count == 1
    assert report.archive_count == 1
    assert report.member_count == 1
    assert report.listing_like_member_count == 0
    assert report.source_token_synthesized is False
    assert report.write_permitted is False


def test_file_revalidation_checks_all_three_artifacts_and_source_drift(
    tmp_path: Path,
) -> None:
    source, archive = _inventories()
    artifact = _payload(source, archive)
    artifact_path = tmp_path / "artifact.json"
    source_path = tmp_path / "source_inventory.json"
    archive_path = tmp_path / "archive_inventory.json"
    artifact_bytes, artifact_sha = _write(artifact_path, artifact)
    source_bytes, source_sha = _write(source_path, source)
    archive_bytes, archive_sha = _write(archive_path, archive)

    report = revalidate_source_token_file(
        "artifact.json",
        expected_bytes=artifact_bytes,
        expected_sha256=artifact_sha,
        source_inventory_bytes=source_bytes,
        source_inventory_sha256=source_sha,
        archive_inventory_bytes=archive_bytes,
        archive_inventory_sha256=archive_sha,
        workspace_root=tmp_path,
    )
    assert report.status == "fresh"
    assert report.artifact_file_fresh is True
    assert report.source_inventory_file_fresh is True
    assert report.archive_inventory_file_fresh is True

    source_path.write_bytes(source_path.read_bytes() + b"drift")
    drifted = revalidate_source_token_file(
        "artifact.json",
        expected_bytes=artifact_bytes,
        expected_sha256=artifact_sha,
        source_inventory_bytes=source_bytes,
        source_inventory_sha256=source_sha,
        archive_inventory_bytes=archive_bytes,
        archive_inventory_sha256=archive_sha,
        workspace_root=tmp_path,
    )
    assert drifted.status == "blocked"
    assert MonitoringSourceTokenEvidenceRevalidationIssueCode.FILE_BYTES_MISMATCH in {
        item.code for item in drifted.issues
    }


@pytest.mark.parametrize(
    "hash_field",
    ["expected_sha256", "source_inventory_sha256", "archive_inventory_sha256"],
)
def test_file_expected_hashes_require_exact_lowercase_bytes(
    tmp_path: Path, hash_field: str
) -> None:
    source, archive = _inventories()
    artifact_path = tmp_path / "artifact.json"
    source_path = tmp_path / "source_inventory.json"
    archive_path = tmp_path / "archive_inventory.json"
    artifact_bytes, artifact_sha = _write(artifact_path, _payload(source, archive))
    source_bytes, source_sha = _write(source_path, source)
    archive_bytes, archive_sha = _write(archive_path, archive)

    arguments = {
        "expected_bytes": artifact_bytes,
        "expected_sha256": artifact_sha,
        "source_inventory_bytes": source_bytes,
        "source_inventory_sha256": source_sha,
        "archive_inventory_bytes": archive_bytes,
        "archive_inventory_sha256": archive_sha,
        "workspace_root": tmp_path,
    }
    arguments[hash_field] = f" {arguments[hash_field]}"
    report = revalidate_source_token_file("artifact.json", **arguments)

    assert report.status == "blocked"
    assert any(
        item.code
        == MonitoringSourceTokenEvidenceRevalidationIssueCode.ARTIFACT_FIELD_INVALID
        for item in report.issues
    )


def test_summary_tamper_blocks_without_synthesizing_token() -> None:
    source, archive = _inventories()
    payload = _payload(source, archive)
    payload["candidate_count"] = 13
    report = revalidate_source_token_payload(
        payload, source_inventory=source, archive_inventory=archive
    )

    assert report.status == "blocked"
    assert any(
        item.code
        == MonitoringSourceTokenEvidenceRevalidationIssueCode.CONTENT_SUMMARY_MISMATCH
        for item in report.issues
    )
    assert report.source_token_revalidation_status == "not_proven"
    assert report.source_token_synthesized is False


def test_authority_drift_blocks_even_when_inventory_matches() -> None:
    source, archive = _inventories()
    payload = _payload(source, archive)
    payload["source_token_synthesized"] = True
    report = revalidate_source_token_payload(
        payload, source_inventory=source, archive_inventory=archive
    )

    assert report.status == "blocked"
    assert any(
        item.code
        == MonitoringSourceTokenEvidenceRevalidationIssueCode.AUTHORITY_FLAG_TRUE
        for item in report.issues
    )
    assert report.write_permitted is False


def test_direct_token_evidence_cannot_be_silently_accepted() -> None:
    source, archive = _inventories()
    payload = _payload(source, archive)
    payload["content_scan"]["direct_token_evidence"] = True
    report = revalidate_source_token_payload(
        payload, source_inventory=source, archive_inventory=archive
    )

    assert report.status == "blocked"
    assert any(
        item.code
        == MonitoringSourceTokenEvidenceRevalidationIssueCode.CONTENT_SCAN_INVALID
        for item in report.issues
    )


def test_nonzero_token_hit_requires_new_source_bound_review() -> None:
    source, archive = _inventories()
    payload = _payload(source, archive)
    payload["content_scan"]["raw_utf8_token_hits"] = 1
    report = revalidate_source_token_payload(
        payload, source_inventory=source, archive_inventory=archive
    )

    assert report.status == "blocked"
    assert any(
        item.code
        == MonitoringSourceTokenEvidenceRevalidationIssueCode.CONTENT_SCAN_INVALID
        for item in report.issues
    )


def test_unsafe_artifact_path_blocks_before_access(tmp_path: Path) -> None:
    report = revalidate_source_token_file(
        "../artifact.json",
        expected_bytes=1,
        expected_sha256="0" * 64,
        source_inventory_bytes=1,
        source_inventory_sha256="0" * 64,
        archive_inventory_bytes=1,
        archive_inventory_sha256="0" * 64,
        workspace_root=tmp_path,
    )

    assert report.status == "blocked"
    assert any(
        item.code == MonitoringSourceTokenEvidenceRevalidationIssueCode.FILE_PATH_UNSAFE
        for item in report.issues
    )
