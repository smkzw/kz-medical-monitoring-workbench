"""SAR重跑·映射lane轮询（--stage mapping_poll，可重复调用）。

数据源（双通道，交叉印证）：
  A. GET r7/data-admissions/{attempt}/mapping-candidates?cohort=dual
     → pipeline投影：primary/verifier state + job_count/completed_job_count
  B. 直读 medical_monitoring_ai.sqlite3（只读）按business_key前缀聚合
     monitoring_ai_jobs状态（queued/running/completed/failed/blocked/stale_input）
     + 失败样本（failure_code/message）

判定：
  - 两队列job全部终态(completed/failed/blocked/stale_input)且
    candidates state=completed（候选就绪）→ exit 0, stillRunning=false
  - 有failed/blocked → 如实返回失败详情 → exit 0（轮询阶段本身的完成态，
    失败详情供决策；重试属后续处置）——但若仍有其他作业在跑则stillRunning=true
  - 仍在跑 → exit 10, stillRunning=true

预算：单次调用内部等待≤POLL_BUDGET_S（≤3h上限），超时返回stillRunning=true。
幂等：只读GET+只读sqlite；无副作用；台账记进度。
"""

from __future__ import annotations

import json
import sqlite3
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

WORKBENCH_ROOT = Path(__file__).resolve().parents[2]
R = WORKBENCH_ROOT / "runs/phase_c_mgk10_authority_v2_20260905/runtime"
PROJECT = "proj_mgk10_sar_real"
ATTEMPT_ID = "stg-e9d5050c73ef44be818e1f44920fdb5f"
BUSINESS_PREFIX = "listing-field-mapping:stg-e9d5050c73ef44be818e1f44920fdb5f"

HERE = Path(__file__).resolve().parent
EVIDENCE = HERE / "mapping_poll_evidence.jsonl"
STATE = HERE / "mapping_poll_state.json"
LEDGER = HERE / "run_ledger.jsonl"

BASE = (
    f"http://127.0.0.1:8910/api/projects/{PROJECT}"
    f"/modules/medical-monitoring/r7"
)
CANDIDATES_URL = (
    f"{BASE}/data-admissions/{ATTEMPT_ID}/mapping-candidates?cohort=dual"
)

ROUND_BUDGET_S = 1800.0   # 单次调用内部等待预算30min（上限3h）
POLL_INTERVAL_S = 300.0   # 5分钟一查
STABLE_CONFIRMATIONS = 1  # 连续满足即判终态

TERMINAL = {"completed", "failed", "blocked", "stale_input"}
BAD = {"failed", "blocked"}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _snapshot() -> dict:
    """A通道：pipeline投影；B通道：sqlite直读。"""
    out: dict = {"ts": _now()}
    try:
        req = urllib.request.Request(CANDIDATES_URL, headers={"Authorization": "Bearer local"})
        with urllib.request.urlopen(req, timeout=120) as resp:
            body = json.loads(resp.read())
        s = body.get("summary") or {}
        v = (body.get("verification") or {}).get("summary") or {}
        out["api"] = {
            "state": body.get("state"),
            "primary_jobs": s.get("job_count"),
            "primary_completed": s.get("completed_job_count"),
            "verifier_state": (body.get("verification") or {}).get("state"),
            "verifier_jobs": v.get("job_count"),
            "verifier_completed": v.get("completed_job_count"),
        }
    except Exception as exc:
        out["api_error"] = str(exc)[:200]
    conn = sqlite3.connect(f"file:{R / 'medical_monitoring_ai.sqlite3'}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    rows = conn.execute(
        "SELECT status, COUNT(*) n FROM monitoring_ai_jobs "
        "WHERE business_key LIKE ? AND created_at > '2026-09-26T10:40' "
        "GROUP BY status",
        (BUSINESS_PREFIX + "%",),
    ).fetchall()
    out["db_status_counts"] = {r["status"]: r["n"] for r in rows}
    by_cohort = {}
    for r in conn.execute(
        "SELECT profile_id, status, COUNT(*) n FROM monitoring_ai_jobs "
        "WHERE business_key LIKE ? AND created_at > '2026-09-26T10:40' "
        "GROUP BY profile_id, status",
        (BUSINESS_PREFIX + "%",),
    ):
        cohort = (
            "primary" if "_ai__" in (r["profile_id"] or "")
            else "verifier" if "_verifier_ai__" in (r["profile_id"] or "")
            else "deterministic"
        )
        by_cohort.setdefault(cohort, {}).setdefault(r["status"], 0)
        by_cohort[cohort][r["status"]] += r["n"]
    out["db_by_cohort"] = by_cohort
    fails = conn.execute(
        "SELECT job_id, failure_code, failure_message, attempt_count FROM monitoring_ai_jobs "
        "WHERE business_key LIKE ? AND created_at > '2026-09-26T10:40' "
        "AND status IN ('failed','blocked') LIMIT 5",
        (BUSINESS_PREFIX + "%",),
    ).fetchall()
    out["failure_samples"] = [
        {k: str(v)[:160] for k, v in dict(f).items()} for f in fails
    ]
    conn.close()
    return out


def main() -> int:
    deadline = time.time() + ROUND_BUDGET_S
    last = None
    with EVIDENCE.open("a", encoding="utf-8") as ev:
        def _e(step, ok, **d):
            ev.write(json.dumps(
                {"ts": _now(), "stage": "mapping_poll", "step": step,
                 "ok": bool(ok), **d}, ensure_ascii=False) + "\n")
        first = _snapshot()
        _e("round_start", True, snapshot=first)
        while True:
            last = first
            db = first.get("db_by_cohort", {})
            total = sum(sum(v.values()) for v in db.values())
            terminal = sum(
                n for v in db.values()
                for st, n in v.items() if st in TERMINAL
            )
            bad = sum(
                n for v in db.values()
                for st, n in v.items() if st in BAD
            )
            api = first.get("api") or {}
            states_done = (
                api.get("primary_state") == "completed"
                and api.get("verifier_state") == "completed"
            )
            if total and terminal == total and states_done:
                _e("round_done", True, verdict="all_terminal_candidates_ready",
                   snapshot=last)
                STATE.write_text(json.dumps(
                    {"round": "final", "snapshot": last, "updated_at": _now()},
                    ensure_ascii=False, indent=1), encoding="utf-8")
                print(json.dumps({"ok": True, "stillRunning": False,
                                  "snapshot": last, "bad": bad}, ensure_ascii=False))
                return 0
            if time.time() >= deadline:
                break
            time.sleep(POLL_INTERVAL_S)
            first = _snapshot()
            _e("poll", True, snapshot=first)

    still = {
        "db_by_cohort": last.get("db_by_cohort"),
        "api": last.get("api"),
        "failure_samples": last.get("failure_samples"),
    }
    with LEDGER.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps({
            "ts_utc": _now(), "stage": "mapping_poll",
            "project": PROJECT, "paid_ai_jobs_started": 0,
            "note": f"轮询快照：{json.dumps(still['db_by_cohort'], ensure_ascii=False)}",
            "failures": still["failure_samples"],
        }, ensure_ascii=False) + "\n")
    STATE.write_text(json.dumps(
        {"round": "in_progress", "snapshot": still, "updated_at": _now()},
        ensure_ascii=False, indent=1), encoding="utf-8")
    ev = {
        "ok": True,
        "stillRunning": last.get("db_by_cohort", {}) != {} and any(
            st in {"queued", "running"}
            for v in last.get("db_by_cohort", {}).values()
            for st in v
        ),
        "snapshot": still,
    }
    print(json.dumps(ev, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if a != "--stage" and a != "mapping_poll"]
    if any(not a.isdigit() for a in args):
        print("usage: sar_mapping_poll.py [--stage mapping_poll] [round]")
        sys.exit(2)
    sys.exit(main())
