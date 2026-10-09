"""R30 攻坚复现驱动（第1次）：常驻开考项目「MX循开考-CSU」运行启动死锁复测。

背景：R29 攻坚（1c73967c，零代码改动全绿）之后，R29 测试循环修复
（6e8412ce：EventRow riskSeverityLabel 悬空引用/queue dwell 收割/首页建项
等）+ R29 轮次归档（c71bce82，HEAD）重建，backend_build_id 变为
api-0feb76ce663ae085（R29 攻坚时 api-3cc7a71cf1e003d7），前端
runtime-build.json expectedBackendBuildId 配对一致。R29 轮次修复触及前端
事件明细与 worker 收割路径——本轮按任务①在新 build 下独立复现当前全链
（不信任日志），任一步被拒/卡住即对照同刻后端 mapping/facts/project/open
口径；第二遍=任务③重验。

  Phase A 基线：runtime-readiness + 同刻双侧状态（mapping/facts/project/
               open/protocol-versions/runs + 磁盘 launch_registry/
               profile_layer_versions/admission_events 行数）。
  Phase B 全链（全新幂等键=用户下一次日常监查的常规路径，忠实界面路径
  不先 bootstrap；bootstrap 仅按任务书列名实测留证）：
    run-setup/options → workspace/bootstrap（留证）→ runs/prepare-and-start
    → progress 轮询至终态 → publication → available → result-entry →
    results/{rct}/overview 可读。
  第二遍调用=任务③重验（再一个全新幂等键）。

用法：python3 r30s_siege_repro.py
证据：r30s_siege_evidence.jsonl（每请求一条 JSONL）。
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
EVIDENCE = HERE / "r30s_siege_evidence.jsonl"

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


def admission_count(pid: str) -> int:
    path = Path(f"{WS}/{pid}/admissions/admission_events.jsonl")
    try:
        return len(path.read_text(encoding="utf-8").splitlines())
    except FileNotFoundError:
        return -1


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
        n_completed=result_rows(lr_rows),
        n_waiting_start=sum(
            1 for r in lr_rows if r.get("run_state") == "waiting_start"),
        profile_layer_versions=prof_rows,
        admission_events_lines=admission_count(pid))


def result_rows(rows):
    return sum(1 for r in rows
               if r.get("run_state") == "completed"
               and r.get("result_available") == 1)


def backend_truth(mm: str, att: str, tag: str) -> None:
    """同一时刻后端真实状态（口径差对照用）。"""
    _http(f"{tag}_mapping_candidates", "GET", f"{att}/mapping-candidates?focus=all")
    _http(f"{tag}_facts", "GET", f"{att}/facts")
    _http(f"{tag}_project_open", "GET", f"{mm}/project/open")
    _http(f"{tag}_protocol_versions", "GET", f"{mm.replace('/r7', '')}/protocol-versions")


def run_chain(mm: str, pid: str, attempt: str, pass_tag: str) -> bool:
    """单遍全链；返回 chain_ok。"""
    att = f"{mm}/data-admissions/{attempt}"
    backend_truth(mm, att, f"{pass_tag}_a_pre")

    # 步1 run-setup/options
    so, options, so_ms = _http(f"{pass_tag}_b1_run_setup_options", "GET",
                               f"{mm}/run-setup/options", timeout=300)
    cur = (options or {}).get("current_data") or {}
    snap = cur.get("snapshot_token")
    _ev(f"{pass_tag}_b1_snapshot_token", bool(snap), snapshot_token=snap,
        elapsed_ms=so_ms)
    if so != 200 or not snap:
        backend_truth(mm, att, f"{pass_tag}_blocked")
        return False

    # 步2 workspace/bootstrap（任务书列名步骤；界面路径从不调用——留证）
    bs, bbody, bs_ms = _http(f"{pass_tag}_b2_workspace_bootstrap", "POST",
                             f"{mm}/workspace/bootstrap", json_body={},
                             timeout=120)
    _ev(f"{pass_tag}_b2_bootstrap_note", True,
        note="界面链路从不调用该端点（前端零组件引用）；此处按任务书列名实测留证",
        replayed=(bbody or {}).get("replayed"),
        revision=(bbody or {}).get("revision"))

    # 步3 prepare-and-start（全新幂等键）
    idem = f"r30s-fresh-{uuid.uuid4().hex[:12]}"
    body = {
        "mode": "daily",
        "execution_basis": "full",
        "current_snapshot_token": snap,
        "risk_rule_tokens": [],
        "idempotency_key": idem,
    }
    _ev(f"{pass_tag}_b3_prepare_input", True, fresh_key=idem, snapshot=snap)
    ps, pbody, ps_ms = _http(f"{pass_tag}_b3_prepare_and_start", "POST",
                             f"{mm}/runs/prepare-and-start",
                             json_body=body, timeout=600)
    run_token = (pbody or {}).get("public_run_token") or ""
    _ev(f"{pass_tag}_b3_launch_result", ps == 200 and bool(run_token),
        http=ps, run_token=run_token, elapsed_ms=ps_ms)
    if ps != 200 or not run_token:
        backend_truth(mm, att, f"{pass_tag}_blocked")
        code = (pbody or {}).get("code") or ((pbody or {}).get("detail") or {}).get("code")
        _ev(f"{pass_tag}_BLOCKED", False, http=ps, code=code, elapsed_ms=ps_ms)
        return False

    # 步4 progress 轮询至终态
    t_run = time.monotonic()
    deadline = time.monotonic() + 7200
    prog, run_state, poll_n, ra_first = {}, "", 0, None
    while time.monotonic() < deadline:
        gs, prog, _ = _http(f"{pass_tag}_b4_run_progress", "GET",
                            f"{mm}/runs/{run_token}/progress", timeout=120)
        poll_n += 1
        run_state = str((prog or {}).get("run_state") or "")
        if ra_first is None:
            ra_first = bool((prog or {}).get("result_available"))
        if run_state in ("completed", "failed", "ended_incomplete"):
            break
        time.sleep(15)
    run_s = int(time.monotonic() - t_run)
    pct = (prog or {}).get("percent")
    _ev(f"{pass_tag}_b4_run_final_state", run_state == "completed",
        run_state=run_state, percent=pct, polls=poll_n, run_seconds=run_s,
        result_available_first_poll=ra_first,
        result_available_final=bool((prog or {}).get("result_available")))
    if run_state != "completed":
        disk_state(pid, f"final_{pass_tag}")
        _ev(f"{pass_tag}_STUCK", False, run_state=run_state)
        return False

    # 步5 发布 → available
    pub_idem = f"r30s-pub-{uuid.uuid4().hex[:12]}"
    pubs, pub, pubs_ms = _http(f"{pass_tag}_b5_publication_post", "POST",
                               f"{mm}/runs/{run_token}/publication",
                               json_body={"idempotency_key": pub_idem},
                               timeout=300)
    pub_state = str((pub or {}).get("publication_state") or "")
    deadline2 = time.monotonic() + 600
    while time.monotonic() < deadline2 and pub_state != "available":
        time.sleep(10)
        _, pub2, _ = _http(f"{pass_tag}_b5_publication_get", "GET",
                           f"{mm}/runs/{run_token}/publication")
        pub_state = str((pub2 or {}).get("publication_state") or "")
    _ev(f"{pass_tag}_b5_publication_state", pub_state == "available",
        publication_state=pub_state, post_ms=pubs_ms)

    # 步6 result-entry（访问序契约：entry 先于 overview）
    es, entry, es_ms = _http(f"{pass_tag}_b6_result_entry", "GET",
                             f"{mm}/runs/{run_token}/result-entry", timeout=120)
    rct = str((entry or {}).get("result_context_token") or "")
    _ev(f"{pass_tag}_b6_result_entry_read", es == 200 and bool(rct),
        http=es, result_context_token=rct, elapsed_ms=es_ms)

    # 步7 结果可读（overview 非空、受试者/发现数>0）
    ov_bytes, findings, subjects, risks = 0, 0, 0, 0
    if rct:
        ovs, overview, ovs_ms = _http(
            f"{pass_tag}_b7_result_overview", "GET",
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
        _ev(f"{pass_tag}_b7_result_overview_read",
            ovs == 200 and ov_bytes > 1000 and findings > 0 and subjects >= 3,
            http=ovs, overview_bytes=ov_bytes, findings=findings,
            subjects=subjects, current_risks=risks,
            identity_project=ident.get("project_ref"),
            run_token=ident.get("public_run_token"), elapsed_ms=ovs_ms)

    disk_state(pid, f"final_{pass_tag}")
    chain_ok = (run_state == "completed" and pub_state == "available"
                and es == 200 and bool(rct) and ov_bytes > 1000
                and findings > 0 and subjects >= 3)
    _ev(f"{pass_tag}_CHAIN_RESULT", chain_ok,
        run=run_state, pub=pub_state, entry=es, rct=rct[:44],
        overview_bytes=ov_bytes, findings=findings, subjects=subjects)
    return chain_ok


def main() -> int:
    print(f"=== R30 siege repro @ {_now()}", flush=True)
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
    _http("a_admission_open", "GET", f"{att}")
    _http("a_runs_list", "GET", f"{mm}/runs")
    disk_state(pid, "baseline")

    # ── Phase B 第一遍（任务①复现，全新幂等键）──────────────────────
    print("\n--- 第一遍（复现）---", flush=True)
    ok1 = run_chain(mm, pid, attempt, "p1")

    # ── Phase B 第二遍（任务③重验，再一个全新幂等键）────────────────
    print("\n--- 第二遍（重验）---", flush=True)
    ok2 = run_chain(mm, pid, attempt, "p2")

    total_s = int(time.monotonic() - t_start)
    print(f"\n=== R30 攻坚复现结论: pass1={ok1} pass2={ok2} total_s={total_s}",
          flush=True)
    return 0 if (ok1 and ok2) else 2


if __name__ == "__main__":
    sys.exit(main())
