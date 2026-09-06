"""Product-ready deterministic listing admission pipeline (Phase C C1)."""

from __future__ import annotations

import os
import re
import shutil
import tempfile
from pathlib import Path
from pathlib import PurePosixPath
from typing import Any, BinaryIO, Callable, Iterable, Mapping, Optional, Sequence

from ..domain.entities import SourceRevision, content_hash
from ..graph.store import Store
from ..intelligence.structure_profile import (
    build_listing_profile,
    build_table_locators,
    build_table_snapshot,
    canonical_listing_content,
    execution_source_revision,
    table_rows_from_sheet,
)
from ..runtime.runtime_progress import ARTIFACT_DIR_NAME, RUNTIME_DB_NAME, RUNTIME_DIR_NAME
from .staging import (
    StagingHashMismatchError,
    StagingIncompleteError,
    StagingSourceError,
    list_attempt_ids,
    load_attempt,
    stage_copy,
)
from .workbook_manifest import (
    SOURCE_PROFILE_RECONCILIATION_SCHEMA_VERSION,
    WORKBOOK_MANIFEST_SCHEMA_VERSION,
    WorkbookManifestError,
    manifest_unavailable_summary,
    reconcile_source_to_profile,
    validate_workbook_manifest_bundle,
)

ADMISSION_RECORD_KIND = "data_admission"
LOCATOR_INDEX_KIND = "source_cell_locator_index"
DEFAULT_LISTING_SUFFIXES = frozenset({".csv", ".xls", ".xlsx", ".xlsm"})
_UPLOAD_CHUNK_SIZE = 1024 * 1024
_PROJECT_ID_HEADERS = frozenset(
    {
        "STUDYID",
        "STUDYOID",
        "PSTUDYID",
        "PROJECTID",
        "PROTOCOLID",
        "项目编号",
        "研究编号",
        "方案编号",
    }
)


class AdmissionPipelineError(RuntimeError):
    """Stable error code consumed by the product route."""

    def __init__(self, code: str) -> None:
        self.code = str(code)
        super().__init__(self.code)


def _relative_listing_paths(source: Path, suffixes: frozenset[str]) -> tuple[Path, tuple[str, ...]]:
    resolved = source.expanduser().resolve()
    if resolved.is_file():
        if resolved.suffix.lower() not in suffixes:
            raise AdmissionPipelineError("admission_profile_unavailable")
        return resolved.parent, (resolved.name,)
    if not resolved.is_dir():
        raise AdmissionPipelineError("admission_source_invalid")
    files = tuple(
        path.relative_to(resolved).as_posix()
        for path in sorted(resolved.rglob("*"))
        if path.is_file() and path.suffix.lower() in suffixes
    )
    if not files:
        raise AdmissionPipelineError("admission_profile_unavailable")
    return resolved, files


def _store(workspace_dir: Path) -> Store:
    runtime = Path(workspace_dir) / RUNTIME_DIR_NAME
    runtime.mkdir(parents=True, exist_ok=True)
    return Store(runtime / RUNTIME_DB_NAME, runtime / ARTIFACT_DIR_NAME)


def _candidate_roles(column: Any) -> list[str]:
    roles = []
    if column.is_subject_key_candidate:
        roles.append("受试者标识")
    if column.is_visit_candidate:
        roles.append("访视")
    if column.is_date_candidate:
        roles.append("日期")
    return roles


def _normalized_identifier(value: Any) -> str:
    identifier = str(value or "").upper().strip()
    # Export environments are annotations, not arbitrary study-ID prefixes.
    # Strip only an explicit, bracketed environment suffix before comparing
    # the complete study identifier. Unknown suffixes remain significant.
    identifier = re.sub(
        r"\s*\[(?:PROD|PRODUCTION|UAT|TEST|DEV)\]\s*$", "", identifier
    )
    return re.sub(r"[^A-Z0-9]", "", identifier)


def _normalized_header(value: Any) -> str:
    return re.sub(r"[^A-Z0-9\u4e00-\u9fff]", "", str(value or "").upper())


def _project_identifiers(
    headers: Sequence[str],
    rows: Sequence[Mapping[str, Any]],
) -> set[str]:
    identity_headers = [
        header
        for header in headers
        if _normalized_header(header) in _PROJECT_ID_HEADERS
    ]
    return {
        normalized
        for row in rows
        for header in identity_headers
        if (normalized := _normalized_identifier(row.get(header)))
    }


def _project_identity_assessment(
    expected_values: Sequence[str],
    observed_values: Iterable[str],
) -> dict[str, Any]:
    expected = sorted(
        {
            normalized
            for value in expected_values
            if (normalized := _normalized_identifier(value))
        }
    )
    observed = sorted(
        {
            normalized
            for value in observed_values
            if (normalized := _normalized_identifier(value))
        }
    )
    compatible = bool(expected and observed) and all(
        observed_id in expected
        for observed_id in observed
    )
    status = (
        "not_configured"
        if not expected
        else "not_observed"
        if not observed
        else "matched"
        if compatible
        else "conflict"
    )
    return {
        "schema_version": "mm-admission-project-identity-v2",
        "status": status,
        "expected_count": len(expected),
        "observed_count": len(observed),
        "expected_sha256": content_hash(expected),
        "observed_sha256": content_hash(observed),
    }


def _public_table(
    source_file: str,
    table: Any,
    source_headers: Sequence[str] = (),
) -> dict[str, Any]:
    columns = []
    for index, column in enumerate(table.columns):
        columns.append({
            "name": column.name,
            "source_label": (
                str(source_headers[index]).strip()
                if index < len(source_headers)
                and str(source_headers[index]).strip()
                else column.name
            ),
            "inferred_type": column.inferred_type,
            "missing_count": column.missing_count,
            "distinct_count": column.distinct_count,
            "samples": list(column.samples),
            "date_range": column.date_range,
            "suggested_roles": _candidate_roles(column),
        })
    return {
        "name": table.table_name,
        "source_file": source_file,
        "row_count": table.row_count,
        "column_count": table.column_count,
        "columns": columns,
        "needs_confirmation": sum(bool(item["suggested_roles"]) for item in columns),
    }


class DataAdmissionPipeline:
    """Compose staging, parsing, profiling and the existing Store authority.

    The workbook physical-integrity manifest comes from the parse authority:
    every ``ListingSheetPayload`` parsed by a manifest-capable parser carries
    the file's ``WorkbookPhysicalManifest``, which this pipeline pairs with
    the staged file digest, validates, reconciles against the profiled tables
    and persists inside ``technical_details``.  ``manifest_provider``
    optionally overrides that source (tests, synthetic admissions).  The
    mapping bridge refuses to run unless the reconciliation is complete; a
    record admitted without any manifest carries a ``manifest_unavailable``
    reconciliation so the gate fails closed.
    """

    def __init__(
        self,
        parser: Callable[[str, bytes], Sequence[Any]],
        *,
        supported_suffixes: Iterable[str] = DEFAULT_LISTING_SUFFIXES,
        manifest_provider: Optional[Callable[[str, bytes], Mapping[str, Any]]] = None,
        expected_project_identifiers: Optional[
            Callable[[str], Sequence[str]]
        ] = None,
    ) -> None:
        self._parser = parser
        self._suffixes = frozenset(str(value).lower() for value in supported_suffixes)
        self._manifest_provider = manifest_provider
        self._expected_project_identifiers = expected_project_identifiers

    @staticmethod
    def _admission_workspace(workspace_dir: Path) -> Path:
        return Path(workspace_dir) / "admissions"

    def _manifest_payload(
        self,
        source_file: str,
        source_bytes: bytes,
        sheets: Sequence[Any],
    ) -> Optional[Mapping[str, Any]]:
        """Resolve the parse authority's manifest for one staged file.

        ``manifest_provider`` overrides the payload-attached manifest so
        tests and synthetic admissions can inject or mutate the evidence.
        Without a provider the manifest attached to the parsed sheet payloads
        by the parse authority is used as-is.
        """

        if self._manifest_provider is not None:
            try:
                return self._manifest_provider(source_file, source_bytes)
            except Exception as exc:
                raise AdmissionPipelineError(
                    "admission_profile_unavailable"
                ) from exc
        for sheet in sheets:
            candidate = getattr(sheet, "workbook_manifest", None)
            if candidate is None:
                continue
            if isinstance(candidate, Mapping):
                return dict(candidate)
            dump = getattr(candidate, "model_dump", None)
            if callable(dump):
                return dump()
            return None
        return None

    def create_attempt(
        self, *, project_id: str, source_dir: Path, workspace_dir: Path
    ) -> Mapping[str, Any]:
        root, relative_paths = _relative_listing_paths(Path(source_dir), self._suffixes)
        admission_workspace = self._admission_workspace(workspace_dir)
        try:
            attempt = stage_copy(root, relative_paths, admission_workspace)
        except StagingSourceError as exc:
            raise AdmissionPipelineError("admission_source_invalid") from exc
        except (StagingHashMismatchError, StagingIncompleteError) as exc:
            raise AdmissionPipelineError("admission_copy_rejected") from exc

        profiles = []
        public_tables = []
        revision_ids: list[str] = []
        snapshot_ids: list[str] = []
        locator_index_ids: list[str] = []
        manifest_files: list[dict[str, Any]] = []
        staged_file_payloads: list[dict[str, Any]] = []
        observed_project_identifiers: set[str] = set()
        store = _store(workspace_dir)
        try:
            try:
                project = store.get_project(project_id)
            except Exception as exc:
                if "project not found" not in str(exc).casefold():
                    raise
                store.create_project(project_id, project_id, is_synthetic=False)
                project = store.get_project(project_id)
            if project.is_synthetic:
                raise AdmissionPipelineError("admission_project_identity_conflict")
            for staged_file in attempt.files:
                file_path = attempt.file_path(staged_file.path)
                source_bytes = file_path.read_bytes()
                staged_file_payloads.append({
                    "path": staged_file.path,
                    "size": staged_file.size,
                    "sha256": staged_file.sha256,
                })
                revision_id = "srcc1_" + content_hash({
                    "project_id": project_id,
                    "relative_path": staged_file.path,
                    "sha256": staged_file.sha256,
                })[:24]
                revision = SourceRevision.from_bytes(
                    revision_id,
                    project_id,
                    "listing",
                    staged_file.sha256[:16],
                    source_bytes,
                    scope=(("source_file", staged_file.path),),
                )
                store.add_source_revision(execution_source_revision(revision))
                try:
                    sheets = list(self._parser(file_path.name, source_bytes))
                except Exception as exc:
                    raise AdmissionPipelineError("admission_profile_unavailable") from exc
                profile = build_listing_profile(
                    project_id,
                    revision_id,
                    file_path.name,
                    staged_file.sha256,
                    sheets,
                )
                profiles.append(profile)
                revision_ids.append(revision_id)
                manifest_payload = self._manifest_payload(
                    file_path.name, source_bytes, sheets
                )
                if manifest_payload is not None:
                    manifest_files.append({
                        "source_file": staged_file.path,
                        "source_file_sha256": staged_file.sha256,
                        "manifest": manifest_payload,
                    })
                if len(profile.tables) != len(sheets):
                    raise AdmissionPipelineError("admission_profile_unavailable")
                for table, sheet in zip(profile.tables, sheets):
                    public_tables.append(
                        _public_table(
                            file_path.name,
                            table,
                            tuple(getattr(sheet, "source_headers", ()) or ()),
                        )
                    )
                for sheet in sheets:
                    table_name, headers, rows, row_numbers = table_rows_from_sheet(sheet)
                    observed_project_identifiers.update(
                        _project_identifiers(headers, rows)
                    )
                    snapshot = build_table_snapshot(
                        project_id,
                        revision_id,
                        attempt.manifest_hash[:16],
                        table_name,
                        headers,
                        rows,
                        is_synthetic=project.is_synthetic,
                    )
                    store.add_listing_snapshot(snapshot, canonical_listing_content([sheet]))
                    locators = build_table_locators(
                        project_id,
                        revision_id,
                        snapshot.snapshot_id,
                        file_path.name,
                        staged_file.sha256,
                        table_name,
                        headers,
                        rows,
                        row_numbers,
                    )
                    locator_index = {
                        "project_id": project_id,
                        "source_revision_id": revision_id,
                        "snapshot_id": snapshot.snapshot_id,
                        "source_file": file_path.name,
                        "source_file_digest": staged_file.sha256,
                        "table_name": table_name,
                        "row_numbers": list(row_numbers),
                        "columns": list(headers),
                        "locator_ids": [locator.locator_id for locator in locators],
                    }
                    store.put_domain_object(
                        LOCATOR_INDEX_KIND, snapshot.snapshot_id, locator_index
                    )
                    snapshot_ids.append(snapshot.snapshot_id)
                    locator_index_ids.append(snapshot.snapshot_id)

            if manifest_files:
                manifest_bundle = {
                    "schema_version": WORKBOOK_MANIFEST_SCHEMA_VERSION,
                    "files": manifest_files,
                }
                try:
                    validated_bundle = validate_workbook_manifest_bundle(
                        manifest_bundle
                    )
                    reconciliation = reconcile_source_to_profile(
                        validated_bundle,
                        technical_files=staged_file_payloads,
                        tables=public_tables,
                    )
                except WorkbookManifestError as exc:
                    raise AdmissionPipelineError(
                        "admission_profile_unavailable"
                    ) from exc
            else:
                manifest_bundle = None
                reconciliation = manifest_unavailable_summary()
            expected_project_identifiers = (
                tuple(self._expected_project_identifiers(project_id))
                if self._expected_project_identifiers is not None
                else ()
            )
            project_identity = _project_identity_assessment(
                expected_project_identifiers,
                observed_project_identifiers,
            )
            if project_identity["status"] == "conflict":
                raise AdmissionPipelineError(
                    "admission_project_identity_conflict"
                )
            summary = {
                "files": len(attempt.files),
                "tables": len(public_tables),
                "rows": sum(int(table["row_count"]) for table in public_tables),
            }
            record = {
                "attempt_id": attempt.attempt_id,
                "project_id": project_id,
                "state": "profile_ready",
                "summary": summary,
                "tables": public_tables,
                "technical_details": {
                    "manifest_hash": attempt.manifest_hash,
                    "files": staged_file_payloads,
                    "revision_ids": revision_ids,
                    "snapshot_ids": snapshot_ids,
                    "locator_index_ids": locator_index_ids,
                    "profile_ids": [profile.profile_id for profile in profiles],
                    "project_identity": project_identity,
                    "physical_manifest": manifest_bundle,
                    "source_profile_reconciliation": {
                        "schema_version": SOURCE_PROFILE_RECONCILIATION_SCHEMA_VERSION,
                        "status": reconciliation["status"],
                        "complete": reconciliation["complete"],
                        "manifest_sha256": reconciliation["manifest_sha256"],
                        "files": reconciliation["files"],
                        "blocking_finding_codes": reconciliation["blocking_finding_codes"],
                        "findings": reconciliation["findings"],
                    },
                },
            }
            store.put_domain_object(ADMISSION_RECORD_KIND, attempt.attempt_id, record)
            return {key: value for key, value in record.items() if key != "project_id"}
        except AdmissionPipelineError:
            raise
        except Exception as exc:
            raise AdmissionPipelineError("admission_pipeline_failed") from exc
        finally:
            store.close()

    def revalidate_project_identity(
        self,
        *,
        project_id: str,
        attempt_id: str,
        workspace_dir: Path,
    ) -> Mapping[str, Any]:
        """Recheck a persisted attempt and quarantine a cross-project binding."""

        if self._expected_project_identifiers is None:
            raise AdmissionPipelineError("admission_project_identity_unavailable")
        record = self._record(
            project_id=project_id,
            attempt_id=attempt_id,
            workspace_dir=workspace_dir,
        )
        technical = dict(record.get("technical_details") or {})
        observed: set[str] = set()
        store = _store(workspace_dir)
        try:
            for snapshot_id in technical.get("snapshot_ids") or ():
                content = store.load_listing_content(str(snapshot_id))
                for rows in content.values():
                    if not isinstance(rows, list) or not rows:
                        continue
                    headers = tuple(rows[0])
                    observed.update(_project_identifiers(headers, rows))
            assessment = _project_identity_assessment(
                tuple(self._expected_project_identifiers(project_id)),
                observed,
            )
            technical["project_identity"] = assessment
            record["technical_details"] = technical
            if assessment["status"] == "conflict":
                record["state"] = "identity_conflict"
            store.put_domain_object(ADMISSION_RECORD_KIND, attempt_id, record)
        finally:
            store.close()
        return {
            "attempt_id": attempt_id,
            "state": record["state"],
            "identity_status": assessment["status"],
        }

    def create_uploaded_attempt(
        self,
        *,
        project_id: str,
        uploads: Sequence[tuple[str, BinaryIO]],
        workspace_dir: Path,
    ) -> Mapping[str, Any]:
        """Admit browser-selected files without exposing a local path.

        Upload streams are first materialized under a short-lived directory
        inside the project workspace. ``create_attempt`` then applies the same
        staging hash, atomic-completion, profile and Store contract used for a
        read-only local source. The temporary intake is always removed; only
        the verified staging attempt remains.
        """
        if not uploads:
            raise AdmissionPipelineError("admission_source_invalid")
        intake_parent = self._admission_workspace(workspace_dir) / "upload-intake"
        intake_parent.mkdir(parents=True, exist_ok=True)
        intake = Path(tempfile.mkdtemp(prefix="upload-", dir=intake_parent))
        seen: set[str] = set()
        try:
            for raw_path, stream in uploads:
                raw = str(raw_path or "").replace("\\", "/")
                normalized = raw.strip("/")
                relative = PurePosixPath(normalized)
                if (
                    not normalized
                    or raw.startswith("/")
                    or relative.is_absolute()
                    or any(part in {"", ".", ".."} for part in relative.parts)
                    or ":" in relative.parts[0]
                    or normalized in seen
                    or relative.suffix.lower() not in self._suffixes
                ):
                    raise AdmissionPipelineError("admission_source_invalid")
                seen.add(normalized)
                target = intake.joinpath(*relative.parts)
                target.parent.mkdir(parents=True, exist_ok=True)
                try:
                    stream.seek(0)
                except (AttributeError, OSError):
                    pass
                with open(target, "xb") as output:
                    while True:
                        chunk = stream.read(_UPLOAD_CHUNK_SIZE)
                        if not chunk:
                            break
                        output.write(chunk)
                    output.flush()
                    os.fsync(output.fileno())
            return self.create_attempt(
                project_id=project_id,
                source_dir=intake,
                workspace_dir=workspace_dir,
            )
        except AdmissionPipelineError:
            raise
        except Exception as exc:
            raise AdmissionPipelineError("admission_copy_rejected") from exc
        finally:
            shutil.rmtree(intake, ignore_errors=True)
            try:
                intake_parent.rmdir()
            except OSError:
                pass

    def _record(
        self, *, project_id: str, attempt_id: str, workspace_dir: Path
    ) -> dict[str, Any]:
        try:
            load_attempt(self._admission_workspace(workspace_dir), attempt_id)
        except StagingIncompleteError as exc:
            raise AdmissionPipelineError("admission_attempt_not_found") from exc
        try:
            store = _store(workspace_dir)
            persisted = store.get_domain_object(ADMISSION_RECORD_KIND, attempt_id)
        except Exception as exc:
            raise AdmissionPipelineError("admission_attempt_not_found") from exc
        finally:
            if "store" in locals():
                store.close()
        if persisted is None or not isinstance(persisted[1], dict):
            raise AdmissionPipelineError("admission_attempt_not_found")
        record = dict(persisted[1])
        if record.get("project_id") != project_id:
            raise AdmissionPipelineError("admission_attempt_not_found")
        return record

    def attempt_status(
        self, *, project_id: str, attempt_id: str, workspace_dir: Path
    ) -> Mapping[str, Any]:
        record = self._record(
            project_id=project_id, attempt_id=attempt_id, workspace_dir=workspace_dir
        )
        return {
            "attempt_id": attempt_id,
            "state": record["state"],
            "summary": record["summary"],
            "technical_details": record["technical_details"],
        }

    def latest_attempt_status(
        self, *, project_id: str, workspace_dir: Path
    ) -> Mapping[str, Any]:
        admission_workspace = self._admission_workspace(workspace_dir)
        attempts = [
            load_attempt(admission_workspace, attempt_id, verify_files=False)
            for attempt_id in list_attempt_ids(admission_workspace)
        ]
        if not attempts:
            raise AdmissionPipelineError("admission_attempt_not_found")
        latest = max(attempts, key=lambda item: (item.created_at, item.attempt_id))
        return self.attempt_status(
            project_id=project_id,
            attempt_id=latest.attempt_id,
            workspace_dir=workspace_dir,
        )

    def profile_preview(
        self, *, project_id: str, attempt_id: str, workspace_dir: Path
    ) -> Mapping[str, Any]:
        record = self._record(
            project_id=project_id, attempt_id=attempt_id, workspace_dir=workspace_dir
        )
        return {
            "attempt_id": attempt_id,
            "tables": record["tables"],
            "summary": record["summary"],
            "technical_details": record["technical_details"],
        }


__all__ = [
    "ADMISSION_RECORD_KIND",
    "DEFAULT_LISTING_SUFFIXES",
    "LOCATOR_INDEX_KIND",
    "AdmissionPipelineError",
    "DataAdmissionPipeline",
]
