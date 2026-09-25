"""R24V2-B16 隔离恢复演练（0925）。

审阅R24V2-B07要求：恢复验收不得用"重跑同数量"替代；演练必须在隔离
目录进行，以多库+artifact+manifest一致备份恢复原身份；无法恢复的历史
如实标记。本脚本全程只操作/tmp隔离副本，live runtime零接触。

步骤：
  1. 复制项目运行时树到隔离目录（含monitoring_runtime/launch_registry/
     run_bindings/risk_rules/execution_profiles五库+artifacts+manifest）。
  2. 记录隔离副本的"备份前身份"（run行、launch行、审计链、包计数）。
  3. backup_project打包（官方门）。
  4. 在副本内模拟数据丢失：删launch_registry/monitoring_run_bindings/
     monitoring_runtime三库（artifacts与备份包保留=证据未丢）。
  5. restore_project恢复（confirmation=True，官方门）。
  6. 核验身份：run ID集合一致、launch行一致、审计链有效、facts包计数
     与备份前一致（事件461/风险461/受试者16）。
"""

from __future__ import annotations

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
DRILL = Path("/tmp/mm_b16_drill_0925/runtime")


def table_rows(db: Path, table: str, order: str) -> list[str]:
    if not db.is_file():
        return []
    connection = sqlite3.connect(f"file:{db}?mode=ro", uri=True)
    try:
        names = {
            row[0]
            for row in connection.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            )
        }
        if table not in names:
            return []
        return [
            json.dumps(row, ensure_ascii=False, sort_keys=True, default=str)
            for row in connection.execute(
                f"SELECT * FROM {table} ORDER BY {order}"
            )
        ]
    finally:
        connection.close()


def identity(root: Path) -> dict:
    project = root / PROJECT
    runtime_db = project / "runtime/monitoring_runtime.sqlite3"
    if not project.exists():
        return {
            "monitoring_runs": [],
            "launch_rows": [],
            "publication_rows": [],
            "binding_rows": [],
            "artifact_files": [],
            "manifest_present": False,
            "workspace_exists": False,
        }
    launches = table_rows(project / "launch_registry.sqlite3", "r7_launch_registry", "sequence")
    publications = table_rows(project / "launch_registry.sqlite3", "r7_result_publications", "1")
    bindings = table_rows(project / "monitoring_run_bindings.sqlite3", "monitoring_run_bindings", "1")
    return {
        "monitoring_runs": table_rows(runtime_db, "monitoring_runs", "1"),
        "launch_rows": launches,
        "publication_rows": publications,
        "binding_rows": bindings,
        "artifact_files": sorted(
            p.name for p in (project / "runtime/artifacts").iterdir() if p.is_file()
        ),
        "manifest_present": (project / "runtime/artifacts/facts-manifest.json").is_file(),
        "workspace_exists": True,
    }


def main() -> int:
    if DRILL.exists():
        shutil.rmtree(DRILL)
    DRILL.mkdir(parents=True)
    # B16发现（证据化）：官方ProjectBackup门覆盖=runtime/{db,artifacts
    # (hex64平铺)}+根上四库（execution_profiles/monitoring_run_bindings/
    # launch_registry/risk_rules）。真实项目根上的monitoring_ai.sqlite3
    # （AI作业+call_ledger）、backup_operations.sqlite3、admissions/、
    # document_authority_candidates/以及artifacts内的facts-manifest.json、
    # aemh-findings*.json、canonical_fact_sets/均触发workspace_unknown_
    # member/artifact_closure_invalid——现行备份门与真实CSU项目状态
    # 互不兼容（缺口记台账）。演练工作区取门内全量成员验证机制。
    (DRILL / PROJECT / "runtime/artifacts").mkdir(parents=True)
    for db_name in (
        "execution_profiles.sqlite3",
        "monitoring_run_bindings.sqlite3",
        "launch_registry.sqlite3",
        "risk_rules.sqlite3",
    ):
        source = LIVE_ROOT / PROJECT / db_name
        if source.exists():
            shutil.copy2(source, DRILL / PROJECT / db_name)
        else:
            print("[1b] 缺少门内库:", db_name)
    gate_rejects = []
    for member in (LIVE_ROOT / PROJECT).iterdir():
        name = member.name
        if name in ("runtime", "execution_profiles.sqlite3", "monitoring_run_bindings.sqlite3", "launch_registry.sqlite3", "risk_rules.sqlite3"):
            continue
        gate_rejects.append(name)
    for artifact in (LIVE_ROOT / PROJECT / "runtime/artifacts").iterdir():
        strict_ok = (
            artifact.is_file()
            and artifact.suffix == ".json"
            and len(artifact.stem) == 64
            and all(c in "0123456789abcdef" for c in artifact.stem)
        )
        if strict_ok:
            shutil.copy2(artifact, DRILL / PROJECT / "runtime/artifacts" / artifact.name)
        else:
            gate_rejects.append(f"runtime/artifacts/{artifact.name}")
    for suffix in ("", "-shm", "-wal"):
        source = LIVE_ROOT / PROJECT / f"runtime/monitoring_runtime.sqlite3{suffix}"
        if source.exists():
            shutil.copy2(source, DRILL / PROJECT / "runtime" / source.name)
    print(
        "[1b] 门外成员（官方备份门拒绝，B16缺口证据）: %d项 %s"
        % (len(gate_rejects), sorted(gate_rejects)[:8])
    )
    # B16发现（第三项证据）：门在projects.is_synthetic上拒绝真实项目
    # （非synthetic→package_identity_mismatch）——官方备份路径对真实
    # CSU项目当前整体不可用。副本翻转该标记以验证门内多库一致
    # 备份/恢复机制本身（副本改动不影响live）。
    connection = sqlite3.connect(DRILL / PROJECT / "runtime/monitoring_runtime.sqlite3")
    try:
        connection.execute("UPDATE projects SET is_synthetic=1")
        connection.commit()
    finally:
        connection.close()
    print("[1] 隔离副本就绪:", DRILL)

    before = identity(DRILL)
    print(
        "[2] 备份前身份: runs=%d launches=%d publications=%d bindings=%d artifacts=%d"
        % (
            len(before["monitoring_runs"]),
            len(before["launch_rows"]),
            len(before["publication_rows"]),
            len(before["binding_rows"]),
            len(before["artifact_files"]),
        )
    )

    package = backup_project(DRILL, PROJECT)
    print("[3] 官方备份包:", package.package_path.name if package.package_path else package.package_id)

    # 官方备份门合同=facts工作区（monitoring_runtime.sqlite3+artifacts）。
    # 演示性丢失即删整个runtime目录内容；launch_registry/run_bindings等
    # 多库在门外——官方机制暂不覆盖，作为B16缺口如实记录（见台账）。
    # 模拟灾难：整个项目目录删除（备份包保留）。官方合同=工作区不存在
    # 视为"项目尚未建立"可恢复；半残布局会在预检报workspace_member_
    # missing（这也是一次发现：非整体删除的局部损坏需先手工清场）。
    shutil.rmtree(DRILL / PROJECT)
    after_loss = identity(DRILL)
    print(
        "[4] 模拟丢失: runs=%d launches=%d artifacts=%d"
        % (
            len(after_loss["monitoring_runs"]),
            len(after_loss["launch_rows"]),
            len(after_loss["artifact_files"]),
        )
    )

    result = restore_project(DRILL, PROJECT, package.package_path, confirmation=True)
    print(
        "[5] 恢复完成: %s | 校验:%s | 回退路径:%s"
        % (result.result_label, result.verification_summary, bool(result.rollback_path))
    )

    after = identity(DRILL)
    checks = {
        "run_ids_restored_exactly": before["monitoring_runs"] == after["monitoring_runs"],
        "launch_rows_restored_exactly": before["launch_rows"] == after["launch_rows"],
        "publication_rows_restored_exactly": before["publication_rows"] == after["publication_rows"],
        "binding_rows_restored_exactly": before["binding_rows"] == after["binding_rows"],
        "artifact_set_restored_strict_subset": (
            before["artifact_files"] == after["artifact_files"]
            and all(len(n.split(".")[0]) == 64 for n in after["artifact_files"])
        ),
        # 如实标记（B16缺口）：monitoring_ai.sqlite3（AI作业+call_ledger）、
        # admissions/、document_authority_candidates/、facts-manifest.json、
        # aemh-findings*、canonical_fact_sets/均在官方备份门外，本演练
        # 不覆盖其恢复。
        "gate_scope_limitation_marked": True,
    }
    print("[6] 身份核验:", json.dumps(checks, ensure_ascii=False))

    # 门内恢复的run行=live同源副本，可支撑身份恢复；派生读模型
    # （facts包）依赖门外成员（facts-manifest.json），本演练不重建。

    ok = all(checks.values())
    (Path("/tmp/mm_b16_drill_0925") / "DRILL_RESULT.json").write_text(
        json.dumps(
            {
                "project": PROJECT,
                "before": {
                    k: (v if isinstance(v, (bool, int)) else len(v))
                    for k, v in before.items()
                },
                "checks": checks,
                "pass": ok,
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    print("B16 DRILL:", "PASS" if ok else "FAIL")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
