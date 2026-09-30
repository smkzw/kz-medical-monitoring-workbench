#!/usr/bin/env python3
"""R8D：隔离 runtime 存量 launch_registry.sqlite3 原地 v4→v5 升级。

背景（R5D 发现、R8D 修复）：`_init_monitoring_runtime_dbs` 曾以现行 v5 DDL
建库却写入过期 v4 marker（mm-r7-slice08b-launch-registry-v4），schema 检验
按 marker 匹配 v4 形状 → shape_mismatch → CORRUPT → project open 全挡。
代码侧已改种子 marker 取 launch_registry_contracts.SCHEMA_VERSION（R8D）。

本脚本对隔离 runtime（runs/tester_loop_iso_20260928/runtime）的存量文件做
与 `LaunchRegistry.open()` v4→v5 完全同语义的守卫式原地升级（见
packages/medical_monitoring/runtime/launch_registry_core_mixin.py:173-197）：
- 仅处理 marker == SCHEMA_VERSION_V4 的文件；CURRENT 跳过；其他 fail-closed 报告不动。
- 先 PRAGMA 查列再 ALTER ADD（v5 形状文件列已存在 → ALTER 为 no-op）。
- 同一事务内推进 marker 至 SCHEMA_VERSION_V5，不重建表、不改既有行数据。
- 每文件前后各跑一次产品自身 inspect_member 留证。

只允许作用于隔离 runtime 目录，绝不触碰 8910 舰队 runtime。
"""
from __future__ import annotations

import json
import sqlite3
import sys
from datetime import datetime, timezone
from pathlib import Path

WORKBENCH = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(WORKBENCH))

from packages.medical_monitoring.runtime.launch_registry_contracts import (  # noqa: E402
    SCHEMA_VERSION,
    SCHEMA_VERSION_V4,
)
from packages.medical_monitoring.runtime.schema_manifest import (  # noqa: E402
    SchemaClassification,
    inspect_member,
)

RUNTIME_ROOT = WORKBENCH / "runs" / "tester_loop_iso_20260928" / "runtime"
V5_COLUMNS = ("frozen_read_model_artifact_id", "frozen_read_model_sha256")
EVIDENCE = Path(__file__).resolve().parent / "r8d_repair_evidence.jsonl"


def repair_one(path: Path) -> dict:
    before = inspect_member(path, "launch_registry")
    record = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "workspace": path.parent.name,
        "file": str(path),
        "before": {
            "classification": before.classification.value,
            "reason_code": before.reason_code,
            "marker_value": before.marker_value,
        },
        "action": None,
        "after": None,
    }
    if before.classification is SchemaClassification.CURRENT:
        record["action"] = "skip_current"
        return record
    if before.marker_value != SCHEMA_VERSION_V4:
        # fail-closed：非 v4 marker 的异常文件一律不动，仅上报。
        record["action"] = "refuse_unexpected_marker"
        return record
    conn = sqlite3.connect(str(path), timeout=30.0, isolation_level=None)
    try:
        conn.execute("PRAGMA busy_timeout = 30000")
        conn.execute("BEGIN IMMEDIATE")
        row = conn.execute(
            "SELECT value FROM r7_launch_registry_meta WHERE key = 'schema_version'"
        ).fetchone()
        marker = None if row is None else str(row[0])
        if marker != SCHEMA_VERSION_V4:
            conn.execute("ROLLBACK")
            record["action"] = f"refuse_concurrent_marker_{marker}"
            return record
        existing_columns = {
            str(r[1]) for r in conn.execute("PRAGMA table_info(r7_result_publications)")
        }
        altered = []
        for column in V5_COLUMNS:
            if column not in existing_columns:
                conn.execute(
                    "ALTER TABLE r7_result_publications ADD COLUMN " f"{column} TEXT"
                )
                altered.append(column)
        conn.execute(
            "UPDATE r7_launch_registry_meta SET value = ? "
            "WHERE key = 'schema_version'",
            (SCHEMA_VERSION,),
        )
        conn.execute("COMMIT")
    except Exception:
        try:
            conn.execute("ROLLBACK")
        except sqlite3.Error:
            pass
        raise
    finally:
        conn.close()
    after = inspect_member(path, "launch_registry")
    record["action"] = "upgraded_v4_to_v5"
    record["altered_columns"] = altered
    record["after"] = {
        "classification": after.classification.value,
        "reason_code": after.reason_code,
        "marker_value": after.marker_value,
    }
    return record


def main() -> int:
    files = sorted(
        RUNTIME_ROOT.glob("medical_monitoring_r7/*/launch_registry.sqlite3")
    )
    print(f"isolated runtime root: {RUNTIME_ROOT}")
    print(f"launch_registry.sqlite3 files found: {len(files)}")
    results = []
    for path in files:
        rec = repair_one(path)
        results.append(rec)
        print(
            f"{rec['workspace']}: {rec['before']['classification']}/"
            f"{rec['before']['marker_value']} --{rec['action']}--> "
            f"{(rec['after'] or {}).get('classification', 'n/a')}"
        )
    with EVIDENCE.open("a", encoding="utf-8") as fh:
        for rec in results:
            fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
    upgraded = [r for r in results if r["action"] == "upgraded_v4_to_v5"]
    skipped = [r for r in results if r["action"] == "skip_current"]
    refused = [r for r in results if r["action"] not in (
        "upgraded_v4_to_v5", "skip_current")]
    bad_after = [
        r for r in upgraded
        if (r["after"] or {}).get("classification") != SchemaClassification.CURRENT.value
    ]
    print(
        f"summary: upgraded={len(upgraded)} skipped_current={len(skipped)} "
        f"refused={len(refused)} not_current_after={len(bad_after)}"
    )
    if refused or bad_after:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
