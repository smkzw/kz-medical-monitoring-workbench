"""SAR重跑·阶段2(mapping_start)：文档权威核对 + 启动映射候选双队列。

链路（r7产品面 medical_monitoring_r7_product_router.py:963 注册的
mapping_candidate_routes；旧版 /ai/field-mapping-jobs 已停用
main.py:4237 allow_legacy_field_mapping=False → 410）：

PhaseA 文档权威核对（映射lane前置门，缺它=422 mapping_document_evidence_incomplete，
2026-09-26 09:18实测）：
  A1 POST r7/data-admissions/{attempt}/study-documents/analyze
     （multipart：研究方案docx + eCRF pdf）→ 202 {state, analysis_token}
     ⚠付费：document_authority双VLM分析（主glm-5.3-flash高思考+
     盲核deepseek-v4.1-flash高思考，ai_role_bindings.json实测在位）
  A2 轮询 GET study-documents 直到 ready=true（自动晋级）或 needs_user_input
     （歧义需医学经理裁决——本脚本不代为裁决，如实上报）
PhaseB 双队列映射候选（mapping_pipeline.py:1107 generate_dual_candidates）：
  冻结一次harness输入→双cohort预检（allow_local_fallback=False，
  不可用fail-closed）→各自提交分块作业→worker唤醒。
  幂等：作业按business_key+input_revision入库，重复调用返回既有作业，
  失败分片_recover_failed_submission_jobs有界恢复。

分批策略（服务端固定）：chunk_size默认12、上限50（mapping_pipeline.py:91-92），
按域分块Σceil(域字段/12)。本listing 1495字段62域→151 AI作业/cohort
（与2026-09实际完全一致），另~4个确定性元数据作业。双队列≈302 AI作业。
worker并发：primary默认4、verifier默认1（main.py:1398-1417）。

付费台账：PhaseA/PhaseB启动即在run_ledger.jsonl记录时间与规模。
退出码：0=已启动且队列在消耗；10=已提交仍在运行（可再轮询，含PhaseA分析中）；
2=前置/提交失败（evidence含原因）。
"""

from __future__ import annotations

import json
import sys
import time
import urllib.error
import uuid
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

WORKBENCH_ROOT = Path(__file__).resolve().parents[2]
PROJECT = "proj_mgk10_sar_real"
ATTEMPT_ID = "stg-e9d5050c73ef44be818e1f44920fdb5f"  # 09-05 attempt，live实测仍profile_ready

# 研究文档（与2026-09链同源同字节）
PROTOCOL_DOCX = Path(
    "/Users/smkzw/Documents/康哲项目资料/AI/医学经理工作台/qoderwork"
    "/datalisting&protocol/MG-K10-SAR-001_临床研究方案_ V2.1_20250919_clean版 .docx"
)
ECRF_PDF = (
    WORKBENCH_ROOT
    / "runs/phase_c_mgk10_authority_v2_20260905/runtime/source_artifacts"
    / PROJECT
    / "medical_monitoring/ecrf"
    / "bc93ca20212a3c93a363520fa52565d4cc02b299c5981ba8f5240343e3d03229.pdf"
)

HERE = Path(__file__).resolve().parent
EVIDENCE = HERE / "stage2_evidence.jsonl"
STATE = HERE / "stage2_state.json"
LEDGER = HERE / "run_ledger.jsonl"

BASE = (
    f"http://127.0.0.1:8910/api/projects/{PROJECT}"
    f"/modules/medical-monitoring/r7"
)
ADMISSION_URL = f"{BASE}/data-admissions/{ATTEMPT_ID}"
DOCS_URL = f"{ADMISSION_URL}/study-documents"
CANDIDATES_URL = f"{ADMISSION_URL}/mapping-candidates"

DOCS_POLL_BUDGET_S = 2400.0     # PhaseA单次调用预算40min；未完exit 10可再轮询
DOCS_POLL_INTERVAL_S = 30.0
OBSERVE_WINDOW_S = 150.0        # PhaseB提交后观测窗口
OBSERVE_INTERVAL_S = 30.0
SUBMIT_TIMEOUT_S = 900

PRIMARY_PARALLELISM = 4         # main.py:1398 默认4
VERIFIER_PARALLELISM = 1        # main.py:1412 默认1
PER_JOB_BUDGET_S = 900          # w04契约：attempt级单调用上限900s，max_attempts=2

_evidence_fh = EVIDENCE.open("a", encoding="utf-8")
FAILURES: list[str] = []


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _ev(step: str, ok: bool, **detail: object) -> None:
    _evidence_fh.write(
        json.dumps(
            {"ts": _now(), "stage": "mapping_start", "step": step, "ok": bool(ok), **detail},
            ensure_ascii=False,
        )
        + "\n"
    )
    _evidence_fh.flush()


def _assert(step: str, label: str, ok: bool, detail: object) -> None:
    _ev(step, ok, assertion=label, detail=detail)
    if not ok:
        FAILURES.append(f"{step}:{label}={detail!r}")


def _http(step: str, method: str, url: str, *, payload=None, timeout=120,
          multipart=None):
    request = urllib.request.Request(url, method=method)
    if multipart is not None:
        boundary, fields = multipart
        body = b""
        for name, filename, content in fields:
            body += (
                f"--{boundary}\r\n"
                f'Content-Disposition: form-data; name="{name}"; filename="{filename}"\r\n'
                f"Content-Type: application/octet-stream\r\n\r\n"
            ).encode() + content + b"\r\n"
        body += f"--{boundary}--\r\n".encode()
        request.add_header("Content-Type", f"multipart/form-data; boundary={boundary}")
    elif payload is not None:
        body = json.dumps(payload, ensure_ascii=False).encode()
        request.add_header("Content-Type", "application/json")
    else:
        body = None
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
        _ev(step, False, kind="http", url=url, error=str(exc)[:300])
        FAILURES.append(f"{step}:http_error={exc}")
        return 0, {}
    elapsed_ms = int((time.monotonic() - started) * 1000)
    try:
        parsed = json.loads(raw.decode())
    except Exception:
        parsed = {"_raw": raw.decode("utf-8", errors="replace")[:2000]}
    _ev(
        step, True, kind="http", request={"method": method, "url": url},
        http_status=status, elapsed_ms=elapsed_ms,
        response=json.dumps(parsed, ensure_ascii=False)[:3000],
    )
    return status, parsed


def _docs_state() -> dict:
    status, body = _http("documents_readiness", "GET", DOCS_URL)
    return body if status == 200 else {}


def _ledger(entry: dict) -> None:
    with LEDGER.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(entry, ensure_ascii=False) + "\n")


def phase_a_document_authority() -> dict:
    """文档权威核对：ready即复用；有持久化token则续resolve；否则analyze。"""
    docs = _docs_state()
    if docs.get("ready"):
        _ev("phase_a", True, note="ready=true，复用现有文档权威绑定", roles=docs.get("roles"))
        return {"state": "ready", "reused": True}
    required = [
        (r.get("role"), r.get("status"))
        for r in docs.get("roles") or []
        if r.get("required_now")
    ]
    _ev("phase_a_precheck", True, ready=False, required_roles=required)

    # 幂等续跑：已有分析token（batch已提交）则不重复付费提交
    prior_token = ""
    if STATE.is_file():
        try:
            prior_token = str(json.loads(STATE.read_text(encoding="utf-8")).get("analysis_token") or "")
        except Exception:
            prior_token = ""
    if prior_token:
        token = prior_token
        _ev("phase_a_resume", True, note="复用已提交分析批次，不重复analyze",
            analysis_token=token)
        fresh_submit = False
    else:
        fresh_submit = True
        protocol_bytes = PROTOCOL_DOCX.read_bytes()
        ecrf_bytes = ECRF_PDF.read_bytes()
        boundary = "----sarRerun" + uuid.uuid4().hex
        status, body = _http(
            "documents_analyze_start",
            "POST",
            DOCS_URL + "/analyze",
            multipart=(
                boundary,
                [
                    ("files", PROTOCOL_DOCX.name, protocol_bytes),
                    ("files", "MG-K10-SAR-001_eCRF_V1.1_20251029.pdf", ecrf_bytes),
                ],
            ),
            timeout=SUBMIT_TIMEOUT_S,
        )
        _assert("documents_analyze_start", "http_ok", status in (200, 202), status)
        token = str(body.get("analysis_token") or "")
        if status not in (200, 202):
            _ev("stage_failed", False, failures=FAILURES, code=body.get("code"))
            print(json.dumps({"ok": False, "phase": "A", "code": body.get("code"),
                              "failures": FAILURES}, ensure_ascii=False))
            return {"state": "failed"}
        # token立即持久化（重启/超时续跑不重复提交）
        STATE.write_text(json.dumps(
            {"attempt_id": ATTEMPT_ID, "phase": "A_document_authority",
             "analysis_token": token, "updated_at": _now()},
            ensure_ascii=False, indent=1), encoding="utf-8")
    if fresh_submit:
        _ledger({
            "ts_utc": _now(),
            "stage": "mapping_start.phaseA_document_authority",
            "project": PROJECT,
            "attempt_id": ATTEMPT_ID,
            "paid": True,
            "scale": {
                "files": 2,
                "protocol_bytes": len(protocol_bytes),
                "ecrf_bytes": len(ecrf_bytes),
                "cohorts": ["document_authority_primary_ai(glm-5.3-flash,high)",
                            "document_authority_verifier_ai(deepseek-v4.1-flash,high)"],
            },
            "analysis_token": token,
            "note": "文档权威双VLM分析启动（常设授权条款登记：时间+规模）",
        })

    deadline = time.time() + DOCS_POLL_BUDGET_S
    last = docs
    while time.time() < deadline:
        time.sleep(DOCS_POLL_INTERVAL_S)
        # 推进/轮询统一走resolve（main.py:4107 _promote_r7_monitoring_...
        # ——UI"重新核对"手势；空selections=不做人工裁决，让双队列
        # reconciliation说话）。promoted后readiness才翻ready。
        rstatus, rbody = _http(
            "documents_resolve",
            "POST",
            DOCS_URL + "/resolve",
            payload={
                "batch_id": token,
                "user_role_selections": [],
            },
            timeout=SUBMIT_TIMEOUT_S,
        )
        rstate = str(rbody.get("state") or "")
        if rstate == "promoted":
            last = _docs_state()
            _ev("phase_a_poll", True, note="promoted", resolve_state=rstate,
                ready=last.get("ready"), roles=last.get("roles"))
            if last.get("ready"):
                return {"state": "ready", "analysis_token": token, "reused": False}
            # 已promoted但readiness未翻：下一轮readiness复查
            continue
        if rstate in ("needs_user_input", "failed", "project_mismatch",
                      "project_identity_incomplete"):
            _ev("phase_a_blocked", False, resolve_state=rstate, resolve=rbody)
            print(json.dumps({"ok": False, "phase": "A", "state": rstate,
                              "detail": rbody}, ensure_ascii=False))
            return {"state": "failed"}
        last = _docs_state()
        _ev("phase_a_poll", True, still_running=True, resolve_state=rstate or rstatus,
            ready=last.get("ready"))
        if last.get("ready"):
            return {"state": "ready", "analysis_token": token, "reused": False}
    _ev("phase_a_timeout", True, note="分析仍在进行，预算内未完成", last=last)
    return {"state": "running", "analysis_token": token, "last": last}


def phase_b_dual_candidates() -> dict:
    """启动双队列映射候选并观测。返回{'state':...}；可能为started/running/failed。"""
    status, body = _http(
        "dual_candidates_start", "POST", CANDIDATES_URL, payload={}, timeout=SUBMIT_TIMEOUT_S
    )
    code = body.get("code") if isinstance(body.get("code"), str) else None
    _assert("dual_candidates_start", "http_ok", status in (200, 201), status)
    if status not in (200, 201):
        _ev("stage_failed", False, failures=FAILURES, code=code)
        print(json.dumps({"ok": False, "phase": "B", "code": code,
                          "failures": FAILURES}, ensure_ascii=False))
        return {"state": "failed", "code": code}
    prim = body.get("summary") or {}
    ver = (body.get("verification") or {}).get("summary") or {}
    progress = {
        "primary_state": body.get("state"),
        "primary_jobs": prim.get("job_count"),
        "primary_completed": prim.get("completed_job_count"),
        "verifier_state": (body.get("verification") or {}).get("state"),
        "verifier_jobs": ver.get("job_count"),
        "verifier_completed": ver.get("completed_job_count"),
    }
    _ev("submitted_scale", True, progress=progress)
    _assert("dual_candidates_start", "both_cohorts_have_jobs",
            bool(progress["primary_jobs"]) and bool(progress["verifier_jobs"]), progress)

    _ledger({
        "ts_utc": _now(),
        "stage": "mapping_start.phaseB_dual_candidates",
        "project": PROJECT,
        "attempt_id": ATTEMPT_ID,
        "paid": True,
        "scale": {
            "primary_ai_jobs": progress["primary_jobs"],
            "verifier_ai_jobs": progress["verifier_jobs"],
            "chunk_size": 12,
            "cohorts": ["medical_monitoring_ai(glm-5.3-flash,high)",
                        "medical_monitoring_verifier_ai(deepseek-v4.1-flash,high)"],
        },
        "note": "双队列映射候选启动（常设授权条款登记：时间+规模）",
    })

    samples = [progress]
    deadline = time.time() + OBSERVE_WINDOW_S
    while time.time() < deadline:
        time.sleep(OBSERVE_INTERVAL_S)
        gs, gb = _http(
            "candidates_poll", "GET",
            CANDIDATES_URL + "?" + urllib.parse.urlencode({"cohort": "dual"}),
        )
        if gs == 200:
            s = gb.get("summary") or {}
            v = (gb.get("verification") or {}).get("summary") or {}
            samples.append({
                "primary_state": gb.get("state"),
                "primary_jobs": s.get("job_count"),
                "primary_completed": s.get("completed_job_count"),
                "verifier_state": (gb.get("verification") or {}).get("state"),
                "verifier_jobs": v.get("job_count"),
                "verifier_completed": v.get("completed_job_count"),
            })
    last = samples[-1]
    _ev("observation_window", True, samples=samples)
    moved = (last.get("primary_completed") or 0) > (progress.get("primary_completed") or 0) or \
            (last.get("verifier_completed") or 0) > (progress.get("verifier_completed") or 0)
    completed = (last.get("primary_state") == "completed")
    if not (moved or completed):
        return {"state": "running", "progress": last, "samples": samples}
    _assert("observation_window", "queues_consuming_or_done", True, last)
    return {"state": "started", "progress": last, "samples": samples}


def main() -> int:
    # 前置：attempt仍为profile_ready
    status, body = _http("admission_precheck", "GET", ADMISSION_URL)
    _assert("admission_precheck", "http_ok", status == 200, status)
    _assert("admission_precheck", "state_profile_ready",
            body.get("state") == "profile_ready", body.get("state"))
    _assert("admission_precheck", "summary_matches_real_listing",
            (body.get("summary") or {}).get("tables") == 62
            and (body.get("summary") or {}).get("rows") == 148788, body.get("summary"))
    if FAILURES:
        _ev("stage_failed", False, failures=FAILURES)
        print(json.dumps({"ok": False, "failures": FAILURES}, ensure_ascii=False))
        return 2

    a = phase_a_document_authority()
    if a["state"] == "failed":
        return 2
    if a["state"] == "running":
        STATE.write_text(json.dumps(
            {"attempt_id": ATTEMPT_ID, "phase": "A_document_authority",
             "analysis_token": a.get("analysis_token"), "updated_at": _now()},
            ensure_ascii=False, indent=1), encoding="utf-8")
        _ev("stage_still_running", True, phase="A")
        _evidence_fh.close()
        print(json.dumps({"ok": True, "exit": 10, "phase": "A_document_authority",
                          "note": "文档权威分析仍在运行，稍后重跑本阶段续轮询"}, ensure_ascii=False))
        return 10

    b = phase_b_dual_candidates()
    if b["state"] == "failed":
        return 2

    progress = b.get("progress") or {}
    pj = int(progress.get("primary_jobs") or 0)
    vj = int(progress.get("verifier_jobs") or 0)
    eta = {
        "job_count": {"primary": pj, "verifier": vj},
        "assumptions": {
            "worker_parallelism": {"primary": PRIMARY_PARALLELISM, "verifier": VERIFIER_PARALLELISM},
            "per_job_budget_s": PER_JOB_BUDGET_S,
            "note": "上限法（每作业900s预算）；verifier串行为瓶颈；实际中位数更快",
        },
        "eta_upper_bound_h": {
            "primary": round(pj * PER_JOB_BUDGET_S / PRIMARY_PARALLELISM / 3600, 1),
            "verifier": round(vj * PER_JOB_BUDGET_S / VERIFIER_PARALLELISM / 3600, 1),
        },
    }
    STATE.write_text(json.dumps(
        {"attempt_id": ATTEMPT_ID, "phase": "B_dual_candidates_started",
         "documents_ready": True, "scale": eta["job_count"], "eta": eta,
         "samples": b.get("samples"), "updated_at": _now()},
        ensure_ascii=False, indent=1), encoding="utf-8")
    if b["state"] == "running":
        _ev("stage_still_running", True, phase="B", eta=eta)
        _evidence_fh.close()
        print(json.dumps({"ok": True, "exit": 10, "phase": "B_dual_candidates",
                          "jobs": eta["job_count"], "eta_upper_bound_h": eta["eta_upper_bound_h"]},
                         ensure_ascii=False))
        return 10
    _ev("stage_done", not FAILURES, failures=FAILURES, eta=eta)
    _evidence_fh.close()
    print(json.dumps({"ok": not FAILURES, "jobs": eta["job_count"],
                      "eta_upper_bound_h": eta["eta_upper_bound_h"]}, ensure_ascii=False))
    return 0 if not FAILURES else 2


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if a != "--stage"]
    if args and args != ["mapping_start"]:
        print("usage: sar_mapping_start.py [--stage mapping_start]")
        sys.exit(2)
    sys.exit(main())
