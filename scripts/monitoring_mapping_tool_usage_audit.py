"""R27-01历史mapping作业诚实分类（只读，无副作用）。

把持久化mapping作业按「登记能力合同 × 实际evidence_reads回执数」分类，
回答"该作业是否真的做过工具取证"。分类依据是实际回执，不是版本名——
tools-vN后缀不构成能力声称（见packages/medical_monitoring/admission/
evidence_tool_contract.py的如实登记表）。

分类值（evidence_tool_contract.classify_tool_usage）：
  tool_loop_executed            登记有工具合同且回执>0（真的做了工具取证）
  tool_loop_idle                登记有工具合同但回执=0（未发生工具读取）
  single_call                   登记为无工具且回执=0（单次调用）
  receipts_without_tool_contract 登记为无工具但回执>0（合同违约，需核查）
  unregistered                  版本未在登记处（历史遗留，需登记或退役）

用法：
  python3 scripts/monitoring_mapping_tool_usage_audit.py <monitoring_ai.sqlite3> [--out FILE]
sqlite以 uri?mode=ro 只读打开；只运行SELECT，不写库。
"""

from __future__ import annotations

import argparse
import json
import sqlite3
import sys
from datetime import datetime, timezone
from pathlib import Path

WORKBENCH_ROOT = Path(__file__).resolve().parents[1]
if str(WORKBENCH_ROOT) not in sys.path:
    sys.path.insert(0, str(WORKBENCH_ROOT))

from packages.medical_monitoring.admission.evidence_tool_contract import classify_tool_usage


def classify_persisted_jobs(db_path: Path) -> dict:
    conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    try:
        rows = conn.execute(
            """
            SELECT j.job_id, j.prompt_version, j.status,
                   (SELECT COUNT(*) FROM monitoring_ai_evidence_reads r
                    WHERE r.job_id = j.job_id) AS reads
            FROM monitoring_ai_jobs j
            WHERE j.task_type = 'listing_field_mapping'
            ORDER BY j.prompt_version, j.status
            """
        ).fetchall()
    finally:
        conn.close()
    by_class: dict[str, int] = {}
    detail = []
    # R27复核修正（20260927）：按作业粒度分类——组级read_rows总数会把
    # 混合组（少数有回执+多数0回执）整组误记，夸大tool_loop_executed。
    for row in rows:
        usage_class = classify_tool_usage(row["prompt_version"], row["reads"])
        by_class[usage_class] = by_class.get(usage_class, 0) + 1
        detail.append({
            "job_id": row["job_id"],
            "prompt_version": row["prompt_version"],
            "status": row["status"],
            "class": usage_class,
            # 该作业的实际回执行数（分类证据本身，随行可核查）。
            "evidence_read_rows": row["reads"],
        })
    return {
        "total_jobs": len(detail),
        "by_class": by_class,
        "rows": detail,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("db", type=Path)
    parser.add_argument("--out", type=Path, default=None,
                        help="同时把JSONL明细写入该文件")
    args = parser.parse_args()
    report = classify_persisted_jobs(args.db)
    record = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "db": str(args.db),
        "classifier": "evidence_tool_contract.classify_tool_usage",
        **report,
    }
    print(json.dumps(
        {key: record[key] for key in ("ts", "db", "total_jobs", "by_class")},
        ensure_ascii=False, indent=1,
    ))
    for item in record["rows"]:
        line = json.dumps(item, ensure_ascii=False)
        print(line)
        if args.out is not None:
            with args.out.open("a", encoding="utf-8") as fh:
                fh.write(line + "\n")
    if args.out is not None:
        with args.out.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(
                {"ts": record["ts"], "db": record["db"],
                 "total_jobs": record["total_jobs"],
                 "by_class": record["by_class"]}, ensure_ascii=False) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
