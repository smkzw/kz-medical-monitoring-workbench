"""Synthetic export / import / backup / restore / rollback for the R2 kernel
(Batch C).

Proves user data can be moved and restored without losing current
publication, history, or identities.  This is a functional data-mobility /
recovery mechanism:

* :meth:`Migration.export_snapshot` serializes a store's committed state +
  artifact bytes to a single canonical JSON archive.
* :meth:`Migration.import_snapshot` rebuilds a new store from the archive,
  preserving revisions, the publication pointer, history, audit chain, and
  identities.
* :meth:`Migration.backup` and :meth:`Migration.restore` copy the live
  SQLite DB + artifact directory so a restore lands the exact bytes.
* :meth:`Migration.rollback` wraps the store's publication-pointer rollback.

No deletion, schema attack, signature, access-control, tamper-red-team, or
security certification work (per user directive).  Hashes are functional
data-integrity mechanisms.
"""

from __future__ import annotations

import json
import os
import shutil
import sqlite3
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

from .audit import AuditChain
from .artifacts import ArtifactCompleteness
from .domain import (
    MmR2Error,
    canonical_json,
    content_hash,
    new_id,
    now_iso,
    sha256_hex,
    to_dictable,
)
from .store import R2Store, StoreError

__all__ = [
    "MigrationError",
    "MigrationArchive",
    "Migration",
]

# Tables that are exported/imported in canonical order so the rebuilt store
# is internally consistent.  Order matters for FK relationships.
_EXPORT_TABLES = (
    "r2_publication_revisions",
    "r2_publication_pointer",
    "r2_idempotency_ledger",
    "r2_artifact_refs",
    "r2_audit_events",
    "r2_audit_chain_head",
    "r2_meta",
)


class MigrationError(MmR2Error):
    """A migration / export / import / restore violation."""


@dataclass(frozen=True)
class MigrationArchive:
    """An in-memory canonical archive of one store's committed state.

    ``archive_hash`` is the content hash of the canonical archive payload so
    an import can prove it landed the same bytes it exported.
    """

    store_id: str
    exported_at: str
    tables: Dict[str, List[Dict[str, Any]]]
    artifacts: Dict[str, str]   # content_hash -> hex bytes
    archive_hash: str


class Migration:
    """Export / import / backup / restore / rollback for :class:`R2Store`."""

    ARCHIVE_TYPE = "r2_migration_archive"
    ARCHIVE_VERSION = "1"

    # -- export / import ---------------------------------------------------

    @staticmethod
    def export_snapshot(store: R2Store) -> MigrationArchive:
        """Serialize the store's committed state + artifact bytes.

        Every artifact referenced by a committed revision is read + verified
        and included as hex bytes.  The archive hash binds the full canonical
        payload so an import can prove fidelity.
        """
        conn = store._conn  # noqa: SLF001 -- export reads the live connection
        tables: Dict[str, List[Dict[str, Any]]] = {}
        for table in _EXPORT_TABLES:
            rows = list(conn.execute(f"SELECT * FROM {table}").fetchall())
            tables[table] = [
                {k: row[k] for k in row.keys()} for row in rows
            ]
        # Collect every artifact content_hash referenced by revisions.
        artifacts: Dict[str, str] = {}
        for row in conn.execute(
            "SELECT DISTINCT content_hash FROM r2_publication_revisions"
        ).fetchall():
            ch = row["content_hash"]
            data = store.read_artifact(ch)
            artifacts[ch] = data.hex()
        store_id = conn.execute(
            "SELECT value FROM r2_meta WHERE key='store_id'"
        ).fetchone()["value"]
        exported_at = now_iso()
        # The archive hash binds the stable data (store_id, tables, artifacts)
        # but NOT exported_at, which changes on every export and would make
        # verify_import always fail.
        archive_hash = content_hash({
            "archive_type": Migration.ARCHIVE_TYPE,
            "archive_version": Migration.ARCHIVE_VERSION,
            "store_id": store_id,
            "tables": tables,
            "artifacts": artifacts,
        })
        return MigrationArchive(
            store_id=store_id,
            exported_at=exported_at,
            tables=tables,
            artifacts=artifacts,
            archive_hash=archive_hash,
        )

    @staticmethod
    def import_snapshot(
        archive: MigrationArchive,
        db_path: Path,
        artifact_dir: Path,
        *,
        local_user: Optional[str] = None,
    ) -> R2Store:
        """Rebuild a store from an archive.

        The new store lands the same revisions, publication pointer,
        idempotency ledger, audit chain, and artifact bytes.  After import,
        :meth:`R2Store.dashboard_inputs` returns the same current published
        state as the source.
        """
        expected_archive_hash = content_hash({
            "archive_type": Migration.ARCHIVE_TYPE,
            "archive_version": Migration.ARCHIVE_VERSION,
            "store_id": archive.store_id,
            "tables": archive.tables,
            "artifacts": archive.artifacts,
        })
        if expected_archive_hash != archive.archive_hash:
            raise MigrationError(
                "migration archive hash mismatch; import source is incomplete "
                "or inconsistent"
            )
        db_path = Path(db_path)
        artifact_dir = Path(artifact_dir)
        if db_path.exists():
            raise MigrationError(
                f"migration import requires a fresh database target: {db_path}"
            )
        if artifact_dir.exists() and any(artifact_dir.iterdir()):
            raise MigrationError(
                "migration import requires an empty artifact target"
            )
        revisions = archive.tables.get("r2_publication_revisions", [])
        revision_ids = [int(row["revision"]) for row in revisions]
        if len(set(revision_ids)) != len(revision_ids):
            raise MigrationError("migration archive has duplicate revision identities")
        revision_by_id = {int(row["revision"]): row for row in revisions}
        artifact_ref_rows = archive.tables.get("r2_artifact_refs", [])
        artifact_ids = [row.get("artifact_id") for row in artifact_ref_rows]
        artifact_hashes = [row.get("content_hash") for row in artifact_ref_rows]
        if (
            len(set(artifact_ids)) != len(artifact_ids)
            or len(set(artifact_hashes)) != len(artifact_hashes)
        ):
            raise MigrationError(
                "migration archive has duplicate artifact-reference identities"
            )
        artifact_refs = {
            (row.get("artifact_id"), row.get("content_hash")): row
            for row in artifact_ref_rows
        }
        missing_artifacts = sorted({
            row.get("content_hash", "") for row in revisions
            if row.get("content_hash", "") not in archive.artifacts
        })
        if missing_artifacts:
            raise MigrationError(
                "migration archive is missing artifacts referenced by committed "
                f"revisions: {missing_artifacts}"
            )
        missing_refs = sorted({
            (row.get("artifact_id", ""), row.get("content_hash", ""))
            for row in revisions
            if (row.get("artifact_id"), row.get("content_hash"))
            not in artifact_refs
        })
        if missing_refs:
            raise MigrationError(
                "migration archive has committed revisions without matching "
                f"artifact references: {missing_refs}"
            )
        pointer_rows = archive.tables.get("r2_publication_pointer", [])
        pointer_projects_list = [row.get("project_id") for row in pointer_rows]
        if len(set(pointer_projects_list)) != len(pointer_projects_list):
            raise MigrationError(
                "migration archive has more than one current publication pointer "
                "for a project"
            )
        for pointer in pointer_rows:
            revision = revision_by_id.get(int(pointer["current_revision"]))
            if (
                revision is None
                or revision.get("project_id") != pointer.get("project_id")
                or not int(revision.get("published", 0))
                or revision.get("completeness") != ArtifactCompleteness.COMPLETE
            ):
                raise MigrationError(
                    "migration archive publication pointer does not resolve to "
                    "a completed published revision"
                )
        published_projects = {
            row.get("project_id") for row in revisions
            if int(row.get("published", 0))
        }
        pointer_projects = {
            row.get("project_id") for row in pointer_rows
        }
        if published_projects != pointer_projects:
            raise MigrationError(
                "migration archive does not preserve one current publication "
                "pointer for every project with published history"
            )
        ledger_rows = archive.tables.get("r2_idempotency_ledger", [])
        ledger_keys = [row.get("idempotency_key") for row in ledger_rows]
        if len(set(ledger_keys)) != len(ledger_keys):
            raise MigrationError("migration archive has duplicate idempotency keys")
        ledger_by_key = {row.get("idempotency_key"): row for row in ledger_rows}
        revision_keys = [row.get("idempotency_key") for row in revisions]
        if (
            any(not key for key in revision_keys)
            or any(not row.get("request_hash") for row in revisions)
            or len(set(revision_keys)) != len(revision_keys)
            or set(revision_keys) != set(ledger_by_key)
        ):
            raise MigrationError(
                "migration archive idempotency keys do not bind revision history "
                "exactly"
            )
        ledger_revisions: List[int] = []
        for revision in revisions:
            row = ledger_by_key[revision["idempotency_key"]]
            try:
                result = json.loads(row["result_json"])
                required_result_fields = {
                    "revision", "artifact_id", "content_hash", "published",
                    "idempotent_replay", "saved_at",
                }
                if not required_result_fields.issubset(result):
                    raise KeyError("incomplete idempotency result")
                ledger_revision = int(result["revision"])
            except (KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
                raise MigrationError(
                    "migration archive has an invalid idempotency result"
                ) from exc
            ledger_revisions.append(ledger_revision)
            expected_scope = f"save:{revision['project_id']}:{revision['run_id']}"
            if (
                row.get("scope") != expected_scope
                or row.get("request_hash") != revision.get("request_hash")
                or result.get("artifact_id") != revision.get("artifact_id")
                or result.get("content_hash") != revision.get("content_hash")
                or bool(result.get("published")) != bool(revision.get("published"))
                or bool(result.get("idempotent_replay"))
                or result.get("saved_at") != revision.get("saved_at")
                or ledger_revision != int(revision["revision"])
            ):
                raise MigrationError(
                    "migration archive idempotency key/request/result binding is "
                    "inconsistent"
                )
        committed_revisions = sorted(revision_by_id)
        if sorted(ledger_revisions) != committed_revisions:
            raise MigrationError(
                "migration archive idempotency ledger does not cover committed "
                "revision history exactly"
            )
        decoded_artifacts: Dict[str, bytes] = {}
        artifact_contracts: Dict[str, Dict[str, Any]] = {}
        for content_hash_value, hex_bytes in archive.artifacts.items():
            try:
                data = bytes.fromhex(hex_bytes)
                contract = json.loads(data.decode("utf-8"))
            except (TypeError, ValueError, UnicodeDecodeError, json.JSONDecodeError) as exc:
                raise MigrationError(
                    f"archive artifact {content_hash_value!r} is not valid JSON bytes"
                ) from exc
            actual = sha256_hex(data)
            if actual != content_hash_value:
                raise MigrationError(
                    f"archive artifact hash mismatch for {content_hash_value!r}: "
                    f"recomputed {actual!r}"
                )
            if not isinstance(contract, dict):
                raise MigrationError(
                    f"archive artifact {content_hash_value!r} has no object contract"
                )
            decoded_artifacts[content_hash_value] = data
            artifact_contracts[content_hash_value] = contract
        for revision in revisions:
            ref = artifact_refs[(revision["artifact_id"], revision["content_hash"])]
            contract = artifact_contracts[revision["content_hash"]]
            try:
                envelope = json.loads(ref["envelope_json"])
                if not isinstance(envelope, dict):
                    raise TypeError("artifact envelope is not an object")
                envelope_fields = envelope.get("fields", envelope)
                if not isinstance(envelope_fields, dict):
                    raise TypeError("artifact envelope fields are not an object")
            except (TypeError, json.JSONDecodeError) as exc:
                raise MigrationError(
                    "migration archive has an invalid artifact envelope"
                ) from exc
            if (
                ref.get("run_id") != revision.get("run_id")
                or ref.get("artifact_type") != R2Store.ARTIFACT_TYPE
                or ref.get("completeness") != revision.get("completeness")
                or contract.get("artifact_type") != R2Store.ARTIFACT_TYPE
                or contract.get("completeness") != revision.get("completeness")
                or contract.get("input_hash") != revision.get("request_hash")
                or envelope_fields.get("artifact_id") != revision.get("artifact_id")
                or envelope_fields.get("content_hash") != revision.get("content_hash")
                or envelope_fields.get("input_hash") != revision.get("request_hash")
                or envelope_fields.get("completeness") != revision.get("completeness")
            ):
                raise MigrationError(
                    "migration archive artifact bytes, envelope, reference, and "
                    "revision are inconsistent"
                )
        saved_events: Dict[int, Dict[str, Any]] = {}
        advanced_events: Dict[int, Dict[str, Any]] = {}
        for event in archive.tables.get("r2_audit_events", []):
            try:
                payload = json.loads(event["payload_json"])
            except (KeyError, TypeError, json.JSONDecodeError) as exc:
                raise MigrationError(
                    "migration archive has an invalid business-history event"
                ) from exc
            if event.get("event_type") == "result_saved":
                revision_id = int(payload.get("revision", -1))
                if revision_id in saved_events:
                    raise MigrationError(
                        "migration archive has duplicate result_saved history"
                    )
                saved_events[revision_id] = payload
            elif event.get("event_type") == "publication_advanced":
                revision_id = int(payload.get("revision", -1))
                if revision_id in advanced_events:
                    raise MigrationError(
                        "migration archive has duplicate publication_advanced history"
                    )
                advanced_events[revision_id] = payload
        if set(saved_events) != set(revision_by_id):
            raise MigrationError(
                "migration archive business history does not cover committed "
                "revisions exactly"
            )
        published_revision_ids = {
            int(row["revision"]) for row in revisions if int(row.get("published", 0))
        }
        if set(advanced_events) != published_revision_ids:
            raise MigrationError(
                "migration archive publication history does not match published "
                "revisions"
            )
        for revision_id, revision in revision_by_id.items():
            payload = saved_events[revision_id]
            if any((
                payload.get("run_id") != revision.get("run_id"),
                payload.get("project_id") != revision.get("project_id"),
                payload.get("snapshot_id") != revision.get("snapshot_id"),
                payload.get("artifact_id") != revision.get("artifact_id"),
                payload.get("content_hash") != revision.get("content_hash"),
                payload.get("completeness") != revision.get("completeness"),
                payload.get("baseline_id", "") != revision.get("baseline_id", ""),
                payload.get("actor", "") != revision.get("actor", ""),
                payload.get("note", "") != revision.get("note", ""),
            )):
                raise MigrationError(
                    "migration archive result_saved history is inconsistent with "
                    f"revision {revision_id}"
                )
        # Write artifact bytes FIRST (content-addressed, hash-verified).
        astore_dir = artifact_dir
        astore_dir.mkdir(parents=True, exist_ok=True)
        for content_hash_value, data in decoded_artifacts.items():
            # Write via a minimal content-addressed layout (same as ArtifactStore).
            shard = astore_dir / content_hash_value[:2]
            shard.mkdir(parents=True, exist_ok=True)
            (shard / content_hash_value).write_bytes(data)

        # Create the new store (applies schema).
        store = R2Store(db_path, artifact_dir, local_user=local_user)
        conn = store._conn  # noqa: SLF001 -- import writes the live connection

        def _rebuild():
            # Preserve the source store_id (overwrite the freshly-seeded one).
            conn.execute(
                "UPDATE r2_meta SET value=? WHERE key='store_id'",
                (archive.store_id,),
            )
            for table in _EXPORT_TABLES:
                rows = archive.tables.get(table, [])
                if not rows:
                    continue
                # r2_audit_chain_head has a singleton PK; clear + reinsert so
                # the source head replaces the freshly-seeded genesis.
                if table == "r2_audit_chain_head":
                    conn.execute("DELETE FROM r2_audit_chain_head")
                # r2_meta: skip store_id (already set); merge the rest.
                if table == "r2_meta":
                    for row in rows:
                        if row["key"] == "store_id":
                            continue
                        conn.execute(
                            "INSERT INTO r2_meta(key, value) VALUES (?,?)"
                            " ON CONFLICT(key) DO UPDATE SET value=excluded.value",
                            (row["key"], row["value"]),
                        )
                    continue
                cols = list(rows[0].keys())
                placeholders = ",".join("?" for _ in cols)
                col_list = ",".join(cols)
                for row in rows:
                    conn.execute(
                        f"INSERT INTO {table}({col_list}) VALUES ({placeholders})",
                        tuple(row[c] for c in cols),
                    )

        try:
            conn.execute("BEGIN IMMEDIATE")
            _rebuild()
            if not store.audit.verify_chain():
                raise MigrationError(
                    "migration archive contains an inconsistent audit chain"
                )
            conn.execute("COMMIT")
        except BaseException:
            try:
                conn.execute("ROLLBACK")
            except sqlite3.Error:
                pass
            store.close()
            raise
        return store

    @staticmethod
    def verify_import(store: R2Store, archive: MigrationArchive) -> bool:
        """Return True iff the store's state reproduces the archive hash."""
        re = Migration.export_snapshot(store)
        return re.archive_hash == archive.archive_hash

    # -- backup / restore (byte-level copy) -------------------------------

    @staticmethod
    def backup(store: R2Store, backup_dir: Path) -> Path:
        """Copy the live DB + artifacts to ``backup_dir``.  Returns the path.

        The store is closed first so the WAL is checkpointed into the main
        DB file, then both files are copied.  A restore lands the exact
        bytes.
        """
        backup_dir = Path(backup_dir)
        backup_dir.mkdir(parents=True, exist_ok=True)
        store.close()
        # Checkpoint WAL into the main db file before copying.
        # (store is closed; reopen read-only to checkpoint.)
        conn = sqlite3.connect(str(store.db_path))
        try:
            conn.execute("PRAGMA wal_checkpoint(TRUNCATE)")
        finally:
            conn.close()
        db_dest = backup_dir / store.db_path.name
        shutil.copy2(store.db_path, db_dest)
        # Copy the artifact dir.
        art_dest = backup_dir / "artifacts"
        if art_dest.exists():
            shutil.rmtree(art_dest)
        shutil.copytree(store.artifact_dir, art_dest)
        return backup_dir

    @staticmethod
    def restore(
        backup_dir: Path, db_path: Path, artifact_dir: Path,
        *,
        local_user: Optional[str] = None,
    ) -> R2Store:
        """Restore a store from a backup directory.  Lands the exact bytes."""
        backup_dir = Path(backup_dir)
        # The backup stores the DB under its original filename; find it.
        db_files = sorted(backup_dir.glob("*.db"))
        if not db_files:
            raise MigrationError(f"no backup db found in {backup_dir}")
        db_src = db_files[0]
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(db_src, db_path)
        art_src = backup_dir / "artifacts"
        if art_src.exists():
            if Path(artifact_dir).exists():
                shutil.rmtree(artifact_dir)
            shutil.copytree(art_src, artifact_dir)
        return R2Store(db_path, artifact_dir, local_user=local_user)

    # -- rollback (delegates to store) ------------------------------------

    @staticmethod
    def rollback(
        store: R2Store, project_id: str, target_revision: int, *, actor: str,
    ) -> int:
        return store.rollback_to_published_revision(
            project_id, target_revision, actor=actor,
        )
