"""R29 攻坚复现驱动（第1次）：常驻开考项目「MX循开考-CSU」运行启动死锁复测。

背景：R28 轮次修复（4b9338ca：R28-01/02/03/04/07，读取链整值浮点规范等）+
R28 轮次归档（a9fa52c2）重建后，backend_build_id 变为 api-3cc7a71cf1e003d7
（R28 攻坚收尾时 api-75f010c43fde3f82），前端 runtime-build.json
expectedBackendBuildId 配对一致，8911（pid 62965，04:57 起）/5178（pid 62430，
04:53 起）为重启后进程。R28 轮次修复首次触及结果读取链（journey digest
浮点/facts 解析/envelope 兜底）——本轮按任务①独立复现当前 build 下全链
（含 results/{rct}/overview 读数核对），不信任日志。

  Phase A 基线：runtime-readiness + 同一时刻双侧状态（mapping/facts/project/
               open/protocol-versions/runs + 磁盘 launch_registry/
               profile_layer_versions）。
  Phase B 全链（任务书口径，全新幂等键=用户下一次日常监查的常规路径）：
    run-setup/options → workspace/bootstrap（任务书列名步骤；实证记录其
    行为——界面路径从不调用它，此处仅留证）→ runs/prepare-and-start →
    progress 轮询至终态 → publication → available → result-entry →
    results/{rct}/overview 可读。
  任一步被拒/卡住：立即对照同一时刻 mapping/facts/project/open/protocol-
  versions（口径差证据）。第二遍调用=任务③重验。

用法：python3 r29s_siege_repro.py
证据：r29s_siege_evidence.jsonl（每请求一条 JSONL）。
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
EVIDENCE = HERE / "r29s_siege_evidence.jsonl"

RUNTIME = (
    "/Users/smkzw/Documents/康哲项目资料/AI/医学经理工作台"
    "/implementation/workbench/runs/tester_loop_iso_20260928/runtime"
)
WS = f"{RUNTIME}/medical_monitoring_r7"

s = requests.Session()


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _ev(step: str, ok: bool, **kv) -> None:
    rec = {"ts": _now(), "step": step, "ok": bool(ok)}
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
        "SELECT sequence, run_state, result_available, "
        "substr(manifest_digest,1,12) mdig, idempotency_key, created_at, "
        "updated_at FROM r7_launch_registry ORDER BY sequence",
    )
    prof_rows = _sqlite_rows(
        f"{WS}/{pid}/execution_profiles.sqlite3",
        "SELECT layer_kind, scope_key, revision FROM profile_layer_versions "
        "ORDER BY rowid",
    )
    _ev(f"disk_state_{tag}", True, launch_registry_tail=lr_rows[-4:],
        n_registry_rows=len(lr_rows),
        profile_layer_versions=prof_rows)


def backend_truth(mm: str, att: str, tag: str) -> None:
    """同一时刻后端真实状态（口径差对照用）。"""
    _http(f"{tag}_mapping_candidates", "GET", f"{att}/mapping-candidates?focus=all")
    _http(f"{tag}_facts", "GET", f"{att}/facts")
    _http(f"{tag}_project_open", "GET", f"{mm}/project/open")
    _http(f"{tag}_protocol_versions", "GET", f"{mm.replace('/r7', '')}/protocol-versions")


def main() -> int:
    print(f"=== R29 siege repro @ {_now()}", flush=True)
    t_start = time.monotonic()

    # ── Phase A 基线 ──────────────────────────────────────────────────
    _http("a_runtime_readiness", "GET", f"{BASE}/api/runtime-readiness")
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
    attempt = "stg-cd69899943ba42618f589ba07a134a59"  # 常驻项目种子 attempt
    att = f"{mm}/data-admissions/{attempt}"
    backend_truth(mm, att, "a")
    _http("a_runs_list", "GET", f"{mm}/runs")
    disk_state(pid, "baseline")

    # ── Phase B 全链（任务书口径，全新幂等键） ────────────────────────
    # 步1 run-setup/options
    so, options, so_ms = _http("b1_run_setup_options", "GET",
                               f"{mm}/run-setup/options", timeout=300)
    cur = (options or {}).get("current_data") or {}
    snap = cur.get("snapshot_token")
    _ev("b1_snapshot_token", bool(snap), snapshot_token=snap, elapsed_ms=so_ms)
    if so != 200 or not snap:
        backend_truth(mm, att, "b_blocked")
        return 2

    # 步2 workspace/bootstrap（任务书列名步骤；界面路径从不调用——留证）
    bs, bbody, bs_ms = _http("b2_workspace_bootstrap", "POST",
                             f"{mm}/workspace/bootstrap", json_body={},
                             timeout=120)
    _ev("b2_bootstrap_note", True,
        note="界面链路从不调用该端点（前端零组件引用）；此处按任务书列名实测留证",
        replayed=(bbody or {}).get("replayed"),
        revision=(bbody or {}).get("revision"))

    # 步3 prepare-and-start（全新幂等键）
    idem = f"r29s-fresh-{uuid.uuid4().hex[:12]}"
    body = {
        "mode": "daily",
        "execution_basis": "full",
        "current_snapshot_token": snap,
        "risk_rule_tokens": [],
        "idempotency_key": idem,
    }
    _ev("b3_prepare_input", True, fresh_key=idem, snapshot=snap)
    ps, pbody, ps_ms = _http("b3_prepare_and_start", "POST",
                             f"{mm}/runs/prepare-and-start",
                             json_body=body, timeout=600)
    run_token = (pbody or {}).get("public_run_token") or ""
    _ev("b3_launch_result", ps == 200 and bool(run_token),
        http=ps, run_token=run_token, elapsed_ms=ps_ms)
    disk_state(pid, "after_prepare")
    if ps != 200 or not run_token:
        backend_truth(mm, att, "b_blocked")
        code = (pbody or {}).get("code") or ((pbody or {}).get("detail") or {}).get("code")
        print(f"\n=== 复现结论: BLOCKED http={ps} code={code} elapsed={ps_ms}ms",
              flush=True)
        return 2

    # 步4 progress 轮询至终态
    deadline = time.monotonic() + 7200
    prog, run_state, poll_n = {}, "", 0
    while time.monotonic() < deadline:
        gs, prog, _ = _http("b4_run_progress", "GET",
                            f"{mm}/runs/{run_token}/progress", timeout=120)
        poll_n += 1
        run_state = str((prog or {}).get("run_state") or "")
        if run_state in ("completed", "failed", "ended_incomplete"):
            break
        time.sleep(15)
    pct = (prog or {}).get("percent")
    _ev("b4_run_final_state", run_state == "completed",
        run_state=run_state, percent=pct, polls=poll_n,
        result_available=bool((prog or {}).get("result_available")))
    if run_state != "completed":
        disk_state(pid, "final")
        print(f"\n=== 复现结论: run stuck at {run_state}", flush=True)
        return 2

    # 步5 发布 → available
    pub_idem = f"r29s-pub-{uuid.uuid4().hex[:12]}"
    pubs, pub, pubs_ms = _http("b5_publication_post", "POST",
                               f"{mm}/runs/{run_token}/publication",
                               json_body={"idempotency_key": pub_idem},
                               timeout=300)
    pub_state = str((pub or {}).get("publication_state") or "")
    deadline2 = time.monotonic() + 600
    while time.monotonic() < deadline2 and pub_state != "available":
        time.sleep(10)
        _, pub2, _ = _http("b5_publication_get", "GET",
                           f"{mm}/runs/{run_token}/publication")
        pub_state = str((pub2 or {}).get("publication_state") or "")
    _ev("b5_publication_state", pub_state == "available",
        publication_state=pub_state, post_ms=pubs_ms)

    # 步6 result-entry（访问序契约：entry 先于 overview）
    es, entry, _ = _http("b6_result_entry", "GET",
                         f"{mm}/runs/{run_token}/result-entry", timeout=120)
    rct = str((entry or {}).get("result_context_token") or "")
    _ev("b6_result_entry_read", es == 200 and bool(rct),
        http=es, result_context_token=rct)

    # 步7 结果可读（overview 非空、受试者/发现数>0）
    ov_bytes, findings, subjects, risks = 0, 0, 0, 0
    if rct:
        ovs, overview, ovs_ms = _http(
            "b7_result_overview", "GET",
            f"{mm}/results/{rct}/overview", timeout=300)
        ov_bytes = len(json.dumps(overview or {}).encode("utf-8"))
        projection = (overview or {}).get("projection") or {}
        query_findings = projection.get("query_findings") or []
        current_risks = projection.get("current_risks") or []
        findings = len(query_findings)
        risks = len(current_risks)
        subjects = len({
            item.get("subject_id")
            for item in list(query_findings) + list(current_risks)
            if item.get("subject_id")
        })
        ident = (overview or {}).get("identity") or {}
        _ev("b7_result_overview_read",
            ovs == 200 and ov_bytes > 1000 and findings > 0 and subjects >= 3,
            http=ovs, overview_bytes=ov_bytes, findings=findings,
            subjects=subjects, current_risks=risks,
            identity_project=ident.get("project_ref"),
            run_token=ident.get("public_run_token"), elapsed_ms=ovs_ms)

    disk_state(pid, "final")
    total_s = int(time.monotonic() - t_start)
    chain_ok = (run_state == "completed" and pub_state == "available"
                and es == 200 and bool(rct) and ov_bytes > 1000
                and findings > 0 and subjects >= 3)
    print(f"\n=== 攻坚复现结论: chain_ok={chain_ok} run={run_state} "
          f"pub={pub_state} entry={es} rct={rct[:40]} "
          f"overview_bytes={ov_bytes} findings={findings} "
          f"subjects={subjects} total_s={total_s}", flush=True)
    return 0 if chain_ok else 2


if __name__ == "__main__":
    sys.exit(main())
