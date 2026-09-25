"""R24V2-B16：备份门合同扩展——真实形态工作区的备份/恢复roundtrip。

0925隔离演练证明官方备份门对真实CSU项目整体不可用（三项拒绝证据）：
①根上的派生目录（admissions/document_authority_candidates）触发
workspace_unknown_member；②artifacts内DB内容哈希闭包之外的辅助成员
（facts-manifest.json、aemh-findings*.json、canonical_fact_sets/等）
触发artifact_closure_invalid；③projects.is_synthetic=0触发
package_identity_mismatch。本文件钉住扩展后的合同：

- 辅助成员（命名manifest/AI发现/压缩集/派生目录树）作为普通package
  member打包（manifest逐成员sha256），恢复后字节一致；
- hex64内容哈希闭包合同不变（闭包集合仍由runtime DB登记驱动）；
- 真实（非synthetic）项目可备份恢复；跨项目身份强校验保留；
- 派生目录接受上传件后缀（docx/xlsx），拒绝符号链接/临时件；
- 半残布局（成员缺失）仍然fail-closed。
"""

from __future__ import annotations

import hashlib
import json
import os
import sqlite3
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from packages.medical_monitoring.runtime.project_backup import (  # noqa: E402
    ProjectBackupError,
    ProjectBackupManager,
    backup_project,
    restore_project,
)

PROJECT = "proj-real-shape"


def _init_runtime_db(path: Path, *, synthetic: bool) -> None:
    import hashlib as _hashlib

    from packages.medical_monitoring.graph.store_common import AUDIT_GENESIS

    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path)
    try:
        conn.executescript(
            """
            CREATE TABLE meta (key TEXT PRIMARY KEY, value TEXT);
            CREATE TABLE projects (project_id TEXT PRIMARY KEY, name TEXT, is_synthetic INTEGER);
            CREATE TABLE monitoring_runs (run_id TEXT PRIMARY KEY, project_id TEXT, run_state TEXT,
                mode TEXT, execution_basis TEXT, analysis_state TEXT, data_cutoff TEXT);
            CREATE TABLE artifacts (content_hash TEXT PRIMARY KEY, project_id TEXT);
            CREATE TABLE listing_snapshots (snapshot_id TEXT PRIMARY KEY, project_id TEXT, content_hash TEXT);
            CREATE TABLE audit_events (seq INTEGER PRIMARY KEY, event_type TEXT, payload_json TEXT,
                payload_hash TEXT, prev_hash TEXT, chain_hash TEXT, created_at TEXT);
            CREATE TABLE audit_chain_head (singleton INTEGER PRIMARY KEY, last_seq INTEGER, last_chain_hash TEXT);
            INSERT INTO meta VALUES ('schema_version', '6');
            """
        )
        # 一条合法的创世审计事件（R1链校验器要求非空链+头一致）
        payload = json.dumps({"kind": "test-genesis"})
        payload_hash = _hashlib.sha256(payload.encode("utf-8")).hexdigest()
        created = "2026-09-25T00:00:00+00:00"
        chain = _hashlib.sha256(
            json.dumps(
                {
                    "seq": 1,
                    "event_type": "test",
                    "payload_hash": payload_hash,
                    "prev_hash": AUDIT_GENESIS,
                    "created_at": created,
                },
                sort_keys=True,
                separators=(",", ":"),
            ).encode("utf-8")
        ).hexdigest()
        conn.execute(
            "INSERT INTO audit_events VALUES (1, 'test', ?, ?, ?, ?, ?)",
            (payload, payload_hash, AUDIT_GENESIS, chain, created),
        )
        conn.execute(
            "INSERT INTO audit_chain_head VALUES (1, 1, ?)", (chain,)
        )
        conn.execute(
            "INSERT INTO projects VALUES (?, ?, ?)",
            (PROJECT, "真实形态研究", 1 if synthetic else 0),
        )
        conn.execute(
            "INSERT INTO monitoring_runs VALUES ('run-1', ?, 'completed', 'post_lock', 'facts', 'completed', '2026-09-25')",
            (PROJECT,),
        )
        conn.commit()
    finally:
        conn.close()


def _artifact_file(workspace: Path, payload: str) -> str:
    digest = hashlib.sha256(payload.encode("utf-8")).hexdigest()
    target = workspace / "runtime/artifacts" / f"{digest}.json"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(payload, encoding="utf-8")
    conn = sqlite3.connect(workspace / "runtime/monitoring_runtime.sqlite3")
    try:
        conn.execute(
            "INSERT INTO artifacts VALUES (?, ?)", (digest, PROJECT)
        )
        conn.commit()
    finally:
        conn.close()
    return digest


def _make_real_shaped_workspace(runtime_root: Path) -> Path:
    workspace = runtime_root / PROJECT
    _init_runtime_db(workspace / "runtime/monitoring_runtime.sqlite3", synthetic=False)
    blob = _artifact_file(workspace, '{"kind":"listing","rows":42}')
    # 辅助成员：命名manifest、AI发现工件、压缩集子目录
    (workspace / "runtime/artifacts/facts-manifest.json").write_text(
        json.dumps({"schema": "facts", "tables": ["AE"]}), encoding="utf-8"
    )
    (workspace / "runtime/artifacts/aemh-findings.active.json").write_text(
        '{"findings": []}', encoding="utf-8"
    )
    sets = workspace / "runtime/artifacts/canonical_fact_sets"
    sets.mkdir(parents=True)
    (sets / "set-1.json.gz").write_bytes(b"\x1f\x8b\x08\x00" + b"payload")
    # 派生根目录：接入staging（含上传件）与文档权威候选
    staging = workspace / "admissions/staging/stg-1"
    staging.mkdir(parents=True)
    (staging / "manifest.json").write_text("{}", encoding="utf-8")
    (staging / "listing.xlsx").write_bytes(b"PK\x03\x04fake")
    # 真实上传件含中文名（R24V2-B16：包成员名不再要求ASCII）
    (staging / "【Data Listing】真实研究_数据_V1.0.xlsx").write_bytes(b"PK\x03\x04cn")
    (workspace / "document_authority_candidates/files/doc.docx").parent.mkdir(
        parents=True
    )
    (workspace / "document_authority_candidates/files/doc.docx").write_bytes(
        b"PK\x03\x04docx"
    )
    # 门内必需的根库（schema标记须满足门的版本检查）
    conn = sqlite3.connect(workspace / "execution_profiles.sqlite3")
    conn.executescript(
        "CREATE TABLE profile_store_meta (key TEXT PRIMARY KEY, value TEXT);"
        "INSERT INTO profile_store_meta VALUES ('schema_version', 'mm-r7-profile-store-v1');"
    )
    conn.commit()
    conn.close()
    conn = sqlite3.connect(workspace / "monitoring_run_bindings.sqlite3")
    conn.executescript(
        "CREATE TABLE monitoring_run_bindings (binding_id TEXT PRIMARY KEY, schema_version TEXT);"
        "INSERT INTO monitoring_run_bindings VALUES ('b-1', 'r7-slice01-run-binding-v1');"
    )
    conn.commit()
    conn.close()
    return workspace


def _snapshot_identity(workspace: Path) -> dict:
    """Byte-level digests of every auxiliary member plus run rows."""
    identity = {}
    for relative in (
        "runtime/artifacts/facts-manifest.json",
        "runtime/artifacts/aemh-findings.active.json",
        "runtime/artifacts/canonical_fact_sets/set-1.json.gz",
        "admissions/staging/stg-1/manifest.json",
        "admissions/staging/stg-1/listing.xlsx",
        "document_authority_candidates/files/doc.docx",
    ):
        path = workspace / relative
        identity[relative] = (
            hashlib.sha256(path.read_bytes()).hexdigest() if path.is_file() else None
        )
    return identity


def test_real_shaped_workspace_backup_restore_roundtrip(tmp_path: Path) -> None:
    workspace = _make_real_shaped_workspace(tmp_path)
    blob = next(
        p.name
        for p in (workspace / "runtime/artifacts").iterdir()
        if p.stem != "facts-manifest" and len(p.stem) == 64
    )
    assert (workspace / "runtime/artifacts" / blob).is_file()

    package = backup_project(tmp_path, PROJECT)
    assert package.package_path is not None

    # 真实形态identity（含辅助成员+派生目录+闭包blob）
    def _identity(root: Path) -> dict:
        files = {
            "facts-manifest.json": workspace / "runtime/artifacts/facts-manifest.json",
            "findings": workspace / "runtime/artifacts/aemh-findings.active.json",
            "canonical_set": workspace / "runtime/artifacts/canonical_fact_sets/set-1.json.gz",
            "staging_manifest": workspace / "admissions/staging/stg-1/manifest.json",
            "listing": workspace / "admissions/staging/stg-1/listing.xlsx",
            "chinese_named_upload": workspace
            / "admissions/staging/stg-1/【Data Listing】真实研究_数据_V1.0.xlsx",
            "docx": workspace / "document_authority_candidates/files/doc.docx",
            "closure_blob": root / PROJECT / "runtime/artifacts" / blob,
        }
        return {
            key: hashlib.sha256(path.read_bytes()).hexdigest()
            for key, path in files.items()
        }

    before = _identity(tmp_path)

    # 灾难模拟：整个项目目录删除（备份包保留）
    import shutil

    shutil.rmtree(workspace)
    assert not workspace.exists()

    result = restore_project(tmp_path, PROJECT, package.package_path, confirmation=True)
    assert result.result_label == "恢复完成"

    after = _identity(tmp_path)
    assert after == before
    conn = sqlite3.connect(
        f"file:{workspace / 'runtime/monitoring_runtime.sqlite3'}?mode=ro", uri=True
    )
    try:
        assert conn.execute(
            "SELECT run_id, run_state FROM monitoring_runs"
        ).fetchall() == [("run-1", "completed")]
        assert conn.execute(
            "SELECT is_synthetic FROM projects WHERE project_id=?", (PROJECT,)
        ).fetchone() == (0,)
    finally:
        conn.close()


def test_auxiliary_symlink_and_tmp_still_fail_closed(tmp_path: Path) -> None:
    workspace = _make_real_shaped_workspace(tmp_path)
    # 临时件拒绝
    (workspace / "runtime/artifacts/facts-manifest.json.tmp").write_text("wip")
    manager = ProjectBackupManager(tmp_path, PROJECT)
    with pytest.raises(ProjectBackupError, match="artifact_closure_invalid"):
        manager.backup(None)
    (workspace / "runtime/artifacts/facts-manifest.json.tmp").unlink()
    # 符号链接拒绝
    os.symlink("../facts-manifest.json", workspace / "admissions/link.json")
    with pytest.raises(ProjectBackupError, match="workspace_member_symlink"):
        manager.backup(None)
    (workspace / "admissions/link.json").unlink()
    # 半残布局（必需库缺失）仍fail-closed
    (workspace / "execution_profiles.sqlite3").unlink()
    with pytest.raises(ProjectBackupError, match="workspace_member_missing"):
        manager.backup(None)
