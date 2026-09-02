"""Deterministic C3 materialization of confirmed listing mappings."""

from __future__ import annotations

from dataclasses import dataclass
import gzip
import hashlib
import json
import os
from pathlib import Path
import tempfile
from typing import Any, Mapping, Protocol

from ..domain.execution import (
    ACCEPTANCE_CHAIN,
    ACCEPTED_BY_SYSTEM_POLICY,
    SnapshotAcceptanceState,
)
from ..graph.store import Store
from ..intelligence.normalization import normalize_value
from ..intelligence.primitives import canonical_json, content_hash
from ..intelligence.structure_profile import (
    SourceCellLocator,
    resolve_locator,
)
from ..runtime.runtime_progress import ARTIFACT_DIR_NAME, RUNTIME_DB_NAME, RUNTIME_DIR_NAME
from .pipeline import ADMISSION_RECORD_KIND, LOCATOR_INDEX_KIND
from .staging import list_attempt_ids, load_attempt

FACT_SET_KIND = "canonical_fact_set"
FACT_MATERIALIZATION_KIND = "canonical_fact_materialization"
FACT_SET_SCHEMA_VERSION = "mm-c3-canonical-fact-set-v1"
FACT_MATERIALIZATION_SCHEMA_VERSION = "mm-c3-fact-materialization-v1"


class FactMaterializationError(RuntimeError):
    """Stable product error code."""

    def __init__(self, code: str) -> None:
        self.code = str(code)
        super().__init__(self.code)


class ConfirmedMappingRepository(Protocol):
    def find_draft_for_batch(self, project_id: str, batch_id: str) -> Any: ...

    def get_revision(self, project_id: str, mapping_revision: str) -> Any: ...


def _store(workspace_dir: Path) -> Store:
    runtime = Path(workspace_dir) / RUNTIME_DIR_NAME
    return Store(runtime / RUNTIME_DB_NAME, runtime / ARTIFACT_DIR_NAME)


def _payload(value: Any) -> dict[str, Any]:
    if hasattr(value, "model_dump"):
        return value.model_dump(mode="json")
    return dict(value)


def _fact_artifact_path(workspace_dir: Path, digest: str) -> Path:
    return (
        Path(workspace_dir)
        / RUNTIME_DIR_NAME
        / ARTIFACT_DIR_NAME
        / "canonical_fact_sets"
        / f"{digest}.json.gz"
    )


def _write_fact_artifact(workspace_dir: Path, payload: Mapping[str, Any]) -> tuple[str, str]:
    encoded = canonical_json(payload).encode("utf-8")
    digest = content_hash(payload)
    path = _fact_artifact_path(workspace_dir, digest)
    path.parent.mkdir(parents=True, exist_ok=True)
    compressed = gzip.compress(encoded, mtime=0)
    artifact_sha256 = hashlib.sha256(compressed).hexdigest()
    if path.exists():
        if gzip.decompress(path.read_bytes()) != encoded:
            raise FactMaterializationError("facts_snapshot_digest_mismatch")
        return digest, artifact_sha256
    fd, temp_name = tempfile.mkstemp(prefix=f"{digest}.", suffix=".tmp", dir=path.parent)
    try:
        with os.fdopen(fd, "wb") as output:
            output.write(compressed)
            output.flush()
            os.fsync(output.fileno())
        os.replace(temp_name, path)
    except BaseException:
        try:
            os.unlink(temp_name)
        except OSError:
            pass
        raise
    return digest, artifact_sha256


def load_fact_set(workspace_dir: Path, manifest: Mapping[str, Any]) -> dict[str, Any]:
    digest = str(manifest.get("content_hash") or "")
    try:
        payload = json.loads(gzip.decompress(
            _fact_artifact_path(workspace_dir, digest).read_bytes()
        ).decode("utf-8"))
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        raise FactMaterializationError("facts_snapshot_digest_mismatch") from exc
    if content_hash(payload) != digest:
        raise FactMaterializationError("facts_snapshot_digest_mismatch")
    for key in (
        "project_id", "attempt_id", "mapping_revision", "source_revision_id",
        "snapshot_id", "table_name", "row_fact_count", "value_fact_count",
    ):
        if payload.get(key) != manifest.get(key):
            raise FactMaterializationError("facts_snapshot_digest_mismatch")
    return payload


def _fact_sets_available(
    store: Store,
    workspace_dir: Path,
    payload: Mapping[str, Any],
) -> bool:
    fact_set_ids = payload.get("fact_set_ids") or ()
    summary = payload.get("summary") or {}
    if not fact_set_ids or len(fact_set_ids) != int(summary.get("tables") or 0):
        return False
    for fact_set_id in fact_set_ids:
        persisted = store.get_domain_object(FACT_SET_KIND, str(fact_set_id))
        if persisted is None or not isinstance(persisted[1], Mapping):
            return False
        manifest = persisted[1]
        artifact_path = _fact_artifact_path(
            workspace_dir, str(manifest.get("content_hash") or "")
        )
        try:
            artifact_sha256 = hashlib.sha256(artifact_path.read_bytes()).hexdigest()
        except OSError:
            return False
        if (
            manifest.get("fact_set_id") != fact_set_id
            or manifest.get("project_id") != payload.get("project_id")
            or manifest.get("attempt_id") != payload.get("attempt_id")
            or manifest.get("mapping_revision") != payload.get("mapping_revision")
            or artifact_sha256 != manifest.get("artifact_sha256")
        ):
            return False
    return True


def locator_from_fact(
    fact_set: Mapping[str, Any], row_fact: Mapping[str, Any], value_fact: Mapping[str, Any]
) -> SourceCellLocator:
    """Reconstruct the complete exact locator from one compact fact bundle."""
    return SourceCellLocator(
        project_id=str(fact_set["project_id"]),
        source_revision_id=str(fact_set["source_revision_id"]),
        snapshot_id=str(fact_set["snapshot_id"]),
        source_file=str(fact_set["source_file"]),
        source_file_digest=str(fact_set["source_file_digest"]),
        table_name=str(fact_set["table_name"]),
        row_index=int(row_fact["row_index"]),
        row_number=int(row_fact["row_number"]),
        column=str(value_fact["source_field"]),
        column_index=int(value_fact["column_index"]),
        raw_value=value_fact["raw_value"],
        locator_id=str(value_fact["locator_id"]),
    )


def _advance(store: Store, snapshot_id: str, target: SnapshotAcceptanceState) -> None:
    current = store.get_acceptance(snapshot_id)
    while current.state != target:
        index = ACCEPTANCE_CHAIN.index(current.state)
        target_index = ACCEPTANCE_CHAIN.index(target)
        if index > target_index:
            return
        current = store.transition_snapshot_acceptance(
            snapshot_id,
            ACCEPTANCE_CHAIN[index + 1],
            accepted_by=ACCEPTED_BY_SYSTEM_POLICY,
            reason="字段对应已确认，确定性校验通过。",
        )


@dataclass(frozen=True)
class FactMaterializationService:
    mapping_repository: ConfirmedMappingRepository

    def _confirmed_revision(self, project_id: str, attempt_id: str) -> dict[str, Any]:
        draft = self.mapping_repository.find_draft_for_batch(project_id, attempt_id)
        if draft is None:
            raise FactMaterializationError("facts_mapping_not_confirmed")
        draft_payload = _payload(draft)
        if str(draft_payload.get("status")) != "confirmed":
            raise FactMaterializationError("facts_mapping_not_confirmed")
        revision_id = str(draft_payload.get("confirmed_revision_id") or "")
        if not revision_id:
            raise FactMaterializationError("facts_mapping_not_confirmed")
        revision = _payload(self.mapping_repository.get_revision(project_id, revision_id))
        if str(revision.get("batch_id")) != attempt_id:
            raise FactMaterializationError("facts_mapping_conflict")
        return revision

    @staticmethod
    def _record(store: Store, project_id: str, attempt_id: str) -> dict[str, Any]:
        persisted = store.get_domain_object(ADMISSION_RECORD_KIND, attempt_id)
        if persisted is None or not isinstance(persisted[1], Mapping):
            raise FactMaterializationError("facts_admission_not_found")
        record = dict(persisted[1])
        if record.get("project_id") != project_id or record.get("state") != "profile_ready":
            raise FactMaterializationError("facts_admission_not_found")
        return record

    @staticmethod
    def _locator(
        index: Mapping[str, Any], row: Mapping[str, Any], row_index: int, column_index: int
    ) -> SourceCellLocator:
        columns = tuple(index.get("columns") or ())
        row_numbers = tuple(index.get("row_numbers") or ())
        if row_index >= len(row_numbers) or column_index >= len(columns):
            raise FactMaterializationError("facts_locator_invalid")
        locator = SourceCellLocator(
            project_id=str(index["project_id"]),
            source_revision_id=str(index["source_revision_id"]),
            snapshot_id=str(index["snapshot_id"]),
            source_file=str(index["source_file"]),
            source_file_digest=str(index["source_file_digest"]),
            table_name=str(index["table_name"]),
            row_index=row_index,
            row_number=int(row_numbers[row_index]),
            column=str(columns[column_index]),
            column_index=column_index,
            raw_value=row[columns[column_index]],
        )
        expected = index.get("locator_ids") or ()
        offset = row_index * len(columns) + column_index
        if offset >= len(expected) or expected[offset] != locator.locator_id:
            raise FactMaterializationError("facts_locator_invalid")
        return locator

    def materialize(
        self, *, project_id: str, attempt_id: str, workspace_dir: Path
    ) -> Mapping[str, Any]:
        store = _store(workspace_dir)
        try:
            record = self._record(store, project_id, attempt_id)
            revision = self._confirmed_revision(project_id, attempt_id)
            mapping_revision = str(revision["mapping_revision"])
            existing = store.get_domain_object(FACT_MATERIALIZATION_KIND, attempt_id)
            if existing is not None and isinstance(existing[1], Mapping):
                existing_payload = dict(existing[1])
                if (
                    existing_payload.get("project_id") == project_id
                    and existing_payload.get("mapping_revision") == mapping_revision
                    and existing_payload.get("state") == "ready"
                    and _fact_sets_available(store, workspace_dir, existing_payload)
                ):
                    return self._public(existing_payload)
            fields_by_domain: dict[str, dict[str, dict[str, Any]]] = {}
            for raw_field in revision.get("fields") or ():
                field = _payload(raw_field)
                fields_by_domain.setdefault(str(field["domain"]).casefold(), {})[
                    str(field["source_field"])
                ] = field

            technical = dict(record.get("technical_details") or {})
            source_digests: dict[str, str] = {}
            for item in technical.get("files") or ():
                path = str(item.get("path") or "")
                digest = str(item.get("sha256") or "")
                source_digests[path] = digest
                name = Path(path).name
                if name not in source_digests:
                    source_digests[name] = digest
                elif source_digests[name] != digest:
                    source_digests[name] = ""
            fact_set_manifests = []
            skipped_unmapped = 0
            skipped_derived = 0
            value_count = 0
            row_count = 0
            for snapshot_id in technical.get("snapshot_ids") or ():
                snapshot = store.get_listing_snapshot(str(snapshot_id))
                if snapshot.project_id != project_id:
                    raise FactMaterializationError("facts_mapping_conflict")
                content = store.load_listing_content(snapshot.snapshot_id)
                if content_hash(content) != snapshot.content_hash:
                    raise FactMaterializationError("facts_snapshot_digest_mismatch")
                persisted_index = store.get_domain_object(LOCATOR_INDEX_KIND, snapshot.snapshot_id)
                if persisted_index is None or not isinstance(persisted_index[1], Mapping):
                    raise FactMaterializationError("facts_locator_invalid")
                index = dict(persisted_index[1])
                table_name = str(index.get("table_name") or "")
                rows = content.get(table_name)
                columns = tuple(index.get("columns") or ())
                if (
                    index.get("project_id") != project_id
                    or index.get("source_revision_id") != snapshot.revision_id
                    or index.get("snapshot_id") != snapshot.snapshot_id
                    or source_digests.get(str(index.get("source_file")))
                    != index.get("source_file_digest")
                    or not isinstance(rows, list)
                    or len(rows) != snapshot.row_count
                    or len(index.get("locator_ids") or ()) != len(rows) * len(columns)
                ):
                    raise FactMaterializationError("facts_locator_invalid")
                domain_fields = fields_by_domain.get(table_name.casefold())
                if domain_fields is None or set(domain_fields) != set(columns):
                    raise FactMaterializationError("facts_mapping_incomplete")

                row_facts = []
                for row_index, row in enumerate(rows):
                    values = []
                    for column_index, column in enumerate(columns):
                        field = domain_fields[column]
                        field_kind = str(field.get("field_kind") or "")
                        if field_kind == "unmapped":
                            skipped_unmapped += 1
                            continue
                        if field_kind == "deterministic_derived":
                            skipped_derived += 1
                            continue
                        locator = self._locator(index, row, row_index, column_index)
                        resolved = resolve_locator(
                            locator, content,
                            expected_locator_id=locator.locator_id,
                            context_rows=0,
                        )
                        normalized = normalize_value(
                            resolved.raw_value,
                            hint=f"{column} {field.get('recommended_role') or ''}",
                        )
                        values.append({
                            "source_field": column,
                            "column_index": column_index,
                            "canonical_role": str(field.get("recommended_role") or ""),
                            "field_kind": field_kind,
                            **normalized.canonical_payload(),
                            "locator_id": locator.locator_id,
                        })
                    if not values:
                        continue
                    identity = {
                        "project_id": project_id,
                        "snapshot_id": snapshot.snapshot_id,
                        "table_name": table_name,
                        "row_index": row_index,
                        "row_number": int(index["row_numbers"][row_index]),
                    }
                    row_facts.append({
                        "fact_id": "factc3_" + content_hash({
                            "recipe_version": FACT_SET_SCHEMA_VERSION,
                            "mapping_revision": mapping_revision,
                            "identity": identity,
                            "values": values,
                        })[:32],
                        "row_index": row_index,
                        "row_number": int(index["row_numbers"][row_index]),
                        "values": values,
                    })
                    value_count += len(values)
                row_count += len(row_facts)
                fact_set = {
                    "schema_version": FACT_SET_SCHEMA_VERSION,
                    "project_id": project_id,
                    "attempt_id": attempt_id,
                    "mapping_revision": mapping_revision,
                    "source_revision_id": snapshot.revision_id,
                    "snapshot_id": snapshot.snapshot_id,
                    "source_file": str(index["source_file"]),
                    "source_file_digest": str(index["source_file_digest"]),
                    "table_name": table_name,
                    "row_facts": row_facts,
                    "row_fact_count": len(row_facts),
                    "value_fact_count": sum(len(item["values"]) for item in row_facts),
                }
                fact_set_id = "mmfactset_" + content_hash(fact_set)[:32]
                _advance(
                    store,
                    snapshot.snapshot_id,
                    SnapshotAcceptanceState.SNAPSHOT_ACCEPTED,
                )
                digest, artifact_sha256 = _write_fact_artifact(workspace_dir, fact_set)
                manifest = {
                    "schema_version": FACT_SET_SCHEMA_VERSION,
                    "project_id": project_id,
                    "attempt_id": attempt_id,
                    "mapping_revision": mapping_revision,
                    "source_revision_id": fact_set["source_revision_id"],
                    "snapshot_id": fact_set["snapshot_id"],
                    "table_name": fact_set["table_name"],
                    "fact_set_id": fact_set_id,
                    "content_hash": digest,
                    "artifact_sha256": artifact_sha256,
                    "row_fact_count": fact_set["row_fact_count"],
                    "value_fact_count": fact_set["value_fact_count"],
                }
                store.put_domain_object(FACT_SET_KIND, fact_set_id, manifest)
                fact_set_manifests.append(manifest)
                _advance(
                    store,
                    snapshot.snapshot_id,
                    SnapshotAcceptanceState.BASELINE_ELIGIBLE,
                )

            if len(fact_set_manifests) != len(technical.get("snapshot_ids") or ()):
                raise FactMaterializationError("facts_snapshot_incomplete")

            summary = {
                "schema_version": FACT_MATERIALIZATION_SCHEMA_VERSION,
                "project_id": project_id,
                "attempt_id": attempt_id,
                "mapping_revision": mapping_revision,
                "state": "ready",
                "summary": {
                    "tables": len(fact_set_manifests),
                    "rows": row_count,
                    "values": value_count,
                    "unmapped_values_skipped": skipped_unmapped,
                    "derived_values_skipped": skipped_derived,
                },
                "fact_set_ids": [item["fact_set_id"] for item in fact_set_manifests],
            }
            store.put_domain_object(FACT_MATERIALIZATION_KIND, attempt_id, summary)
            return self._public(summary)
        except FactMaterializationError:
            raise
        except Exception as exc:
            raise FactMaterializationError("facts_generation_failed") from exc
        finally:
            store.close()

    def status(
        self, *, project_id: str, attempt_id: str, workspace_dir: Path
    ) -> Mapping[str, Any]:
        store = _store(workspace_dir)
        try:
            self._record(store, project_id, attempt_id)
            persisted = store.get_domain_object(FACT_MATERIALIZATION_KIND, attempt_id)
            if persisted is None:
                return {"state": "not_generated", "facts_generated": False}
            payload = dict(persisted[1])
            if payload.get("project_id") != project_id:
                raise FactMaterializationError("facts_admission_not_found")
            if payload.get("state") == "ready" and not _fact_sets_available(
                store, workspace_dir, payload
            ):
                raise FactMaterializationError("facts_snapshot_digest_mismatch")
            return self._public(payload)
        finally:
            store.close()

    @staticmethod
    def _public(payload: Mapping[str, Any]) -> dict[str, Any]:
        ready = payload.get("state") == "ready"
        return {
            "state": payload.get("state", "not_generated"),
            "facts_generated": ready,
            "summary": dict(payload.get("summary") or {}),
            "message": (
                "可用于监查的数据已生成，可以开始监查。"
                if ready else "可用于监查的数据尚未生成。"
            ),
        }


def latest_fact_materialization_ready(project_id: str, workspace_dir: Path) -> bool:
    """Return true only when the newest admitted attempt has a verified ready summary."""
    try:
        admission_dir = Path(workspace_dir) / "admissions"
        attempts = [
            load_attempt(admission_dir, attempt_id, verify_files=False)
            for attempt_id in list_attempt_ids(admission_dir)
        ]
        if not attempts:
            return False
        latest = max(attempts, key=lambda item: (item.created_at, item.attempt_id))
        store = _store(workspace_dir)
        try:
            persisted = store.get_domain_object(
                FACT_MATERIALIZATION_KIND, latest.attempt_id
            )
            return bool(
                persisted
                and isinstance(persisted[1], Mapping)
                and persisted[1].get("project_id") == project_id
                and persisted[1].get("state") == "ready"
                and _fact_sets_available(store, workspace_dir, persisted[1])
            )
        finally:
            store.close()
    except Exception:
        return False
