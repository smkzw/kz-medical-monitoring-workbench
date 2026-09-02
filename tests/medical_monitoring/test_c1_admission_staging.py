"""C1 staging-copy admission contract tests (Phase C, work item 1).

All fixtures are generated non-real files under ``tmp_path``.  The suite
proves the admission contract invariants: the source tree is never written,
copies are byte-identical (streaming SHA-256, re-verified), interrupted or
hash-mismatched copies are never accepted, and the manifest address is
deterministic across attempts.
"""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path

import pytest

from packages.medical_monitoring.admission import staging as staging_module
from packages.medical_monitoring.admission.staging import (
    MANIFEST_NAME,
    STAGING_SCHEMA_NAME,
    StagingError,
    StagingHashMismatchError,
    StagingIncompleteError,
    StagingSourceError,
    list_attempt_ids,
    load_attempt,
    sha256_file,
    stage_copy,
)


def make_source_tree(root: Path) -> dict[str, bytes]:
    """Generate a small non-real source tree: two nested listing-like files."""
    files = {
        "listing_a.csv": b"subject,visit,result\nS-01,V1,120\nS-02,V1,135\n",
        "sub/listing_b.csv": (
            b"subject,visit,result\nS-01,V2,118\nS-03,V2,cr\n"
        ),
    }
    for relative, payload in files.items():
        target = root / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(payload)
    return files


def snapshot_tree(root: Path) -> dict[str, tuple]:
    """Bytes + metadata fingerprint of every path under *root*.

    atime is deliberately excluded: read-only access may update it, and the
    contract only forbids writes.
    """
    snapshot: dict[str, tuple] = {}
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames.sort()
        for name in sorted(dirnames):
            path = Path(dirpath) / name
            rel = path.relative_to(root).as_posix()
            stat = path.stat()
            snapshot[rel + "/"] = ("dir", stat.st_mode)
        for name in sorted(filenames):
            path = Path(dirpath) / name
            rel = path.relative_to(root).as_posix()
            stat = path.stat()
            digest = hashlib.sha256(path.read_bytes()).hexdigest()
            snapshot[rel] = ("file", stat.st_size, stat.st_mtime_ns, stat.st_mode, digest)
    return snapshot


def test_stage_copy_creates_verified_isolated_attempt(tmp_path: Path) -> None:
    source_root = tmp_path / "source"
    files = make_source_tree(source_root)
    workspace = tmp_path / "workspace"

    attempt = stage_copy(
        source_root, sorted(files), workspace, attempt_id="stg-test-1"
    )

    assert attempt.attempt_id == "stg-test-1"
    assert [f.path for f in attempt.files] == ["listing_a.csv", "sub/listing_b.csv"]
    for staged in attempt.files:
        source_digest = hashlib.sha256(
            (source_root / staged.path).read_bytes()
        ).hexdigest()
        assert staged.sha256 == source_digest
        copy_digest, copy_size = sha256_file(attempt.file_path(staged.path))
        assert copy_digest == source_digest
        assert copy_size == staged.size
    assert attempt.path.is_dir()
    assert (attempt.path / MANIFEST_NAME).is_file()
    assert not (attempt.path.with_name(attempt.attempt_id + ".tmp")).exists()
    assert list_attempt_ids(workspace) == ("stg-test-1",)

    loaded = load_attempt(workspace, "stg-test-1")
    assert loaded.manifest_hash == attempt.manifest_hash
    assert loaded.files == attempt.files


def test_manifest_is_deterministic_across_attempts(tmp_path: Path) -> None:
    source_root = tmp_path / "source"
    files = make_source_tree(source_root)

    first = stage_copy(source_root, sorted(files), tmp_path / "ws1", attempt_id="stg-a")
    second = stage_copy(source_root, sorted(files), tmp_path / "ws2", attempt_id="stg-b")

    assert first.manifest_hash == second.manifest_hash
    assert [f.path for f in first.files] == [f.path for f in second.files]
    assert [f.sha256 for f in first.files] == [f.sha256 for f in second.files]
    manifest = json.loads(first.path.joinpath(MANIFEST_NAME).read_text("utf-8"))
    assert manifest["schema"] == STAGING_SCHEMA_NAME
    assert manifest["attempt_id"] == "stg-a"


def test_source_tree_is_byte_and_metadata_identical_after_staging(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    source_root = tmp_path / "source"
    files = make_source_tree(source_root)
    before = snapshot_tree(source_root)

    stage_copy(source_root, sorted(files), tmp_path / "ws", attempt_id="stg-ok")

    # A failing staging must also leave the source untouched.
    def failing_copy(source_file: Path, copy_file: Path):
        raise StagingHashMismatchError("simulated copy corruption")

    monkeypatch.setattr(staging_module, "_copy_and_hash", failing_copy)
    with pytest.raises(StagingHashMismatchError):
        stage_copy(source_root, sorted(files), tmp_path / "ws", attempt_id="stg-bad")
    monkeypatch.undo()

    assert snapshot_tree(source_root) == before
    assert not (tmp_path / "ws" / "staging" / "stg-bad").exists()
    assert not (tmp_path / "ws" / "staging" / "stg-bad.tmp").exists()


def test_interrupted_copy_is_never_accepted(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    source_root = tmp_path / "source"
    files = make_source_tree(source_root)
    workspace = tmp_path / "workspace"
    calls = {"count": 0}
    real_copy = staging_module._copy_and_hash

    def interrupted_copy(source_file: Path, copy_file: Path):
        calls["count"] += 1
        if calls["count"] == 2:
            raise KeyboardInterrupt("simulated crash mid-copy")
        return real_copy(source_file, copy_file)

    monkeypatch.setattr(staging_module, "_copy_and_hash", interrupted_copy)
    with pytest.raises(KeyboardInterrupt):
        stage_copy(
            source_root, sorted(files), workspace, attempt_id="stg-crash"
        )
    monkeypatch.undo()

    assert not (workspace / "staging" / "stg-crash").exists()
    assert not (workspace / "staging" / "stg-crash.tmp").exists()
    assert list_attempt_ids(workspace) == ()
    with pytest.raises(StagingIncompleteError):
        load_attempt(workspace, "stg-crash")


def test_unmanifested_partial_directory_is_rejected(tmp_path: Path) -> None:
    source_root = tmp_path / "source"
    files = make_source_tree(source_root)
    workspace = tmp_path / "workspace"

    attempt = stage_copy(
        source_root, sorted(files), workspace, attempt_id="stg-good"
    )
    # Simulate a process killed after the atomic rename layout but with the
    # manifest removed, plus a stale in-progress directory.
    (attempt.path / MANIFEST_NAME).unlink()
    stale_tmp = workspace / "staging" / "stg-stale.tmp"
    (stale_tmp / "sub").mkdir(parents=True)
    (stale_tmp / "listing_a.csv").write_bytes(files["listing_a.csv"][:8])

    assert list_attempt_ids(workspace) == ()
    with pytest.raises(StagingIncompleteError):
        load_attempt(workspace, "stg-good")
    with pytest.raises(StagingIncompleteError):
        load_attempt(workspace, "stg-stale")


def test_tampered_staged_file_is_rejected_on_load(tmp_path: Path) -> None:
    source_root = tmp_path / "source"
    files = make_source_tree(source_root)
    workspace = tmp_path / "workspace"

    attempt = stage_copy(source_root, sorted(files), workspace, attempt_id="stg-t")
    staged_file = attempt.file_path("listing_a.csv")
    staged_file.write_bytes(staged_file.read_bytes() + b"drift\n")

    with pytest.raises(StagingIncompleteError):
        load_attempt(workspace, "stg-t")
    # Without file re-verification the manifest itself still verifies, so
    # the caller explicitly opts out of drift detection.
    assert load_attempt(workspace, "stg-t", verify_files=False).manifest_hash


def test_tampered_manifest_address_is_rejected(tmp_path: Path) -> None:
    source_root = tmp_path / "source"
    files = make_source_tree(source_root)
    workspace = tmp_path / "workspace"

    attempt = stage_copy(source_root, sorted(files), workspace, attempt_id="stg-m")
    manifest_path = attempt.path / MANIFEST_NAME
    payload = json.loads(manifest_path.read_text("utf-8"))
    payload["manifest_hash"] = "f" * 64
    manifest_path.write_text(json.dumps(payload), encoding="utf-8")

    with pytest.raises(StagingIncompleteError):
        load_attempt(workspace, "stg-m")


def test_copy_digest_mismatch_is_rejected(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    source_root = tmp_path / "source"
    files = make_source_tree(source_root)
    workspace = tmp_path / "workspace"
    real_sha = staging_module.sha256_file

    def lying_digest(path: Path):
        digest, size = real_sha(path)
        return "0" * 64, size

    monkeypatch.setattr(staging_module, "sha256_file", lying_digest)
    with pytest.raises(StagingHashMismatchError):
        stage_copy(source_root, sorted(files), workspace, attempt_id="stg-x")
    monkeypatch.undo()

    assert list_attempt_ids(workspace) == ()
    assert not (workspace / "staging" / "stg-x.tmp").exists()


def test_streaming_hash_handles_multi_chunk_files(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    source_root = tmp_path / "source"
    payload = bytes(range(256)) * 8  # 2048 bytes
    (source_root / "big.bin").parent.mkdir(parents=True)
    (source_root / "big.bin").write_bytes(payload)
    monkeypatch.setattr(staging_module, "_CHUNK_SIZE", 64)

    attempt = stage_copy(
        source_root, ["big.bin"], tmp_path / "workspace", attempt_id="stg-chunk"
    )

    assert attempt.files[0].size == len(payload)
    assert attempt.files[0].sha256 == hashlib.sha256(payload).hexdigest()


def test_source_path_rejections_leave_source_tree_untouched(tmp_path: Path) -> None:
    source_root = tmp_path / "source"
    files = make_source_tree(source_root)
    before = snapshot_tree(source_root)

    with pytest.raises(StagingSourceError):
        stage_copy(source_root, ["/etc/hostname"], tmp_path / "ws")
    with pytest.raises(StagingSourceError):
        stage_copy(source_root, ["../outside.csv"], tmp_path / "ws")
    (tmp_path / "outside.csv").write_bytes(b"nearby")
    with pytest.raises(StagingSourceError):
        stage_copy(source_root, ["../outside.csv"], tmp_path / "ws")
    with pytest.raises(StagingSourceError):
        stage_copy(source_root, ["missing.csv"], tmp_path / "ws")
    with pytest.raises(StagingSourceError):
        stage_copy(source_root, ["sub"], tmp_path / "ws")
    with pytest.raises(StagingError):
        stage_copy(source_root, [], tmp_path / "ws")
    with pytest.raises(StagingError):
        stage_copy(source_root, ["listing_a.csv", "listing_a.csv"], tmp_path / "ws")

    assert snapshot_tree(source_root) == before


def test_workspace_inside_source_root_is_rejected(tmp_path: Path) -> None:
    source_root = tmp_path / "source"
    files = make_source_tree(source_root)
    before = snapshot_tree(source_root)

    with pytest.raises(StagingError):
        stage_copy(
            source_root, sorted(files), source_root / "isolated",
            attempt_id="stg-inside",
        )

    assert snapshot_tree(source_root) == before
    assert not (source_root / "isolated").exists()


def test_retry_never_overwrites_existing_attempt(tmp_path: Path) -> None:
    source_root = tmp_path / "source"
    files = make_source_tree(source_root)
    workspace = tmp_path / "workspace"

    first = stage_copy(source_root, sorted(files), workspace, attempt_id="stg-1")
    with pytest.raises(StagingError):
        stage_copy(source_root, sorted(files), workspace, attempt_id="stg-1")

    reloaded = load_attempt(workspace, "stg-1")
    assert reloaded.manifest_hash == first.manifest_hash
    assert list_attempt_ids(workspace) == ("stg-1",)


def test_manifest_hash_rejects_file_list_changes(tmp_path: Path) -> None:
    source_root = tmp_path / "source"
    files = make_source_tree(source_root)
    workspace = tmp_path / "workspace"

    attempt = stage_copy(source_root, sorted(files), workspace, attempt_id="stg-d")
    payload = json.loads(attempt.path.joinpath(MANIFEST_NAME).read_text("utf-8"))
    payload["files"][0]["size"] += 1
    (attempt.path / MANIFEST_NAME).write_text(
        json.dumps(payload), encoding="utf-8"
    )

    with pytest.raises(StagingIncompleteError):
        load_attempt(workspace, "stg-d", verify_files=False)
