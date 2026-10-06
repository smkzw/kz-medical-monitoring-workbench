"""R19 攻坚复现驱动（第1次）：常驻开考项目「MX循开考-CSU」运行启动死锁。

目的（对应攻坚任务①③）：
  Phase A 基线：同一时刻后端真实状态（mapping/facts/project/open/run-setup/
               options/runs + 磁盘 launch_registry/profile_layer_versions）。
  Phase B 复现：忠实重放 R19-D 界面向导的 prepare-and-start（同一幂等键、
               同一指纹、**不先 workspace/bootstrap**——界面路径从不调用它，
               且 /workspace/bootstrap 需 ADMINISTER_RUNTIME 权限，监查用户
               无从调用）。记录 http 状态/耗时/响应体 + 拒绝事件落盘。
  Phase V 重验（--verify，修复后）：同一幂等键再放一次（run_routes 的 replay
               分支应补完同一运行）→ 轮询 progress 至 completed →
               publication → available → result-entry 可读。

用法：
  python3 r19s_siege_repro.py            # 复现（修复前）
  python3 r19s_siege_repro.py --verify   # 重验（修复后）
证据：r19s_siege_evidence.jsonl（每请求一条 JSONL）。
"""
from __future__ import annotations

import json
import sqlite3
import sys
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path

import requests

BASE = "http://127.0.0.1:8911"
PROJECT_NAME = "MX循开考-CSU"
HERE = Path(__file__).resolve().parent
EVIDENCE = HERE / "r19s_siege_evidence.jsonl"

# R19-D 界面向导 2026-10-05T22:35:48Z 创建的僵尸预约（launch_registry 行）：
R19D_IDEM = "monitoring_46a9e2b3-ad66-4790-8efe-b05a12309b34"
R19D_SNAPSHOT = "snapshot:ef8692acfbab4d2a9846916f"

RUNTIME = (
    "/Users/smkzw/Documents/康哲项目资料/AI/医学经理工作台"
    "/implementation/workbench/runs/tester_loop_iso_20260928/runtime"
)
WS = f"{RUNTIME}/medical_monitoring_r7"

VERIFY = "--verify" in sys.argv
MODE_TAG = "verify" if VERIFY else "repro"

s = requests.Session()


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _ev(step: str, ok: bool, **kv) -> None:
    rec = {"ts": _now(), "mode": MODE_TAG, "step": step, "ok": bool(ok)}
    rec.update(kv)
    with EVIDENCE.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
    print(f"  [{step}] ok={ok} " + " ".join(
        f"{k}={str(v)[:120]}" for k, v in list(kv.items())[:4]), flush=True)


def _http(step: str, method: str, url: str, *, json_body=None, timeout=180):
    t0 = time.monotonic()
    try:
        resp = s.request(method, url, json=json_body, timeout=timeout)
        status, text = resp.status_code, resp.text
        elapsed_ms = int((time.monotonic() - t0) * 1000)
    except Exception as exc:  # noqa: BLE001
        _ev(step, False, kind="http", url=url,
            error=f"{type(exc).__name__}: {exc}"[:300])
        return 0, {}, 0
    try:
        parsed = json.loads(text)
    except Exception:  # noqa: BLE001
        parsed = {"_raw": text[:1500]}
    _ev(step, 200 <= status < 300, kind="http",
        request={"method": method, "url": url},
        http_status=status, elapsed_ms=elapsed_ms,
        response=json.dumps(parsed, ensure_ascii=False)[:2500])
    return status, parsed, elapsed_ms


def _sqlite_rows(db: str, sql: str, params=()):
    try:
        conn = sqlite3.connect(f"file:{db}?mode=ro", uri=True, timeout=10)
        conn.row_factory = sqlite3.Row
        rows = [dict(r) for r in conn.execute(sql, params).fetchall()]
        conn.close()
        return rows
    except Exception as exc:  # noqa: BLE001
        return [{"error": f"{type(exc).__name__}: {exc}"}]


def disk_state(pid: str, tag: str) -> None:
    lr_rows = _sqlite_rows(
        f"{WS}/{pid}/launch_registry.sqlite3",
        "SELECT sequence, run_state, result_available, manifest_digest, "
        "idempotency_key, substr(public_run_token,1,22) tok, created_at, "
        "updated_at FROM r7_launch_registry ORDER BY sequence",
    )
    prof_rows = _sqlite_rows(
        f"{WS}/{pid}/execution_profiles.sqlite3",
        "SELECT layer_kind, scope_key, revision FROM profile_layer_versions "
        "ORDER BY rowid",
    )
    _ev(f"disk_state_{tag}", True, launch_registry=lr_rows,
        profile_layer_versions=prof_rows)


def main() -> int:
    print(f"=== R19 siege {MODE_TAG} @ {_now()}", flush=True)

    # ── Phase A 基线：同一时刻后端真实状态 ────────────────────────────
    st, projects, _ = _http("projects_list", "GET", f"{BASE}/api/projects")
    pid = None
    plist = projects if isinstance(projects, list) else (projects or {}).get("projects") or []
    for p in plist:
        if p.get("project_name") == PROJECT_NAME:
            pid = p.get("project_id")
    if not pid:
        _ev("find_project", False, reason=f"{PROJECT_NAME} not in list")
        return 2
    _ev("find_project", True, project_id=pid)
    mm = f"{BASE}/api/projects/{pid}/modules/medical-monitoring/r7"
    adm = f"{mm}/data-admissions"
    attempt = "stg-cd69899943ba42618f589ba07a134a59"  # r19d 种子 attempt
    att = f"{adm}/{attempt}"

    _http("a_mapping_candidates", "GET", f"{att}/mapping-candidates?focus=all")
    _http("a_facts", "GET", f"{att}/facts")
    _http("a_project_open", "GET", f"{mm}/project/open")
    so, options, so_ms = _http("a_run_setup_options", "GET",
                               f"{mm}/run-setup/options", timeout=300)
    cur = (options or {}).get("current_data") or {}
    snapshot_now = cur.get("snapshot_token")
    _ev("a_snapshot_now", True, snapshot_token=snapshot_now)
    _http("a_runs_list", "GET", f"{mm}/runs")
    disk_state(pid, "baseline")

    # ── Phase B 复现（或 Phase V 重验）：同一幂等键重放 ──────────────
    idem = R19D_IDEM
    snap = R19D_SNAPSHOT  # 与 registry 行指纹一致（重放分支要求同指纹）
    body = {
        "mode": "daily",
        "execution_basis": "full",
        "current_snapshot_token": snap,
        "risk_rule_tokens": [],
        "idempotency_key": idem,
    }
    _ev("prepare_input", True, replay_key=idem, snapshot=snap,
        fresh_key=False, note="界面同键重放（registry replay 分支补完同一运行）")
    ps, pbody, ps_ms = _http(
        "prepare_and_start", "POST", f"{mm}/runs/prepare-and-start",
        json_body=body, timeout=600)
    disk_state(pid, "after_prepare")

    if not VERIFY:
        # 复现模式：对照同一时刻后端状态（口径差证据）
        _http("b_mapping_candidates", "GET", f"{att}/mapping-candidates?focus=all")
        _http("b_facts", "GET", f"{att}/facts")
        _http("b_project_open", "GET", f"{mm}/project/open")
        code = (pbody or {}).get("code") or ((pbody or {}).get("detail") or {}).get("code")
        print(f"\n=== 复现结论: http={ps} code={code} elapsed={ps_ms}ms", flush=True)
        return 0

    # ── Phase V 重验：progress → publication → result ─────────────────
    run_token = (pbody or {}).get("public_run_token") or "run:0bf83a78bae2a60856267103"
    _ev("run_token", True, run_token=run_token)
    deadline = time.monotonic() + 7200
    prog = {}
    run_state = ""
    while time.monotonic() < deadline:
        gs, prog, _ = _http("run_progress", "GET",
                            f"{mm}/runs/{run_token}/progress", timeout=120)
        run_state = str((prog or {}).get("run_state") or "")
        if run_state in ("completed", "failed", "ended_incomplete"):
            break
        time.sleep(15)
    _ev("run_final_state", run_state == "completed", run_state=run_state,
        result_available=bool((prog or {}).get("result_available")))
    if run_state != "completed":
        return 2

    pub_idem = f"r19s-pub-{uuid.uuid4().hex[:12]}"
    pubs, pub, _ = _http(
        "publication_post", "POST", f"{mm}/runs/{run_token}/publication",
        json_body={"idempotency_key": pub_idem}, timeout=300)
    pub_state = str((pub or {}).get("publication_state") or "")
    if pub_state != "available":
        deadline2 = time.monotonic() + 600
        while time.monotonic() < deadline2 and pub_state != "available":
            time.sleep(10)
            _, pub2, _ = _http("publication_get", "GET",
                               f"{mm}/runs/{run_token}/publication")
            pub_state = str((pub2 or {}).get("publication_state") or "")
    _ev("publication_state", pub_state == "available", publication_state=pub_state)

    es, entry, _ = _http(
        "result_entry", "GET",
        f"{mm}/runs/{run_token}/result-entry", timeout=120)
    rct = str((entry or {}).get("result_context_token") or "")
    _ev("result_entry_read", es == 200 and bool(rct),
        http=es, result_context_token=rct,
        keys=sorted(list((entry or {}).keys()))[:12])
    disk_state(pid, "final")
    print(f"\n=== 重验结论: run={run_state} pub={pub_state} "
          f"entry_http={es} rct={rct[:40]}", flush=True)
    return 0 if (run_state == "completed" and pub_state == "available"
                 and es == 200 and rct) else 2


if __name__ == "__main__":
    sys.exit(main())
