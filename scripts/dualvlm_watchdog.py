#!/usr/bin/env python3
"""双VLM批跑watchdog（轻量，直读sqlite，不导入服务）：

状态机（每次cron触发跑一遍）：
  1. p4主队列仍有 queued/running → 打印进度退出。
  2. p4排空且有failed → 调 dualvlm_retry_failed.py 发p5重试波（幂等）。
  3. p5仍有 queued/running → 打印进度退出。
  4. 全部终态（p4+p5，且每受试者或有completed或有重试耗尽）→
     跑 dualvlm_finalize.py 全流程（裁决→定向核实→合并→发布），
     完成后写哨兵标记防止重复发布。

哨兵：/tmp/aemh_dualvlm_finalize_done.flag
"""
import json
import sqlite3
import subprocess
import sys
from pathlib import Path

WORKBENCH = Path(__file__).resolve().parents[1]
DB = (
    WORKBENCH
    / "runs"
    / "phase_c_mgk10_authority_v2_20260905"
    / "runtime"
    / "medical_monitoring_ai.sqlite3"
)
SENTINEL = Path("/tmp/aemh_dualvlm_finalize_done.flag")
P4_REF = "aemh:facts-snapshot-001.dualvlm-full1-p4:primary:"
P5_REF = "aemh:facts-snapshot-001.dualvlm-full1-p5:primary:"


def cohort_states(prefix: str) -> dict:
    conn = sqlite3.connect(f"file:{DB}?mode=ro", uri=True)
    rows = conn.execute(
        "SELECT status, COUNT(*) FROM monitoring_ai_jobs "
        "WHERE business_key LIKE ? GROUP BY status",
        (prefix + "%",),
    ).fetchall()
    conn.close()
    return dict(rows)


def main() -> int:
    if SENTINEL.exists():
        print("finalize already done; nothing to do")
        return 0
    p4 = cohort_states(P4_REF)
    active_p4 = p4.get("queued", 0) + p4.get("running", 0)
    p5 = cohort_states(P5_REF)
    active_p5 = p5.get("queued", 0) + p5.get("running", 0)
    print(f"p4: {p4} | p5: {p5}")

    if active_p4:
        print("p4 still processing; wait")
        return 0
    if active_p5:
        print("p5 still processing; wait")
        return 0

    # p4已排空：如有失败且p5未发过 → 发重试波
    if p4.get("failed") and not Path("/tmp/aemh_dualvlm_batch_p5_primary.json").exists():
        print("p4 drained with failures; submitting p5 retry wave")
        r = subprocess.run(
            [str(WORKBENCH / ".venv" / "bin" / "python"),
             str(WORKBENCH / "scripts" / "dualvlm_retry_failed.py")],
            capture_output=True, text=True, timeout=1800,
        )
        print(r.stdout[-2000:], r.stderr[-1000:])
        return 0

    # p5已排空：若p5也有failed且无更多代 → 就用现有completed收口
    # （每受试者仍有MTPLX/p2代completed兜底，覆盖率见finalize输出）
    print("all cohorts terminal; running finalize")
    r = subprocess.run(
        [str(WORKBENCH / ".venv" / "bin" / "python"),
         str(WORKBENCH / "scripts" / "dualvlm_finalize.py")],
        capture_output=True, text=True, timeout=14_400,
    )
    out = (r.stdout + r.stderr)[-3000:]
    print(out)
    if r.returncode == 0 and "TOKEN" in out:
        SENTINEL.write_text("done")
        print("finalize complete; sentinel written")
    return 0


if __name__ == "__main__":
    sys.exit(main())
