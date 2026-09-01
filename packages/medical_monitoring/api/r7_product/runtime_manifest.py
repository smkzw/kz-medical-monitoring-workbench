"""Runtime-manifest identity and read-only audit helpers for publication."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Optional

from ...domain.execution import content_hash, to_jsonable
from ...graph.store import Store
from ...runtime.runtime_progress import ARTIFACT_DIR_NAME, RUNTIME_DB_NAME, RUNTIME_DIR_NAME
from .contracts import ProductPublicationError


def _publication_manifest_identity(manifest: Any) -> dict[str, Any]:
    """Return the cross-manifest identity subset frozen by 07C-3."""
    units = getattr(manifest, "work_units", None)
    if units is None:
        units = getattr(manifest, "units", None)
    values: list[dict[str, Any]] = []
    seen: set[str] = set()
    for unit in units:
        work_unit_id = getattr(unit, "work_unit_id", None)
        mandatory = getattr(unit, "mandatory", None)
        if (
            not isinstance(work_unit_id, str)
            or not work_unit_id.strip()
            or not isinstance(mandatory, bool)
            or work_unit_id in seen
        ):
            raise ProductPublicationError("manifest_identity_mismatch")
        seen.add(work_unit_id)
        values.append({"work_unit_id": work_unit_id, "mandatory": mandatory})
    values.sort(key=lambda item: item["work_unit_id"])
    return {
        "work_units": values,
        "mandatory_denominator": sum(bool(item["mandatory"]) for item in values),
    }


def _runtime_manifest_digest(manifest: Any) -> str:
    try:
        return content_hash(to_jsonable(manifest))
    except Exception as exc:
        raise ProductPublicationError("manifest_identity_mismatch") from exc


def _runtime_manifest_metadata(
    workspace: Path,
    run_id: str,
) -> Optional[dict[str, Any]]:
    """Read existing R1 manifest metadata without creating runtime state."""
    runtime_dir = workspace / RUNTIME_DIR_NAME
    db_path = runtime_dir / RUNTIME_DB_NAME
    artifact_dir = runtime_dir / ARTIFACT_DIR_NAME
    if not db_path.is_file() or not artifact_dir.is_dir():
        return None
    store: Optional[Store] = None
    try:
        store = Store(db_path, artifact_dir)
        run = store.get_run(run_id)
        revision = int(run.manifest_revision)
        if revision < 1:
            return None
        manifest = store.get_manifest(run_id, revision)
        if manifest is None:
            raise ProductPublicationError("runtime_read_failed", recoverable=True)
        return {
            "revision": revision,
            "manifest": manifest,
            "identity": _publication_manifest_identity(manifest),
            "digest": _runtime_manifest_digest(manifest),
        }
    except ProductPublicationError:
        raise
    except Exception as exc:
        raise ProductPublicationError("runtime_read_failed", recoverable=True) from exc
    finally:
        if store is not None:
            store.close()


def _runtime_audit_chain_is_invalid(workspace: Path, run_id: str) -> bool:
    """Detect audit corruption after a progress read fails closed."""
    runtime_dir = workspace / RUNTIME_DIR_NAME
    db_path = runtime_dir / RUNTIME_DB_NAME
    artifact_dir = runtime_dir / ARTIFACT_DIR_NAME
    if not db_path.is_file() or not artifact_dir.is_dir():
        return False
    store: Optional[Store] = None
    try:
        store = Store(db_path, artifact_dir)
        store.get_run(run_id)
        result = store.verify_audit_chain()
        return isinstance(result, tuple) and len(result) == 3 and result[0] is False
    except Exception:
        return False
    finally:
        if store is not None:
            store.close()


__all__ = [
    "_publication_manifest_identity",
    "_runtime_manifest_digest",
    "_runtime_manifest_metadata",
    "_runtime_audit_chain_is_invalid",
]
