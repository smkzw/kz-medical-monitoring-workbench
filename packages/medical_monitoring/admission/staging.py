"""Isolated staging-copy admission contract (Phase C C1, work item 1).

Copies read-only source listing files into an isolated workspace using only
the standard library.  The contract is the deterministic first seam of the
C1 data flow:

    只读原始 listing
      → 流式 SHA-256 + 文件清单
      → 逐文件复制进隔离暂存目录
      → 副本 SHA-256 独立复核
      → 原子改名为正式暂存批次

Invariants
----------

* The source tree is only ever opened for reading; the staging root is
  rejected if it sits inside the source tree, so staging can never write
  into the source.
* An attempt becomes visible only through one atomic directory rename after
  every file has been copied and every copy digest has been re-verified.
  In-progress copies live under ``<attempt_id>.tmp`` and are never
  loadable as attempts.
* ``manifest_hash`` is a content address over the file list only (paths,
  sizes, SHA-256 digests): re-staging the same source bytes yields the same
  hash regardless of attempt id or wall-clock time.  Retries create a new
  attempt id and never overwrite or reuse a previous attempt.
* ``load_attempt`` re-verifies the manifest address and, by default, every
  file digest on disk, so an interrupted or hash-mismatched copy is never
  accepted.

Hash helpers reuse the R2 domain authorities so staging manifests and
later ``SourceRevision`` bindings share one canonicalization.
"""

from __future__ import annotations

import hashlib
import json
import os
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Tuple

from ..domain.entities import (
    content_hash,
    new_id,
    now_iso,
    validate_sha256_hex,
)

__all__ = [
    "StagingError",
    "StagingSourceError",
    "StagingHashMismatchError",
    "StagingIncompleteError",
    "MANIFEST_NAME",
    "STAGING_SCHEMA_NAME",
    "STAGING_SCHEMA_VERSION",
    "StagedFile",
    "StagingAttempt",
    "sha256_file",
    "stage_copy",
    "load_attempt",
    "list_attempt_ids",
]

MANIFEST_NAME = "manifest.json"
STAGING_SCHEMA_NAME = "mm_staging_manifest"
STAGING_SCHEMA_VERSION = "1"

_CHUNK_SIZE = 1024 * 1024


class StagingError(Exception):
    """Base error for the staging-copy admission contract."""


class StagingSourceError(StagingError):
    """A requested source path is missing, not a regular file, or escapes
    the source root."""


class StagingHashMismatchError(StagingError):
    """The copy digest does not match the source digest."""


class StagingIncompleteError(StagingError):
    """An attempt directory is missing, has no verifiable manifest, or its
    files no longer match the manifest."""


def _fsync_dir(path: Path) -> None:
    try:
        fd = os.open(str(path), os.O_RDONLY)
    except OSError:
        return
    try:
        os.fsync(fd)
    except OSError:
        pass
    finally:
        os.close(fd)


def sha256_file(path: Path) -> Tuple[str, int]:
    """Stream *path* and return ``(sha256_hex, size)`` without buffering the
    whole file."""
    digest = hashlib.sha256()
    size = 0
    with open(path, "rb") as handle:
        while True:
            chunk = handle.read(_CHUNK_SIZE)
            if not chunk:
                break
            digest.update(chunk)
            size += len(chunk)
    return digest.hexdigest(), size


@dataclass(frozen=True)
class StagedFile:
    """One admitted file: source and copy verified byte-identical."""

    path: str   # relative POSIX-style path inside the attempt directory
    size: int
    sha256: str


def _manifest_address(files: Tuple[StagedFile, ...]) -> str:
    """Deterministic content address over the admitted file list only."""
    return content_hash({
        "schema": STAGING_SCHEMA_NAME,
        "version": STAGING_SCHEMA_VERSION,
        "files": [
            {"path": f.path, "size": f.size, "sha256": f.sha256}
            for f in files
        ],
    })


@dataclass(frozen=True)
class StagingAttempt:
    """A completed isolated staging attempt."""

    attempt_id: str
    source_root: str
    workspace_root: str
    files: Tuple[StagedFile, ...]
    manifest_hash: str
    created_at: str

    @property
    def path(self) -> Path:
        return _staging_root(Path(self.workspace_root)) / self.attempt_id

    def file_path(self, relative_path: str) -> Path:
        """Absolute path of one staged file inside the attempt directory."""
        return self.path / Path(relative_path)

    def manifest_payload(self) -> Dict[str, Any]:
        return {
            "schema": STAGING_SCHEMA_NAME,
            "version": STAGING_SCHEMA_VERSION,
            "attempt_id": self.attempt_id,
            "manifest_hash": self.manifest_hash,
            "source_root": self.source_root,
            "created_at": self.created_at,
            "files": [
                {"path": f.path, "size": f.size, "sha256": f.sha256}
                for f in self.files
            ],
        }


def _staging_root(workspace_root: Path) -> Path:
    return workspace_root / "staging"


def _resolve_relative_path(source_root: Path, relative_path: str) -> Path:
    candidate = Path(relative_path)
    if candidate.is_absolute():
        raise StagingSourceError(
            f"source path must be relative to the source root: {relative_path!r}"
        )
    resolved = (source_root / candidate).resolve()
    if not resolved.is_relative_to(source_root.resolve()):
        raise StagingSourceError(
            f"source path escapes the source root: {relative_path!r}"
        )
    if not resolved.is_file():
        raise StagingSourceError(
            f"source path is not a readable file: {relative_path!r}"
        )
    return resolved


def _copy_and_hash(source_file: Path, copy_file: Path) -> Tuple[str, int]:
    """Copy one file while hashing the source stream, then re-verify the
    copy with an independent read of what landed on disk."""
    source_digest = hashlib.sha256()
    size = 0
    with open(source_file, "rb") as src, open(copy_file, "wb") as dst:
        while True:
            chunk = src.read(_CHUNK_SIZE)
            if not chunk:
                break
            source_digest.update(chunk)
            size += len(chunk)
            dst.write(chunk)
        dst.flush()
        os.fsync(dst.fileno())
    copy_digest, copy_size = sha256_file(copy_file)
    if copy_digest != source_digest.hexdigest() or copy_size != size:
        raise StagingHashMismatchError(
            f"staged copy digest mismatch for {source_file.name}: "
            f"source {source_digest.hexdigest()!r} ({size} bytes) != "
            f"copy {copy_digest!r} ({copy_size} bytes)"
        )
    return copy_digest, size


def _write_manifest(attempt_dir: Path, payload: Dict[str, Any]) -> None:
    """Write the completion manifest inside the staging directory atomically
    (the directory itself is still named ``<attempt_id>.tmp`` here)."""
    encoded = json.dumps(
        payload, sort_keys=True, separators=(",", ":"),
        ensure_ascii=False, allow_nan=False,
    ).encode("utf-8")
    partial = attempt_dir / (MANIFEST_NAME + ".partial")
    with open(partial, "wb") as handle:
        handle.write(encoded)
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(str(partial), str(attempt_dir / MANIFEST_NAME))
    _fsync_dir(attempt_dir)


def _remove_tree(path: Path) -> None:
    shutil.rmtree(str(path), ignore_errors=True)


def stage_copy(
    source_root: Path,
    relative_paths: Iterable[str],
    workspace_root: Path,
    *,
    attempt_id: str = "",
) -> StagingAttempt:
    """Copy the requested source files into an isolated staging attempt.

    Only ``source_root`` reads happen; every byte written lands under
    ``workspace_root/staging``.  On success the attempt directory
    ``workspace_root/staging/<attempt_id>`` appears atomically with a
    verified ``manifest.json``.  Any failure removes the in-progress
    directory and raises; the source tree and any previous attempt are
    never touched.
    """
    root = Path(source_root)
    if not root.is_dir():
        raise StagingSourceError(f"source root is not a directory: {root}")
    workspace = Path(workspace_root)
    staging_root = _staging_root(workspace)
    if staging_root.resolve().is_relative_to(root.resolve()):
        raise StagingError(
            "staging root must live outside the source tree: "
            f"{staging_root} is inside {root}"
        )

    paths = list(relative_paths)
    if not paths:
        raise StagingError("no source files requested")
    ordered = sorted(set(paths))
    if len(ordered) != len(paths):
        raise StagingError("duplicate source paths requested")

    resolved_sources: List[Tuple[str, Path]] = [
        (rel, _resolve_relative_path(root, rel)) for rel in ordered
    ]

    final_id = attempt_id or new_id("stg-")
    final_dir = staging_root / final_id
    tmp_dir = staging_root / f"{final_id}.tmp"
    if final_dir.exists() or tmp_dir.exists():
        raise StagingError(
            f"staging attempt {final_id!r} already exists; a retry must use "
            f"a new attempt id and never overwrite a previous attempt"
        )
    staging_root.mkdir(parents=True, exist_ok=True)

    staged: List[StagedFile] = []
    try:
        for relative, source_file in resolved_sources:
            copy_file = tmp_dir / Path(relative)
            copy_file.parent.mkdir(parents=True, exist_ok=True)
            digest, size = _copy_and_hash(source_file, copy_file)
            staged.append(StagedFile(path=relative, size=size, sha256=digest))
        files = tuple(sorted(staged, key=lambda f: f.path))
        manifest_hash = _manifest_address(files)
        created_at = now_iso()
        _write_manifest(tmp_dir, StagingAttempt(
            attempt_id=final_id,
            source_root=str(root),
            workspace_root=str(workspace),
            files=files,
            manifest_hash=manifest_hash,
            created_at=created_at,
        ).manifest_payload())
        os.rename(str(tmp_dir), str(final_dir))
        _fsync_dir(staging_root)
    except BaseException:
        _remove_tree(tmp_dir)
        raise
    return StagingAttempt(
        attempt_id=final_id,
        source_root=str(root),
        workspace_root=str(workspace),
        files=files,
        manifest_hash=manifest_hash,
        created_at=created_at,
    )


def list_attempt_ids(workspace_root: Path) -> Tuple[str, ...]:
    """Attempt ids whose directories carry a manifest (visible completions).

    ``<id>.tmp`` directories are in-progress or failed attempts and are
    never listed.
    """
    staging_root = _staging_root(Path(workspace_root))
    if not staging_root.is_dir():
        return ()
    ids = []
    for entry in staging_root.iterdir():
        if entry.is_dir() and (entry / MANIFEST_NAME).is_file():
            ids.append(entry.name)
    return tuple(sorted(ids))


def load_attempt(
    workspace_root: Path,
    attempt_id: str,
    *,
    verify_files: bool = True,
) -> StagingAttempt:
    """Load a completed attempt and re-verify it before accepting it.

    Rejects (``StagingIncompleteError``): a missing directory, a missing or
    unreadable manifest, a manifest whose recomputed address differs from
    the stored ``manifest_hash``, and — when ``verify_files`` is on — any
    staged file whose on-disk size or digest drifted from the manifest.
    """
    attempt_dir = _staging_root(Path(workspace_root)) / attempt_id
    manifest_path = attempt_dir / MANIFEST_NAME
    if not manifest_path.is_file():
        raise StagingIncompleteError(
            f"staging attempt {attempt_id!r} has no completion manifest and "
            f"is not an accepted copy"
        )
    try:
        payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise StagingIncompleteError(
            f"staging attempt {attempt_id!r} manifest is unreadable: {exc}"
        ) from exc
    if not isinstance(payload, dict):
        raise StagingIncompleteError(
            f"staging attempt {attempt_id!r} manifest is not an object"
        )
    entries = payload.get("files")
    if not isinstance(entries, list):
        raise StagingIncompleteError(
            f"staging attempt {attempt_id!r} manifest has no file list"
        )
    files: List[StagedFile] = []
    for entry in entries:
        try:
            files.append(StagedFile(
                path=str(entry["path"]),
                size=int(entry["size"]),
                sha256=validate_sha256_hex(str(entry["sha256"]), "staged sha256"),
            ))
        except (KeyError, TypeError, ValueError) as exc:
            raise StagingIncompleteError(
                f"staging attempt {attempt_id!r} manifest entry is invalid: {exc}"
            ) from exc
    ordered = tuple(sorted(files, key=lambda f: f.path))
    recomputed = _manifest_address(ordered)
    stored_hash = str(payload.get("manifest_hash", ""))
    if str(payload.get("attempt_id", "")) != attempt_id:
        raise StagingIncompleteError(
            f"staging attempt {attempt_id!r} manifest records a different "
            f"attempt id {payload.get('attempt_id')!r}"
        )
    if stored_hash != recomputed:
        raise StagingIncompleteError(
            f"staging attempt {attempt_id!r} manifest address mismatch: "
            f"stored {stored_hash!r} != recomputed {recomputed!r}"
        )
    if verify_files:
        for staged_file in ordered:
            disk_path = attempt_dir / Path(staged_file.path)
            if not disk_path.is_file():
                raise StagingIncompleteError(
                    f"staged file missing from attempt {attempt_id!r}: "
                    f"{staged_file.path!r}"
                )
            digest, size = sha256_file(disk_path)
            if digest != staged_file.sha256 or size != staged_file.size:
                raise StagingIncompleteError(
                    f"staged file drifted from manifest in attempt "
                    f"{attempt_id!r}: {staged_file.path!r}"
                )
    return StagingAttempt(
        attempt_id=str(payload.get("attempt_id", attempt_id)),
        source_root=str(payload.get("source_root", "")),
        workspace_root=str(workspace_root),
        files=ordered,
        manifest_hash=recomputed,
        created_at=str(payload.get("created_at", "")),
    )
