"""R24V2-B16 隔离恢复演练 v2（0925门合同扩展后复测）。

v1（同目录drill.py）证明：扩展前官方备份门对真实CSU项目整体不可用
（三项拒绝证据）。本脚本在门合同扩展后，以真实形态整项目复制重测：
admissions/、document_authority_candidates/、artifacts辅助成员
（facts-manifest.json、aemh-findings*、canonical_fact_sets/、
facts-manifests/）、真实（非synthetic）项目行全部参与备份→整项目
目录删除→官方restore→逐成员字节+行级身份核验。全程隔离目录，
live零接触。
"""

from __future__ import annotations

import hashlib
import json
import shutil
import sqlite3
import sys
from pathlib import Path

WORKBENCH = Path("/Users/smkzw/Documents/康哲项目资料/AI/医学经理工作台/implementation/workbench")
sys.path.insert(0, str(WORKBENCH))

from packages.medical_monitoring.runtime.project_backup import (
    backup_project,
    restore_project,
)

LIVE_ROOT = WORKBENCH / "runs/phase_c_mgk10_authority_v2_20260905/runtime/medical_monitoring_r7"
PROJECT = "proj_user_2f17492ac59b"
DRILL = Path("/tmp/mm_b16_drill_0925_v2/runtime")


def identity(root: Path) -> dict:
    """全成员身份：每文件sha256 + 关键库行级内容。"""
    project = root / PROJECT
    if not project.exists():
        return {"exists": False, "files": {}, "runs": [], "launches": []}
    files = {}
    for path in sorted(project.rglob("*")):
        if path.is_file() and not path.name.endswith(("-wal", "-shm", "-journal")):
            rel = path.relative_to(project).as_posix()
            if rel.startswith(".mmbackup") or "/.mmbackup" in rel:
                continue
            files[rel] = hashlib.sha256(path.read_bytes()).hexdigest()
    conn = sqlite3.connect(f"file:{project / 'runtime/monitoring_runtime.sqlite3'}?mode=ro", uri=True)
    try:
        runs = [
            tuple(row)
            for row in conn.execute(
                "SELECT run_id, analysis_state, execution_basis FROM monitoring_runs ORDER BY run_id"
            )
        ]
    finally:
        conn.close()
    conn = sqlite3.connect(f"file:{project / 'launch_registry.sqlite3'}?mode=ro", uri=True)
    try:
        launches = [
            tuple(row)
            for row in conn.execute(
                "SELECT * FROM r7_launch_registry ORDER BY sequence"
            )
        ]
    finally:
        conn.close()
    return {"exists": True, "files": files, "runs": runs, "launches": launches}


def main() -> int:
    if DRILL.exists():
        shutil.rmtree(DRILL)
    DRILL.mkdir(parents=True)
    shutil.copytree(LIVE_ROOT / PROJECT, DRILL / PROJECT, symlinks=True)
    print("[1] 真实形态隔离副本就绪:", DRILL)

    before = identity(DRILL)
    print(
        "[2] 备份前身份: 文件=%d 运行=%d launch行=%d"
        % (len(before["files"]), len(before["runs"]), len(before["launches"]))
    )

    package = backup_project(DRILL, PROJECT)
    print("[3] 官方备份包:", package.package_path.name if package.package_path else package.package_id)

    shutil.rmtree(DRILL / PROJECT)
    print("[4] 整项目目录已删除:", not (DRILL / PROJECT).exists())

    result = restore_project(DRILL, PROJECT, package.package_path, confirmation=True)
    print("[5] 恢复完成:", result.result_label)

    after = identity(DRILL)
    # sqlite主文件的字节布局允许合法差异（备份走逻辑快照，WAL已
    # checkpoint进主文件）；其内容一致性由恢复后门的审计链/schema/
    # 闭包校验+下方行级核验承担。其余全部成员必须字节一致。
    db_names = {
        "execution_profiles.sqlite3",
        "monitoring_run_bindings.sqlite3",
        "launch_registry.sqlite3",
        "risk_rules.sqlite3",
        "runtime/monitoring_runtime.sqlite3",
    }
    non_db_before = {k: v for k, v in before["files"].items() if k not in db_names}
    non_db_after = {k: v for k, v in after["files"].items() if k not in db_names}
    checks = {
        "every_non_db_file_byte_identical": non_db_before == non_db_after,
        "db_members_present": all(name in after["files"] for name in db_names),
        "file_count_matches": len(before["files"]) == len(after["files"]),
        "run_rows_identical": before["runs"] == after["runs"],
        "launch_rows_identical": before["launches"] == after["launches"],
    }
    # 辅助成员单独点名核验（门扩展的直接对象）
    for key in (
        "runtime/artifacts/facts-manifest.json",
        "runtime/artifacts/aemh-findings.active.json",
        "admissions/staging",
        "document_authority_candidates/files",
    ):
        hits = [name for name in before["files"] if name.startswith(key)]
        checks[f"aux:{key}"] = bool(hits) and all(
            before["files"][name] == after["files"].get(name) for name in hits
        )
    print("[6] 身份核验:", json.dumps(checks, ensure_ascii=False))

    ok = all(checks.values())
    (DRILL.parent / "DRILL_V2_RESULT.json").write_text(
        json.dumps(
            {
                "project": PROJECT,
                "file_count": len(before["files"]),
                "runs": len(before["runs"]),
                "checks": checks,
                "pass": ok,
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    print("B16 DRILL v2:", "PASS" if ok else "FAIL")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
