"""R44 攻坚复现驱动（第1次）：常驻开考项目「MX循开考-CSU」运行链全链复测。

背景：R43 攻坚两遍全绿（零修复）之后，R43 修复员六条修复（6cc49583：
R43-01 研究文件核对作业队列任务类型插队认领、R43-02 重新核对 dwell
重置+受理回执、R41-03 内容差异确认挂起文案、R41-04 准备状态矛盾口径、
R40-04 总看板双口径标注、R40-05 MH域空术语+MH→CM方向新发现行——
**触运行链投影**：facts_publication.py 新增 MH 域发现行）+ 轮次归档
（1c916a9b）之后，8911 pid 90569 于 2026-10-14 07:23:55 CST 拉起
（backend_build_id=api-31cbdf421a25007a）、5178（vite，[::1] 监听，
runtime-build.json expectedBackendBuildId 配对一致）。本轮 = 6cc49583
新代码面在役下的首次运行链复测。

漂移预期（6cc49583 提交说明原句：「R40-05使合成/真实项目的MH域产生新
发现行（空术语+甲减缺药）——下次发布投影与content_hash将按新投影漂移，
属修复预期行为」）：
  - 新增 findings 应全部落在 `facts-finding-event-MH-*` 族（R40-05 两类
    注记：缺诊断名称 / 病史-用药一致性待核实）；任何非 MH 族新发现=未
    预期漂移，须钉代码行。
  - current_risks 集合预期不变（R40-05 只加 findings 不加风险实例）。
  - 共有 findings（SV/CM/AE 族）按 finding_id 键控逐字段零漂移预期。
  - content_hash 预期变化（新发现行 + query_draft_id 含 run_id 的既有
    逐运行漂移，R43 §3 已完备归因）。

  Phase A 基线：runtime-readiness + 项目定位 + 同刻双侧状态（mapping/
               facts/project/open/protocol-versions/runs + 磁盘
               launch_registry/profile_layer_versions/admission_events）。
  Phase B 全链（全新幂等键=用户下一次日常监查的常规路径，忠实界面路径
  不先 bootstrap；bootstrap 仅按任务书列名实测留证）：
    run-setup/options → workspace/bootstrap（留证）→ runs/prepare-and-start
    → progress 轮询至终态 → publication → available → result-entry →
    results/{rct}/overview 可读（entry 与 overview 两次独立读取+缓存探针）
    → 与 r43s_overview_p1.json 逐项比对（按上述漂移预期归因）。
    overview 全文落盘 r44s_overview_{p1,p2}.json 供归档。
  第一遍=任务①复现；第二遍=任务③重验。

用法：python3 r44s_siege_repro.py
证据：r44s_siege_evidence.jsonl（每请求一条 JSONL）。
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
EVIDENCE = HERE / "r44s_siege_evidence.jsonl"
BASELINE = HERE / "r43s_overview_p1.json"

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


def result_rows(rows):
    return sum(1 for r in rows
               if r.get("run_state") == "completed"
               and r.get("result_available") == 1)


def disk_state(pid: str, tag: str) -> None:
    lr_rows = _sqlite_rows(
        f"{WS}/{pid}/launch_registry.sqlite3",
        "SELECT sequence, run_state, result_available, "
        "substr(manifest_digest,1,12) mdig, request_fingerprint, "
        "idempotency_key, created_at, updated_at "
        "FROM r7_launch_registry ORDER BY sequence",
    )
    prof_rows = _sqlite_rows(
        f"{WS}/{pid}/execution_profiles.sqlite3",
        "SELECT layer_kind, scope_key, revision FROM profile_layer_versions "
        "ORDER BY rowid",
    )
    fps = sorted({r.get("request_fingerprint") for r in lr_rows
                  if r.get("request_fingerprint")})
    _ev(f"disk_state_{tag}", True, launch_registry_tail=lr_rows[-4:],
        n_registry_rows=len(lr_rows),
        n_completed=result_rows(lr_rows),
        n_waiting_start=sum(
            1 for r in lr_rows if r.get("run_state") == "waiting_start"),
        request_fingerprints=fps,
        profile_layer_versions=prof_rows,
        admission_events_lines=admission_count(pid))


def backend_truth(mm: str, att: str, tag: str) -> None:
    """同一时刻后端真实状态（口径差对照用）。"""
    _http(f"{tag}_mapping_candidates", "GET", f"{att}/mapping-candidates?focus=all")
    _http(f"{tag}_facts", "GET", f"{att}/facts")
    _http(f"{tag}_project_open", "GET", f"{mm}/project/open")
    _http(f"{tag}_protocol_versions", "GET", f"{mm.replace('/r7', '')}/protocol-versions")


def load_baseline():
    if not BASELINE.exists():
        return None
    return json.loads(BASELINE.read_text(encoding="utf-8"))


def compare_to_baseline(overview: dict, tag: str) -> None:
    """与 R43 基线（r43s_overview_p1.json，api-616662809274f9f0 投影面）
    比对并按 6cc49583 预期归因。

    预期：新发现全落 MH 族（R40-05）；risks 集合不变；共有 findings
    键控零漂移；content_hash 变化（新行+run_id 逐运行既有漂移）。
    任何非 MH 族新发现 / risks 集合变化 / 共有字段漂移 = 未预期，钉行。
    """
    base = load_baseline()
    if not base:
        _ev(f"{tag}_baseline_compare", False, note="基线文件缺失，无法比对")
        return
    bp, cp = base.get("projection") or {}, overview.get("projection") or {}
    bf = {f.get("finding_id") for f in bp.get("query_findings") or []}
    cf = {f.get("finding_id") for f in cp.get("query_findings") or []}
    br = {r.get("risk_instance_ref") for r in bp.get("current_risks") or []}
    cr = {r.get("risk_instance_ref") for r in cp.get("current_risks") or []}
    fmap_b = {f.get("finding_id"): {k: v for k, v in f.items()
                                    if k != "query_draft_id"}
              for f in bp.get("query_findings") or []}
    fmap_c = {f.get("finding_id"): {k: v for k, v in f.items()
                                    if k != "query_draft_id"}
              for f in cp.get("query_findings") or []}
    fdiff_fields: dict[str, list] = {}
    for fid in sorted(fmap_b.keys() & fmap_c.keys()):
        if fmap_b[fid] != fmap_c[fid]:
            keys = {k for k in set(fmap_b[fid]) | set(fmap_c[fid])
                    if fmap_b[fid].get(k) != fmap_c[fid].get(k)}
            fdiff_fields[fid] = sorted(keys)
    rmap_b = {r.get("risk_instance_ref"): r
              for r in bp.get("current_risks") or []}
    rmap_c = {r.get("risk_instance_ref"): r
              for r in cp.get("current_risks") or []}
    rdiff_fields: dict[str, list] = {}
    for rid in sorted(rmap_b.keys() & rmap_c.keys()):
        if rmap_b[rid] != rmap_c[rid]:
            keys = {k for k in set(rmap_b[rid]) | set(rmap_c[rid])
                    if rmap_b[rid].get(k) != rmap_c[rid].get(k)}
            rdiff_fields[rid] = sorted(keys)
    new_ids = sorted(cf - bf)
    gone_ids = sorted(bf - cf)
    new_families: dict[str, int] = {}
    for fid in new_ids:
        fam = fid.rsplit("-", 1)[0]
        new_families[fam] = new_families.get(fam, 0) + 1
    non_mh_new = [fid for fid in new_ids if "-MH-" not in fid]
    # 新 MH 发现的 issue/locator 归因样本（对照 R40-05 两类注记）
    cby = {f.get("finding_id"): f for f in cp.get("query_findings") or []}
    new_samples = [
        {k: cby[fid].get(k) for k in ("finding_id", "issue_id", "subject_id")}
        for fid in new_ids[:8]
    ]
    content_hash_b, content_hash_c = bp.get("content_hash"), cp.get("content_hash")
    as_expected = (
        not non_mh_new and not gone_ids and br == cr
        and not fdiff_fields and not rdiff_fields
    )
    _ev(f"{tag}_baseline_compare", as_expected,
        expectation="新增全MH族+risks不变+共有零漂移；content_hash变化为预期",
        n_findings_base=len(bf), n_findings_current=len(cf),
        n_new=len(new_ids), new_families=new_families,
        non_mh_new=non_mh_new[:8], gone_ids=gone_ids[:8],
        new_samples=new_samples,
        risks_set_equal=br == cr,
        n_risks_base=len(br), n_risks_current=len(cr),
        n_findings_field_drift=len(fdiff_fields),
        findings_drift_fields=dict(list(fdiff_fields.items())[:6]),
        n_risks_field_drift=len(rdiff_fields),
        risks_drift_fields=dict(list(rdiff_fields.items())[:6]),
        content_hash_baseline=content_hash_b, content_hash_current=content_hash_c,
        content_hash_changed=content_hash_b != content_hash_c)


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
        http=bs, replayed=(bbody or {}).get("replayed"),
        revision=(bbody or {}).get("revision"), elapsed_ms=bs_ms)

    # 步3 prepare-and-start（全新幂等键）
    idem = f"r44s-fresh-{uuid.uuid4().hex[:12]}"
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
    pub_idem = f"r44s-pub-{uuid.uuid4().hex[:12]}"
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

    # 步7 结果可读（overview 非空、受试者/发现数>0；与 R43 基线比对按
    # 6cc49583 预期归因——新发现全 MH 族、risks 不变、共有零漂移）
    ov_bytes, findings, subjects, risks = 0, 0, 0, 0
    if rct:
        ovs, overview, ovs_ms = _http(
            f"{pass_tag}_b7_result_overview", "GET",
            f"{mm}/results/{rct}/overview", timeout=300)
        (HERE / f"r44s_overview_{pass_tag}.json").write_text(
            json.dumps(overview, ensure_ascii=False, indent=1),
            encoding="utf-8")
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
            snapshot_token=ident.get("snapshot_token"),
            content_hash=projection.get("content_hash"),
            run_token=ident.get("public_run_token"), elapsed_ms=ovs_ms)
        # 缓存在役实证：紧随其后的第二次读取（同 rct，缓存应命中）
        ovs2, overview2, ovs2_ms = _http(
            f"{pass_tag}_b7b_result_overview_cached", "GET",
            f"{mm}/results/{rct}/overview", timeout=300)
        ov2_bytes = len(json.dumps(overview2 or {}).encode("utf-8"))
        _ev(f"{pass_tag}_b7b_cache_probe",
            ovs2 == 200 and ov2_bytes == ov_bytes,
            http=ovs2, first_read_ms=ovs_ms, second_read_ms=ovs2_ms,
            bytes_equal=ov2_bytes == ov_bytes)
        # 与 R43 基线逐项比对（按 6cc49583 漂移预期归因）
        compare_to_baseline(overview, pass_tag)

    disk_state(pid, f"final_{pass_tag}")
    chain_ok = (run_state == "completed" and pub_state == "available"
                and es == 200 and bool(rct) and ov_bytes > 1000
                and findings > 0 and subjects >= 3)
    _ev(f"{pass_tag}_CHAIN_RESULT", chain_ok,
        run=run_state, pub=pub_state, entry=es, rct=rct[:44],
        overview_bytes=ov_bytes, findings=findings, subjects=subjects)
    return chain_ok


def main() -> int:
    print(f"=== R44 siege repro @ {_now()}", flush=True)
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
    print(f"\n=== R44 攻坚复现结论: pass1={ok1} pass2={ok2} total_s={total_s}",
          flush=True)
    return 0 if (ok1 and ok2) else 2


if __name__ == "__main__":
    sys.exit(main())
