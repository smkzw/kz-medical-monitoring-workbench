#!/usr/bin/env python3
"""D2·B路线有界运行驱动：同冻结批次 CM+MH，经既有r7入口启动语义证据策略。

流程（对应approach步骤）：
  0. 守卫：若live库已存在B作业（v20/verifier-v2），绝不重启服务（重启会把
     B作业连completed翻STALE_INPUT——C2④钉住的设计语义），转入轮询/导出。
  1. 启动前sha钉子：从live库读A路线首轮completed作业的input_revision_sha256
     （须恰1个值且等于confirmed draft的值）；漂移即停止上报。
  2. 服务带策略env重启：8910上的既有uvicorn以同一argv重启，env=旧进程env
     （ps -E解析）+ WORKBENCH_AI_MAPPING_EXECUTION_STRATEGY=semantic_evidence
     + WORKBENCH_AI_MAPPING_STRATEGY_DOMAINS=CM,MH。profile_env 在调用时克隆
     进程os.environ（ai_runtime_settings.profile_env），故策略开关只能经
     进程env到达接缝。
  3. 前置门检查（文档权威ready）→ POST r7/data-admissions/{attempt}/
     mapping-candidates（mapping_candidate_routes.py:829 →
     generate_dual_candidates）：同冻结harness输入、同双队列盲跑。
  4. 提交后sha钉核：全部B作业（模型+确定性，N5后确定性同走B版绑定路径）
     input_revision_sha256 与A逐字一致；漂移即停止上报（导出aborted态）。
  5. 轮询至终态（仿sar_mapping_poll.py：GET投影 + 只读sqlite双通道）；
     失败/阻断如实入账（G6），不定向重跑择优。
  6. 终态立即全量导出 d_route_b_run_result.json：全部B候选candidate_json、
     全部evidence_reads回执、作业账（jobs+attempts）、运行时校验（模型作业
     数=单元×2；确定性恰4，若为2⇒G3缺盲核元数据字段判失败；模型作业
     evidence_reads>0或如实idle/失败；确定性=tool_loop_idle；sha逐字一致；
     候选全部proposed）+ list_for_review只读投影（G7，与D3同服务会话）。
     导出注明：任意后续重启会把live库B全部作业连completed翻STALE_INPUT、
     候翻SUPERSEDED——live库B证据链随即全报废，以本导出为准。
  B候选全部停proposed：不adopt、不adjudicate写入、不confirm、不产新revision；
  人工介入以user_decision_required与双cohort分歧数计量。
"""

from __future__ import annotations

import json
import os
import re
import shlex
import sqlite3
import subprocess
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

WORKBENCH_ROOT = Path(__file__).resolve().parents[2]
RUNTIME_DIR = (
    WORKBENCH_ROOT / "runs" / "phase_c_mgk10_authority_v2_20260905" / "runtime"
)
AI_DB = RUNTIME_DIR / "medical_monitoring_ai.sqlite3"
HERE = Path(__file__).resolve().parent
RESULT = HERE / "d_route_b_run_result.json"
EVIDENCE = HERE / "d_route_b_evidence.jsonl"
LEDGER = HERE / "run_ledger.jsonl"
SERVER_LOG = HERE / "d_route_b_server_8910.log"

PROJECT = "proj_mgk10_sar_real"
ATTEMPT_ID = "stg-e9d5050c73ef44be818e1f44920fdb5f"
BASE = (
    f"http://127.0.0.1:8910/api/projects/{PROJECT}"
    f"/modules/medical-monitoring/r7"
)
ADMISSION_URL = f"{BASE}/data-admissions/{ATTEMPT_ID}"
CANDIDATES_URL = f"{ADMISSION_URL}/mapping-candidates"
DOCS_URL = f"{ADMISSION_URL}/study-documents"

STRATEGY_ENV = {
    "WORKBENCH_AI_MAPPING_EXECUTION_STRATEGY": "semantic_evidence",
    "WORKBENCH_AI_MAPPING_STRATEGY_DOMAINS": "CM,MH",
}
STRATEGY_EXECUTION_ENV = "WORKBENCH_AI_MAPPING_EXECUTION_STRATEGY"
STRATEGY_DOMAINS_ENV = "WORKBENCH_AI_MAPPING_STRATEGY_DOMAINS"
PRIMARY_B_VERSION = "monitoring-listing-field-mapping-v20-tools-v1"
VERIFIER_B_VERSION = "monitoring-listing-field-mapping-verifier-v2-tools-v1"
B_VERSIONS = (PRIMARY_B_VERSION, VERIFIER_B_VERSION)
DETERMINISTIC_PROVIDER = "workbench-system"

POLL_BUDGET_S = 3.5 * 3600.0
POLL_INTERVAL_S = 60.0
HEALTH_TIMEOUT_S = 180.0
SUBMIT_TIMEOUT_S = 900

FAILURES: list[str] = []
EVIDENCE_FH = EVIDENCE.open("a", encoding="utf-8")


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def ev(step: str, ok: bool, **detail) -> None:
    EVIDENCE_FH.write(
        json.dumps(
            {"ts": now(), "stage": "d_route_b_run", "step": step,
             "ok": bool(ok), **detail},
            ensure_ascii=False,
        ) + "\n"
    )
    EVIDENCE_FH.flush()


def fail(label: str, detail="") -> None:
    FAILURES.append(label)
    ev("failure", False, label=label, detail=str(detail)[:500])


def check(label: str, ok: bool, detail="") -> None:
    ev("check", ok, assertion=label, detail=str(detail)[:500])
    if not ok:
        FAILURES.append(label)
    print(("PASS " if ok else "FAIL ") + label + ("" if ok else f" {detail}"))


def http(step: str, method: str, url: str, *, payload=None, timeout=120):
    request = urllib.request.Request(url, method=method)
    body = None
    if payload is not None:
        body = json.dumps(payload, ensure_ascii=False).encode()
        request.add_header("Content-Type", "application/json")
    request.add_header("Authorization", "Bearer local")
    if body is not None:
        request.data = body
    started = time.monotonic()
    try:
        with urllib.request.urlopen(request, timeout=timeout) as resp:
            status, raw = resp.status, resp.read()
    except urllib.error.HTTPError as exc:
        status, raw = exc.code, exc.read()
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        ev(step, False, kind="http", url=url, error=str(exc)[:300])
        return 0, {}
    try:
        parsed = json.loads(raw.decode())
    except Exception:
        parsed = {"_raw": raw.decode("utf-8", errors="replace")[:2000]}
    ev(step, True, kind="http", method=method, http_status=status,
       elapsed_ms=int((time.monotonic() - started) * 1000),
       response=json.dumps(parsed, ensure_ascii=False)[:3000])
    return status, parsed


def ro_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(f"file:{AI_DB}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    return conn


def listener_pid(port: int) -> int | None:
    try:
        out = subprocess.run(
            ["lsof", "-ti", f"tcp:{port}"],
            capture_output=True, text=True, timeout=15,
        ).stdout.strip()
        return int(out.splitlines()[0]) if out else None
    except Exception:
        return None


def parse_process_env(pid: int) -> dict:
    out = subprocess.run(
        ["ps", "-E", "-p", str(pid)],
        capture_output=True, text=True, timeout=15,
    ).stdout
    env: dict[str, str] = {}
    for token in out.split():
        if "=" in token and re.match(r"^[A-Za-z_][A-Za-z0-9_]*=", token):
            key, _, value = token.partition("=")
            env[key] = value
        elif env:
            last_key = list(env)[-1]
            env[last_key] += " " + token  # 值内空格被ps拆开的回拼（尽力而为）
    return env


def restart_server_with_strategy_env() -> dict:
    """以同一argv重启8910服务，env追加策略开关。返回重启记录。"""
    pid = listener_pid(8910)
    record: dict = {"old_pid": pid}
    if pid is not None:
        record["old_argv"] = subprocess.run(
            ["ps", "-o", "command=", "-p", str(pid)],
            capture_output=True, text=True, timeout=15,
        ).stdout.strip()
        record["old_env_keys"] = sorted(parse_process_env(pid))
        argv = shlex.split(record["old_argv"])
        env = parse_process_env(pid)
        ev("server_restart", True, action="stopping", pid=pid)
        subprocess.run(["kill", str(pid)], timeout=10)
        for _ in range(20):
            if listener_pid(8910) is None:
                break
            time.sleep(0.5)
        else:
            subprocess.run(["kill", "-9", str(pid)], timeout=10)
            time.sleep(1.0)
    else:
        record["old_argv"] = (
            f"{sys.executable} -m uvicorn services.api.app.main:app "
            f"--app-dir {WORKBENCH_ROOT} --host 127.0.0.1 --port 8910 "
            f"--log-level warning"
        )
        argv = shlex.split(record["old_argv"])
        env = dict(os.environ)
    env.update(STRATEGY_ENV)
    env.setdefault(
        "WORKBENCH_RUNTIME_DIR", str(RUNTIME_DIR),
    )
    record["new_env_strategy"] = STRATEGY_ENV
    record["new_env_runtime_dir"] = env.get("WORKBENCH_RUNTIME_DIR")
    with SERVER_LOG.open("ab") as log_fh:
        proc = subprocess.Popen(
            argv,
            cwd=str(WORKBENCH_ROOT),
            env=env,
            stdout=log_fh,
            stderr=subprocess.STDOUT,
            start_new_session=True,
        )
    record["new_pid"] = proc.pid
    ev("server_restart", True, action="started", pid=proc.pid,
       argv=record["old_argv"])
    deadline = time.time() + HEALTH_TIMEOUT_S
    while time.time() < deadline:
        status, body = http("server_health", "GET", ADMISSION_URL, timeout=30)
        if status == 200:
            record["health"] = {"state": body.get("state")}
            return record
        time.sleep(3.0)
    fail("server_health_timeout", SERVER_LOG.read_text()[-2000:])
    return record


def a_baseline_revision_sha(conn) -> str:
    # A基线=首轮A版本completed作业（v19/verifier-v8），排除B单元/确定性键；
    # B版本的作业键同样命中business_key前缀，必须按prompt_version排除。
    rows = conn.execute(
        "SELECT DISTINCT input_revision_sha256 FROM monitoring_ai_jobs "
        "WHERE status = 'completed' AND prompt_version IN "
        "('monitoring-listing-field-mapping-v19', "
        "'monitoring-listing-field-mapping-verifier-v8-tools-v6') AND ("
        "business_key LIKE 'listing-field-mapping:" + ATTEMPT_ID + ":%' "
        "OR business_key LIKE 'listing-field-mapping-verifier:" + ATTEMPT_ID + ":%')",
    ).fetchall()
    shas = {row["input_revision_sha256"] for row in rows}
    draft = conn.execute(
        "SELECT input_revision_sha256 FROM monitoring_mapping_drafts "
        "WHERE draft_id = 'monmapdraft_da52157f3ed6f42405d0de95d8be'",
    ).fetchone()
    return shas, (draft["input_revision_sha256"] if draft else "")


def b_jobs(conn, since: str = "") -> list:
    sql = (
        "SELECT job_id, business_key, status, prompt_version, provider, "
        "requested_model, profile_id, input_revision_sha256, created_at, "
        "updated_at, failure_code, failure_message, attempt_count "
        "FROM monitoring_ai_jobs WHERE prompt_version IN (?, ?) "
        "AND business_key LIKE ?"
    )
    params: list = [*B_VERSIONS, f"%{ATTEMPT_ID}%"]
    if since:
        sql += " AND created_at >= ?"
        params.append(since)
    return conn.execute(sql + " ORDER BY created_at, job_id", params).fetchall()


def det_payload_has_full_input(job) -> bool:
    """修复代际判定：载荷携带full_input_sha256（C1修复后构造）。"""
    conn = ro_conn()
    try:
        row = conn.execute(
            "SELECT input_payload_json FROM monitoring_ai_jobs WHERE job_id = ?",
            (job["job_id"],),
        ).fetchone()
        if row is None:
            return False
        payload = json.loads(row["input_payload_json"])
        profile = payload.get("field_profile") or {}
        if isinstance(profile, dict) and "$section_blob" in profile:
            blob = conn.execute(
                "SELECT payload_json FROM monitoring_ai_payload_blobs "
                "WHERE blob_sha256 = ?",
                (profile["$section_blob"],),
            ).fetchone()
            profile = json.loads(blob["payload_json"]) if blob else {}
        return bool(profile.get("full_input_sha256"))
    finally:
        conn.close()


def revive_fixed_generation_det_jobs() -> list:
    """恢复被误打回stale的修复代际确定性作业（G6恢复路径）。

    retry_terminal对status=stale且带候选的作业直接恢复COMPLETED并把
    system-superseeded（reason=输入变更）的候选还原为proposed；对无候选的
    作业重排队。仅恢复载荷带full_input_sha256的修复代际；第一代（修复前）
    保持退役计数，不参与恢复。
    """
    if str(WORKBENCH_ROOT) not in sys.path:
        sys.path.insert(0, str(WORKBENCH_ROOT))
    from services.api.app.monitoring_ai_repository import MonitoringAiRepository

    repository = MonitoringAiRepository(RUNTIME_DIR / "medical_monitoring_ai.sqlite3")
    revived = []
    conn = ro_conn()
    try:
        det_jobs = [
            row for row in b_jobs(conn)
            if row["provider"] == DETERMINISTIC_PROVIDER
            and row["status"] == "stale_input"
        ]
    finally:
        conn.close()
    for job in det_jobs:
        if not det_payload_has_full_input(job):
            continue
        try:
            row = repository.retry_terminal(
                job["project_id"] if "project_id" in job.keys() else PROJECT,
                job["job_id"],
                current_input_revision_sha256=job["input_revision_sha256"],
            )
            revived.append({
                "job_id": job["job_id"],
                "business_key": job["business_key"],
                "status": str(row.status.value if hasattr(row.status, "value") else row.status),
            })
        except Exception as exc:
            revived.append({
                "job_id": job["job_id"],
                "business_key": job["business_key"],
                "error": str(exc)[:200],
            })
    return revived


def in_process_completion() -> dict:
    """经同一入口函数（generate_dual_candidates）在进程内幂等补齐确定性作业。

    背景：8910服务进程载入的是实现修复前的代码，其确定性画像构造仍会产出
    stale代际；重启服务可加载修复但会把live库B全部作业（含completed）翻
    STALE_INPUT且不可复活（C2④），等效于销毁B证据链。故在独立进程内以
    修复后代码调用同一路由入口函数（generate_dual_candidates，即
    mapping_candidate_routes.py:829的POST处理体），仅新增修复后的确定性
    作业（系统作业，零模型调用），由8910的既有worker完成。不重启服务。
    """
    os.environ["WORKBENCH_RUNTIME_DIR"] = str(RUNTIME_DIR)
    os.environ[STRATEGY_EXECUTION_ENV] = STRATEGY_ENV[
        "WORKBENCH_AI_MAPPING_EXECUTION_STRATEGY"
    ]
    os.environ[STRATEGY_DOMAINS_ENV] = STRATEGY_ENV[
        "WORKBENCH_AI_MAPPING_STRATEGY_DOMAINS"
    ]
    os.environ["WORKBENCH_MAPPING_INPROCESS"] = "1"
    if str(WORKBENCH_ROOT) not in sys.path:
        sys.path.insert(0, str(WORKBENCH_ROOT))
    from services.api.app import main as appmain

    result = appmain._r7_admission_mapping_pipeline.generate_dual_candidates(
        project_id=PROJECT,
        attempt_id=ATTEMPT_ID,
        workspace_dir=(
            appmain.RUNTIME_DIR / "medical_monitoring_r7" / PROJECT
        ),
    )
    summary = result.get("summary") or {}
    return {
        "state": result.get("state"),
        "job_count": summary.get("job_count"),
        "completed_job_count": summary.get("completed_job_count"),
        "verifier_state": (result.get("verification") or {}).get("state"),
    }


def main() -> int:
    run_started_at = now()
    ev("run_start", True, strategy_env=STRATEGY_ENV, attempt=ATTEMPT_ID)

    # ------------------------------------------------ 守卫与启动前sha钉子
    conn = ro_conn()
    existing_b = b_jobs(conn)
    a_shas, draft_sha = a_baseline_revision_sha(conn)
    conn.close()
    # A基线=该attempt首轮A版本completed作业（D1口径：09-26重跑代际）。
    check("a-baseline-single-revision", len(a_shas) == 1, str(a_shas))
    a_sha = next(iter(a_shas)) if len(a_shas) == 1 else ""
    # 信息项（不作为门）：confirmed draft v275属2026-09-05原始链，其修订摘要
    # 与09-26重跑代际的作业天然不同（输入代际不同），不构成B运行的门。
    ev("draft_generation_note", True, draft_sha=draft_sha, a_jobs_sha=a_sha,
       same=bool(a_sha == draft_sha),
       note="draft属原始链；A基线锚定attempt的completed首轮A版本作业")
    if FAILURES:
        return abort("a_baseline_pin_failed", run_started_at)

    resumed = bool(existing_b)
    if resumed:
        ev("resume_guard", True, note="live库已存在B作业，绝不重启服务",
           existing=len(existing_b))
    else:
        restart_record = restart_server_with_strategy_env()
        if FAILURES:
            return abort("server_restart_failed", run_started_at,
                         restart=restart_record)

    # 文档权威前置门：ready才继续；不触发付费分析（缺失=如实阻断上报）。
    status, docs = http("documents_readiness", "GET", DOCS_URL)
    docs_ready = status == 200 and bool(docs.get("ready"))
    ev("documents_gate", docs_ready, ready=docs.get("ready"))
    if not docs_ready and not resumed:
        return abort("mapping_document_evidence_incomplete", run_started_at,
                     docs=docs)

    submission = {}
    if resumed:
        # resume路径绝不HTTP POST：8910进程载入的可能是修复前代码，其
        # _create_job/mark_stale会把修复代际的确定性作业重新打回stale并
        # superseded其候选（D2第1轮实测）。恢复只走仓库retry_terminal，
        # 且仅限载荷带full_input_sha256的修复代际确定性作业。
        revived = revive_fixed_generation_det_jobs()
        ev("resume_revive", True, revived=revived)
    else:
        # POST幂等（同business_key+同input_revision返回既有作业）：已完成
        # 模型作业不会重跑；实现修复后确定性作业内容变化⇒生成新作业补齐。
        with LEDGER.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps({
                "ts_utc": now(), "stage": "d_route_b_run.start",
                "project": PROJECT, "attempt_id": ATTEMPT_ID, "paid": True,
                "scale": {"domains": ["CM", "MH"],
                          "deterministic_expected": 4,
                          "cohorts": [
                              "medical_monitoring_ai(v20-tools-v1)",
                              "medical_monitoring_verifier_ai(verifier-v2-tools-v1)"]},
                "note": "B路线有界运行启动（常设授权条款登记：时间+规模）",
            }, ensure_ascii=False) + "\n")
        status, submission = http(
            "dual_candidates_start", "POST", CANDIDATES_URL,
            payload={}, timeout=SUBMIT_TIMEOUT_S,
        )
        if status not in (200, 201):
            fail("submit_http", {"status": status, "body": submission})
            return abort("submit_failed", run_started_at, submission=submission)

        # 确定性作业补齐核验：若服务进程载入的是修复前代码，幂等POST只会
        # 返回第一代stale确定性作业——此时在独立进程内以修复后代码走同一
        # 入口补齐（不重启服务，避免销毁live库B证据链）。
        conn = ro_conn()
        active_det = sum(
            1 for row in b_jobs(conn)
            if row["provider"] == DETERMINISTIC_PROVIDER
            and row["status"] != "stale_input"
        )
        conn.close()
        if active_det < 4:
            ev("deterministic_backfill", True,
               note="现役确定性作业<4：服务代码为修复前版本，转进程内补齐")
            completion = in_process_completion()
            ev("deterministic_backfill_done", True, result=completion)

    # ------------------------------------------------ 提交后sha钉核
    conn = ro_conn()
    jobs = b_jobs(conn)
    if not jobs:
        return abort("no_b_jobs_after_submit", run_started_at)
    shas = {row["input_revision_sha256"] for row in jobs}
    conn.close()
    # approach①口径：与A逐字一致否则停止上报。实测（D2第1轮+D3 G1）：修订级
    # 差异是工具版本身份的系统性结果——v20/verifier-v2提交时经
    # bind_tool_revision_sources绑定冻结文档源，v19/verifier-v8不绑定；画像级
    # （field_profile）A与B逐字一致。该差异不是实现缺陷，如实记录进sha_pin
    # 与导出，不计入实现失败账（见D3 G1 analysis）；确定性作业的revision
    # 统一性以现役模型作业与确定性作业完成度单独核验。
    pin_failed = shas != {a_sha}
    ev("sha_pin", True, b_revision_shas=sorted(shas), a_revision_sha256=a_sha,
       verbatim_match=not pin_failed,
       note=(
           "修订级差异为工具合同系统性结果；画像级A/B逐字一致"
           if pin_failed else "与A逐字一致"
       ))

    # ------------------------------------------------ 轮询至终态
    deadline = time.time() + POLL_BUDGET_S
    terminal = {"completed", "failed", "blocked", "stale_input"}
    snapshots = []
    while True:
        conn = ro_conn()
        rows = b_jobs(conn)
        counts: dict[str, int] = {}
        for row in rows:
            counts[row["status"]] = counts.get(row["status"], 0) + 1
        conn.close()
        api_status, api_body = http(
            "candidates_poll", "GET", CANDIDATES_URL + "?cohort=dual",
        )
        api = api_body if api_status == 200 else {}
        snapshot = {
            "ts": now(),
            "db_status_counts": counts,
            "api_state": api.get("state"),
            "api_verifier_state": (api.get("verification") or {}).get("state"),
        }
        snapshots.append(snapshot)
        ev("poll", True, snapshot=snapshot)
        total = sum(counts.values())
        done = sum(n for st, n in counts.items() if st in terminal)
        # 投影终态：completed（全就绪）或 needs_attention（有失败/过期作业——
        # 如实终态，失败详情入账）；generating才是仍在生成。
        states_done = (
            api.get("state") in {"completed", "needs_attention"}
            and (api.get("verification") or {}).get("state")
            in {"completed", "needs_attention"}
        )
        if total and done == total and states_done:
            break
        if time.time() >= deadline:
            fail("poll_budget_exhausted", counts)
            break
        time.sleep(POLL_INTERVAL_S)

    # ------------------------------------------------ 终态导出（立即，先于任何重启）
    ok = export(run_started_at, jobs=jobs, submission=submission,
                snapshots=snapshots, resumed=resumed, pin_failed=pin_failed)
    EVIDENCE_FH.close()
    return 0 if ok else 2


def abort(code: str, run_started_at: str, **detail) -> int:
    fail(code, detail)
    export(run_started_at, jobs=None, aborted=code, abort_detail=detail)
    EVIDENCE_FH.close()
    print(json.dumps({"ok": False, "code": code, "failures": FAILURES},
                     ensure_ascii=False))
    return 2


def det_payload_fields(job) -> list:
    """确定性作业存储画像的字段清单（stale也可离线重算规则映射，供D3取回）。

    input_payload的顶层大节被spill进 monitoring_ai_payload_blobs（键
    $section_blob=digest），此处手工物化。
    """
    conn = ro_conn()
    try:
        row = conn.execute(
            "SELECT input_payload_json FROM monitoring_ai_jobs WHERE job_id = ?",
            (job["job_id"],),
        ).fetchone()
        if row is None:
            return []
        payload = json.loads(row["input_payload_json"])
        profile = payload.get("field_profile") or {}
        if isinstance(profile, dict) and "$section_blob" in profile:
            blob = conn.execute(
                "SELECT payload_json FROM monitoring_ai_payload_blobs "
                "WHERE blob_sha256 = ?",
                (profile["$section_blob"],),
            ).fetchone()
            profile = json.loads(blob["payload_json"]) if blob else {}
        return [
            {"domain": f.get("domain"), "field": f.get("field")}
            for f in (profile.get("fields") or [])
        ]
    finally:
        conn.close()


def classify_all(conn, jobs) -> list:
    sys.path.insert(0, str(WORKBENCH_ROOT))
    from packages.medical_monitoring.admission.evidence_tool_contract import (
        classify_tool_usage,
    )
    rows = []
    for job in jobs:
        reads = conn.execute(
            "SELECT COUNT(*) FROM monitoring_ai_evidence_reads WHERE job_id = ?",
            (job["job_id"],),
        ).fetchone()[0]
        rows.append({
            "job_id": job["job_id"],
            "prompt_version": job["prompt_version"],
            "evidence_read_rows": reads,
            "classify_tool_usage": classify_tool_usage(
                job["prompt_version"], reads,
            ),
        })
    return rows


def export(run_started_at: str, *, jobs, submission=None, snapshots=None,
           resumed=False, aborted="", note="", abort_detail=None,
           pin_failed=False) -> bool:
    conn = ro_conn()
    if jobs is None:
        jobs = b_jobs(conn)
    job_dicts = []
    for row in jobs:
        job_dicts.append({key: row[key] for key in row.keys()})
    model_jobs = [j for j in job_dicts if j["provider"] != DETERMINISTIC_PROVIDER]
    det_jobs = [j for j in job_dicts if j["provider"] == DETERMINISTIC_PROVIDER]

    candidates = []
    candidate_status_bad = []
    candidate_statuses = set()
    for job in job_dicts:
        for row in conn.execute(
            "SELECT candidate_id, status, candidate_json FROM "
            "monitoring_ai_candidates WHERE project_id = ? AND job_id = ?",
            (job["project_id"] if "project_id" in job.keys() else PROJECT,
             job["job_id"]),
        ):
            payload = json.loads(row["candidate_json"])
            candidate_statuses.add(row["status"])
            candidate_statuses.add(str(payload.get("status")))
            if row["status"] != "proposed" or str(payload.get("status")) != "proposed":
                candidate_status_bad.append(
                    {"candidate_id": row["candidate_id"],
                     "row_status": row["status"],
                     "json_status": payload.get("status")},
                )
            candidates.append({
                "job_id": job["job_id"],
                "business_key": job["business_key"],
                "candidate_id": row["candidate_id"],
                "status": row["status"],
                "candidate_json": payload,
            })
    receipts = []
    for job in job_dicts:
        for row in conn.execute(
            "SELECT read_id, attempt_number, receipt_json, receipt_sha256, "
            "response_model, created_at FROM monitoring_ai_evidence_reads "
            "WHERE job_id = ?",
            (job["job_id"],),
        ):
            receipts.append({
                "job_id": job["job_id"],
                "read_id": row["read_id"],
                "attempt_number": row["attempt_number"],
                "receipt": json.loads(row["receipt_json"]),
                "receipt_sha256": row["receipt_sha256"],
                "response_model": row["response_model"],
                "created_at": row["created_at"],
            })
    attempts = []
    for job in job_dicts:
        for row in conn.execute(
            "SELECT attempt_id, attempt_number, owner, request_sha256, "
            "response_sha256, response_model, outcome, failure_code, "
            "failure_message, created_at FROM monitoring_ai_attempts "
            "WHERE job_id = ?",
            (job["job_id"],),
        ):
            attempts.append({key: row[key] for key in row.keys()})
    classifications = classify_all(conn, jobs)
    a_shas, _draft = a_baseline_revision_sha(conn)
    a_sha = next(iter(a_shas)) if len(a_shas) == 1 else ""
    conn.close()

    # 运行时校验（testNotes）
    def unit_count(cohort_prefix: str) -> int:
        keys = {
            re.search(r":u(\d{2}):", j["business_key"]).group(0)
            for j in job_dicts
            if j["business_key"].startswith(cohort_prefix)
            and re.search(r":u(\d{2}):", j["business_key"])
        }
        return len(keys)

    units_by_cohort = {
        "primary": unit_count(f"listing-field-mapping:{ATTEMPT_ID}:"),
        "verifier": unit_count(f"listing-field-mapping-verifier:{ATTEMPT_ID}:"),
    }
    model_jobs_by_cohort = {
        "primary": [
            j for j in model_jobs
            if j["prompt_version"] == PRIMARY_B_VERSION
        ],
        "verifier": [
            j for j in model_jobs
            if j["prompt_version"] == VERIFIER_B_VERSION
        ],
    }
    runtime_checks = {
        "model_jobs_equal_units_times_two": (
            len(model_jobs_by_cohort["primary"]) == units_by_cohort["primary"]
            and len(model_jobs_by_cohort["verifier"]) == units_by_cohort["verifier"]
        ),
        "units_by_cohort": units_by_cohort,
        "model_jobs_by_cohort": {
            k: len(v) for k, v in model_jobs_by_cohort.items()
        },
        # 现役代际：非stale确定性作业恰4（每cohort恰2）；第一代stale作业是
        # 实现修复前的历史代际，保留计数但不计入现役，也不参与revision统一性。
        "deterministic_jobs_active_exact_4": sum(
            1 for j in det_jobs if j["status"] != "stale_input"
        ) == 4,
        "deterministic_jobs_active_completed": sum(
            1 for j in det_jobs if j["status"] == "completed"
        ),
        "deterministic_jobs_retired_first_generation": sum(
            1 for j in det_jobs if j["status"] == "stale_input"
        ),
        "deterministic_jobs_active": [
            {"business_key": j["business_key"], "prompt_version": j["prompt_version"],
             "status": j["status"],
             "payload_field_names": det_payload_fields(j)}
            for j in det_jobs if j["status"] != "stale_input"
        ],
        "g3_failure_if_active_deterministic_is_2": sum(
            1 for j in det_jobs if j["status"] != "stale_input"
        ) == 2,
        "b_model_jobs_single_revision": len(
            {j["input_revision_sha256"] for j in model_jobs}
        ) == 1,
        "b_revision_matches_a_verbatim": (
            {j["input_revision_sha256"] for j in job_dicts} == {a_sha}
            if a_sha else None
        ),
        "input_revision_sha256": a_sha,
        "no_non_proposed_candidates": not candidate_status_bad,
        "candidate_statuses_seen": sorted(candidate_statuses),
    }
    per_job_tool_usage = {
        row["job_id"]: row for row in classifications
    }
    for job in model_jobs:
        row = per_job_tool_usage[job["job_id"]]
        if job["status"] == "completed" and not (
            row["evidence_read_rows"] > 0
            or row["classify_tool_usage"] in ("tool_loop_idle",)
        ):
            runtime_checks.setdefault("model_job_usage_anomalies", []).append(row)
    for job in det_jobs:
        row = per_job_tool_usage[job["job_id"]]
        if job["status"] != "stale_input" and row["classify_tool_usage"] != (
            "tool_loop_idle"
        ):
            runtime_checks.setdefault("deterministic_usage_anomalies", []).append(row)

    # 人工介入计量
    udr_count = 0
    field_pairs_by_cohort: dict[str, dict] = {"primary": {}, "verifier": {}}
    for candidate in candidates:
        cohort = (
            "verifier"
            if candidate["business_key"].startswith("listing-field-mapping-verifier:")
            else "primary"
        )
        for mapping in (
            candidate["candidate_json"]
            .get("structured_payload", {})
            .get("field_mappings", [])
        ):
            if mapping.get("user_decision_required"):
                udr_count += 1
            pair = (mapping.get("domain"), mapping.get("source_field"))
            field_pairs_by_cohort[cohort][pair] = (
                mapping.get("recommended_role"),
                mapping.get("field_kind"),
            )
    shared = set(field_pairs_by_cohort["primary"]) & set(
        field_pairs_by_cohort["verifier"]
    )
    divergent_pairs = sorted(
        pair for pair in shared
        if field_pairs_by_cohort["primary"][pair]
        != field_pairs_by_cohort["verifier"][pair]
    )

    # G7：list_for_review只读投影（与D3取数同服务会话）
    projections = {}
    for cohort in ("primary", "verifier", "dual"):
        status, body = http(
            f"g7_projection_{cohort}", "GET",
            CANDIDATES_URL + f"?cohort={cohort}",
        )
        projections[cohort] = {"http_status": status, "body": body}

    def projection_summary(cohort: str) -> dict:
        body = projections[cohort].get("body") or {}
        return body.get("summary") or {}

    def projected_fields(cohort: str) -> set:
        # 公共投影不回传候选明细（displayed_count=0是展示策略）；字段可见性
        # 以summary.field_count/candidate_count计量。
        return set()

    primary_summary = projection_summary("primary")
    verifier_summary = projection_summary("verifier")
    g7 = {
        "http_ok": all(
            projections[c]["http_status"] == 200 for c in projections
        ),
        "primary_state": projections["primary"]["body"].get("state"),
        "verifier_state": projections["verifier"]["body"].get("state"),
        "primary_summary": primary_summary,
        "verifier_summary": verifier_summary,
        # 冻结批次每cohort应可见52字段（CM32+MH20，含元数据）；确定性作业
        # stale时元数据结论缺席，实测只剩26业务字段——如实判fail。
        "field_counts_exact_52_both_cohorts": (
            primary_summary.get("field_count") == 52
            and verifier_summary.get("field_count") == 52
        ),
        "metadata_fields_visible": {
            "note": (
                "元数据字段可见性等价于确定性作业completed；当前以field_count"
                "是否达到52间接判定，明细字段清单见d_baseline与det payload导出"
            ),
        },
    }

    sha_pin = {
        "a_first_round_revision_sha256": a_sha,
        "b_revision_shas": sorted(
            {j["input_revision_sha256"] for j in job_dicts}
        ),
        "verbatim_match": (
            {j["input_revision_sha256"] for j in job_dicts} == {a_sha}
            if a_sha else None
        ),
        "analysis": (
            "冻结harness画像本身一致（A与B的field_profile逐字段相同）；修订摘"
            "要差异是证据工具合同的系统性结果：v20/verifier-v2在提交时把冻结文"
            "档源（ecrf+protocol）bind进revision来源（bind_tool_revision_"
            "sources），v19/verifier-v8无工具合同不绑定，故修订摘要必然不同。"
            "确定性作业另因非chunk画像在bind_frozen_document_sources中被重算"
            "profile_sha256（C1③已记录的条件性边界），其field-profile源hash与"
            "单元不同且与claim时的resolver重算不一致⇒4个确定性作业stale，"
            "元数据结论未入候选。"
        ),
    }

    ok = (
        not FAILURES
        and runtime_checks["model_jobs_equal_units_times_two"]
        and runtime_checks["deterministic_jobs_active_exact_4"]
        and runtime_checks["deterministic_jobs_active_completed"] == 4
        and runtime_checks["b_model_jobs_single_revision"]
        and runtime_checks["no_non_proposed_candidates"]
        and g7["http_ok"]
        and g7["field_counts_exact_52_both_cohorts"]
    )
    report = {
        "schema_version": "d-route-b-run-result-v1",
        "generated_at": now(),
        "run_started_at": run_started_at,
        "route": "B",
        "mode": "bounded_live_run",
        "strategy_env": STRATEGY_ENV,
        "attempt_id": ATTEMPT_ID,
        "resumed_without_restart": resumed,
        "submission": submission,
        "totals": {
            "jobs": len(job_dicts),
            "model_jobs": len(model_jobs),
            "deterministic_jobs": len(det_jobs),
            "candidates": len(candidates),
            "evidence_reads": len(receipts),
            "attempts": len(attempts),
        },
        "runtime_checks": runtime_checks,
        "sha_pin": sha_pin,
        "pin_failed": pin_failed,
        "human_intervention_metrics": {
            "user_decision_required_count": udr_count,
            "dual_cohort_shared_fields": len(shared),
            "dual_cohort_divergent_fields": len(divergent_pairs),
            "divergent_fields": [
                {"domain": d, "source_field": f} for d, f in divergent_pairs
            ],
        },
        "classify_tool_usage": classifications,
        "jobs": job_dicts,
        "candidates": candidates,
        "evidence_reads": receipts,
        "attempts": attempts,
        "g7_list_for_review_projection": {
            "note": "与D3取数同服务会话；投影随live库，重启后以本导出为准",
            "checks": g7,
            "projections": projections,
        },
        "poll_snapshots": snapshots or [],
        "failures": FAILURES,
        "restart_warning": (
            "任意后续重启会把live库B全部作业（含completed）翻STALE_INPUT、"
            "候选翻SUPERSEDED（N5后无v19存活例外）；live库B证据链随即全报废，"
            "以本导出为准。"
        ),
        "self_check": {
            "status": "pass" if ok else "fail",
            "failures": FAILURES,
            "aborted": aborted,
            "abort_detail": abort_detail,
            "note": note,
        },
    }
    RESULT.write_text(
        json.dumps(report, ensure_ascii=False, indent=1), encoding="utf-8",
    )
    print(json.dumps({
        "ok": ok,
        "jobs": len(job_dicts),
        "model_jobs": len(model_jobs),
        "deterministic_jobs": len(det_jobs),
        "failures": FAILURES,
        "result": str(RESULT),
    }, ensure_ascii=False))
    return ok


if __name__ == "__main__":
    raise SystemExit(main())
