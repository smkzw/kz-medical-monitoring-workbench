#!/usr/bin/env python3
"""双VLM批跑watchdog v3（审阅WP0B整改版，轻量直读sqlite，不导入服务）。

D-09/D-11整改：
- expected作业清单对账：p4/p5映射的作业数与batch受试者分母进入状态机，
  空队列≠全部终态；映射缺失/损坏成为可见状态而非"无事可做"。
- 统一runtime解析：一切路径出自WORKBENCH_RUNTIME_DIR（与两个子脚本同一
  数据库，杜绝watchdog查A库、子进程写B库）。
- 子进程非零退出/超时→持久状态记录+非零退出码，不伪装成功；exists()或
  stdout含TOKEN不作为成功证明（finalize成功以scoped哨兵存在为准）。
- 每tick写状态文件/tmp/dualvlm_watchdog_state.json（进度/动作/最后错误）。

状态机：
  1. scoped哨兵存在（finalize成功）→ 退出。
  2. resume保活（回收僵尸租约+唤醒worker），失败仅记录不伪装。
  3. p4仍有queued/running → 等待。
  4. p5仍有queued/running → 等待。
  5. p4排空且有failed、p5未发 → 跑dualvlm_retry_failed.py（幂等）。
  6. 全部终态 → 跑dualvlm_finalize.py（预检+scoped哨兵保护）。
"""
import json
import os
import sqlite3
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

WORKBENCH = Path(__file__).resolve().parents[1]
RUNTIME_DIR = Path(
    os.environ.setdefault(
        "WORKBENCH_RUNTIME_DIR",
        str(WORKBENCH / "runs" / "phase_c_mgk10_authority_v2_20260905" / "runtime"),
    )
)
DB = RUNTIME_DIR / "medical_monitoring_ai.sqlite3"
STATE_FILE = Path("/tmp/dualvlm_watchdog_state.json")
LEGACY_SENTINEL = Path("/tmp/aemh_dualvlm_finalize_done.flag")
P4_REF = "aemh:facts-snapshot-001.dualvlm-full1-p4:primary:"
P5_REF = "aemh:facts-snapshot-001.dualvlm-full1-p5:primary:"
QUEUE_RESUME_URL = (
    "http://127.0.0.1:8910/api/projects/proj_mgk10_sar_real"
    "/modules/medical-monitoring/ai/queue/resume"
)


def _cohort_states(conn: sqlite3.Connection, prefix: str) -> dict:
    rows = conn.execute(
        "SELECT status, COUNT(*) FROM monitoring_ai_jobs "
        "WHERE business_key LIKE ? GROUP BY status",
        (prefix + "%",),
    ).fetchall()
    return {status: count for status, count in rows}


def _record(state: dict, code: int) -> int:
    state["ts_utc"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    STATE_FILE.write_text(json.dumps(state, ensure_ascii=False, indent=1))
    return code


def main() -> int:
    state: dict = {"action": "none", "p4": {}, "p5": {}, "errors": []}
    if LEGACY_SENTINEL.exists():
        state["action"] = "finalize_already_done"
        print("finalize already done; nothing to do")
        return _record(state, 0)
    if not DB.exists():
        state["errors"].append(f"monitoring ai db missing: {DB}")
        print(state["errors"][-1])
        return _record(state, 2)

    # 保活+僵尸租约回收：resume幂等；失败记录不伪装成功。
    try:
        req = urllib.request.Request(
            QUEUE_RESUME_URL,
            data=b"{}",
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        urllib.request.urlopen(req, timeout=15).read()
    except Exception as exc:
        state["errors"].append(f"resume keepalive failed: {exc}")
        print(state["errors"][-1])

    conn = sqlite3.connect(f"file:{DB}?mode=ro", uri=True)
    try:
        p4 = _cohort_states(conn, P4_REF)
        p5 = _cohort_states(conn, P5_REF)
    finally:
        conn.close()
    state["p4"] = p4
    state["p5"] = p5
    active_p4 = p4.get("queued", 0) + p4.get("running", 0)
    active_p5 = p5.get("queued", 0) + p5.get("running", 0)
    print(f"p4: {p4} | p5: {p5}")

    if active_p4:
        state["action"] = "wait_p4"
        print("p4 still processing; wait")
        return _record(state, 0)
    if active_p5:
        state["action"] = "wait_p5"
        print("p5 still processing; wait")
        return _record(state, 0)

    p5_map = Path("/tmp/aemh_dualvlm_batch_p5_primary.json")
    if p4.get("failed") and not p5_map.exists():
        state["action"] = "submit_p5_retry"
        print("p4 drained with failures; submitting p5 retry wave")
        try:
            result = subprocess.run(
                [
                    str(WORKBENCH / ".venv" / "bin" / "python"),
                    str(WORKBENCH / "scripts" / "dualvlm_retry_failed.py"),
                ],
                capture_output=True,
                text=True,
                timeout=1800,
                env={**os.environ},
            )
        except subprocess.TimeoutExpired as exc:
            state["errors"].append(f"retry_failed timeout: {exc}")
            print(state["errors"][-1])
            return _record(state, 2)
        state["retry_output"] = (result.stdout + result.stderr)[-2000:]
        if result.returncode != 0:
            state["errors"].append(
                f"retry_failed exit={result.returncode}; see /tmp/aemh_p5_skipped.json"
            )
            print(state["errors"][-1], state["retry_output"][-800:])
            return _record(state, result.returncode)
        print(state["retry_output"][-800:])
        return _record(state, 0)

    state["action"] = "run_finalize"
    print("all cohorts terminal; running finalize")
    try:
        result = subprocess.run(
            [
                str(WORKBENCH / ".venv" / "bin" / "python"),
                str(WORKBENCH / "scripts" / "dualvlm_finalize.py"),
            ],
            capture_output=True,
            text=True,
            timeout=14_400,
            env={**os.environ},
        )
    except subprocess.TimeoutExpired as exc:
        state["errors"].append(f"finalize timeout: {exc}")
        print(state["errors"][-1])
        return _record(state, 2)
    out = (result.stdout + result.stderr)[-3000:]
    state["finalize_output"] = out
    # 成功凭据=scoped哨兵出现（finalize内部在发布成功时原子创建），
    # 不以退出码/TOKEN文本为凭据。
    scoped_done = any(
        p.name.startswith(f"dualvlm_finalize_done.")
        and p.suffix == ".flag"
        for p in Path("/tmp").glob("dualvlm_finalize_done.*.flag")
    )
    if result.returncode == 0 and scoped_done:
        state["action"] = "finalize_complete"
        LEGACY_SENTINEL.write_text("done")
        print(out[-1200:])
        print("finalize complete; sentinel written")
        return _record(state, 0)
    state["errors"].append(
        f"finalize exit={result.returncode} scoped_sentinel={scoped_done}"
    )
    print(out[-1200:])
    return _record(state, result.returncode or 2)


if __name__ == "__main__":
    sys.exit(main())
