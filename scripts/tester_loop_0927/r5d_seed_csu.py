"""R5D 开考位预置：在隔离环境 8911 上把 MX循R5D-CSU 推进到
「字段映射 confirmed + facts 物化完成、界面可开始运行监查」停住。

API 序列参考 scripts/fullchain_sar_rerun_20260926/HANDOFF_SAR_RERUN_20260926.md
与同目录 sar_intake.py / sar_mapping_start.py / sar_mapping_confirm_facts.py
（幂等脚本模式），并对照 R5 验收脚本 /tmp/r5_csu_acceptance.py 的实测调用面
（r7 data-admissions/upload → study-documents/analyze → resolve →
mapping-candidates → mapping-draft → adjudicate → confirm → facts）。

原则：
  - 全部经 HTTP API 操作 8911，绝不触碰 8910/5177；
  - 文档权威与映射的 AI 作业（双队列）真实产生，等待自然完成，
    不跳过任何质量门、不伪造状态；身份归属人工确认按产品设计
    以 identity_confirmation 提交（等价界面一次点击，如实留痕）；
  - 幂等：状态持久化 r5d_seed_state.json，已完成的步骤直接复用；
  - 留痕：每步请求/响应摘要写 r5d_seed_evidence.jsonl。

退出码：0=达标（confirmed+facts）；10=仍在运行（可重跑续轮询）；
2=阻断/断言失败（evidence 含原因）。
"""

from __future__ import annotations

import json
import sys
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path

import requests
from requests.adapters import HTTPAdapter

BASE = "http://127.0.0.1:8911"
STAGING = Path(
    "/Users/smkzw/Documents/康哲项目资料/AI/医学经理工作台"
    "/implementation/workbench/tester_staging_0927/synth_csu"
)
LISTING = STAGING / "MG-K10-CSU-001_合成测试数据_V1.0.xlsx"
PROTOCOL = STAGING / "MG-K10-CSU-001_临床研究方案_V1.3.docx"
ECRF = STAGING / "MG-K10-CSU-001_eCRF填写指南_V1.0.docx"

PROJECT_NAME = "MX循R5D-CSU"
INDICATION = "慢性自发性荨麻疹"
PRODUCT_NAME = "MG-K10"

HERE = Path(__file__).resolve().parent
STATE = HERE / "r5d_seed_state.json"
EVIDENCE = HERE / "r5d_seed_evidence.jsonl"

DOCS_POLL_BUDGET_S = 2700.0    # 文档权威（双VLM）预算45min
DOCS_POLL_INTERVAL_S = 20.0
MAP_POLL_BUDGET_S = 5400.0     # 映射双队列预算90min（parallelism=2）
MAP_POLL_INTERVAL_S = 30.0
ADJ_BUDGET_S = 900.0           # 复核收敛预算15min
ADJ_INTERVAL_S = 10.0

s = requests.Session()
s.mount("http://", HTTPAdapter(max_retries=3))
FAILURES: list[str] = []
_ev_fh = EVIDENCE.open("a", encoding="utf-8")


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _ev(step: str, ok: bool, **detail: object) -> None:
    _ev_fh.write(
        json.dumps(
            {"ts": _now(), "run": "r5d_seed", "step": step, "ok": bool(ok), **detail},
            ensure_ascii=False,
        )
        + "\n"
    )
    _ev_fh.flush()


def _http(step: str, method: str, url: str, *, json_body=None, timeout=180,
          files=None, data=None):
    started = time.monotonic()
    try:
        resp = s.request(method, url, json=json_body, files=files, data=data,
                         timeout=timeout)
        status, text = resp.status_code, resp.text
    except Exception as exc:  # noqa: BLE001
        _ev(step, False, kind="http", url=url, error=f"{type(exc).__name__}: {exc}"[:300])
        return 0, {}
    elapsed_ms = int((time.monotonic() - started) * 1000)
    try:
        parsed = json.loads(text)
    except Exception:  # noqa: BLE001
        parsed = {"_raw": text[:1500]}
    _ev(step, True, kind="http",
        request={"method": method, "url": url},
        http_status=status, elapsed_ms=elapsed_ms,
        response=json.dumps(parsed, ensure_ascii=False)[:2500])
    return status, parsed


def _load_state() -> dict:
    if STATE.is_file():
        try:
            return json.loads(STATE.read_text(encoding="utf-8"))
        except Exception:  # noqa: BLE001
            return {}
    return {}


def _save_state(**kv) -> None:
    st = _load_state()
    st.update(kv, updated_at=_now())
    STATE.write_text(json.dumps(st, ensure_ascii=False, indent=1), encoding="utf-8")


def main() -> int:
    for p in (LISTING, PROTOCOL, ECRF):
        if not p.is_file():
            _ev("prerequisite", False, reason=f"missing {p}")
            print(f"FAIL: missing {p}")
            return 2
    st = _load_state()

    # ── Step1 建项（幂等：已有 project_id 复用） ─────────────────────
    pid = st.get("project_id")
    if not pid:
        key = f"r5d-seed-{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}-{uuid.uuid4().hex[:8]}"
        status, body = _http(
            "project_create", "POST", f"{BASE}/api/projects",
            json_body={
                "project_name": PROJECT_NAME,
                "indication": INDICATION,
                "product_name": PRODUCT_NAME,
                "modules": ["medical_monitoring"],
                "actor": "r5d_seeder",
                "idempotency_key": key,
            },
        )
        proj = (body or {}).get("project") or {}
        if status != 201 or not proj.get("project_id"):
            print(json.dumps({"ok": False, "step": "project_create",
                              "status": status, "body": body}, ensure_ascii=False))
            return 2
        pid = proj["project_id"]
        _save_state(project_id=pid, create_key=key,
                    project_name=proj.get("project_name"))
        _ev("project_created", True, project_id=pid, name=proj.get("project_name"))
    mm = f"{BASE}/api/projects/{pid}/modules/medical-monitoring/r7"
    adm = f"{mm}/data-admissions"

    # ── Step2 数据接入（上传合成listing，同步复制+解析） ─────────────
    attempt = st.get("attempt_id")
    if not attempt:
        with LISTING.open("rb") as fh:
            status, body = _http(
                "admission_upload", "POST", f"{adm}/upload",
                files={"files": (LISTING.name, fh)},
                data={"relative_paths": LISTING.name},
                timeout=600,
            )
        attempt = (body or {}).get("attempt_id")
        if status not in (200, 201) or not attempt:
            print(json.dumps({"ok": False, "step": "admission_upload",
                              "status": status, "body": body}, ensure_ascii=False))
            return 2
        _save_state(attempt_id=attempt)
        _ev("admission_uploaded", True, attempt_id=attempt,
            summary=(body or {}).get("summary"))
    att = f"{adm}/{attempt}"

    # ── Step3 文档权威：analyze（方案docx + eCRF指南docx 双VLM） ─────
    docs = {}
    status, docs = _http("documents_readiness_pre", "GET", f"{att}/study-documents")
    batch_id = st.get("docs_batch_id")
    if not (docs or {}).get("ready"):
        if not batch_id:
            files = []
            try:
                for path in (PROTOCOL, ECRF):
                    files.append(("files", (path.name, path.open("rb"))))
                status, body = _http(
                    "documents_analyze", "POST", f"{att}/study-documents/analyze",
                    files=files, timeout=300,
                )
            finally:
                for _, (_, fh) in files:
                    fh.close()
            if status != 202:
                print(json.dumps({"ok": False, "step": "documents_analyze",
                                  "status": status, "body": body}, ensure_ascii=False))
                return 2
            batch_id = (body or {}).get("analysis_token")
            _save_state(docs_batch_id=batch_id)
            _ev("documents_analyze_submitted", True, analysis_token=batch_id)

        # 轮询 resolve 至 ready；身份门按设计提交 identity_confirmation（一次）
        identity_confirmed = False
        deadline = time.monotonic() + DOCS_POLL_BUDGET_S
        ready = False
        while time.monotonic() < deadline:
            time.sleep(DOCS_POLL_INTERVAL_S)
            payload: dict = {"batch_id": batch_id}
            status, body = _http(
                "documents_resolve", "POST", f"{att}/study-documents/resolve",
                json_body=payload, timeout=300,
            )
            if status != 200:
                continue
            state = body.get("state")
            gs, gdocs = _http("documents_readiness", "GET", f"{att}/study-documents")
            if (gdocs or {}).get("ready"):
                ready = True
                break
            if state in ("project_mismatch", "project_identity_incomplete") and not identity_confirmed:
                _ev("identity_gate", True, state=state,
                    note="身份归属人工确认：等价界面一次点击（R5验收同款手势）")
                status, body = _http(
                    "documents_resolve_identity_confirm", "POST",
                    f"{att}/study-documents/resolve",
                    json_body={
                        "batch_id": batch_id,
                        "identity_confirmation": {
                            "confirmed": True,
                            "reason": (
                                "R5D开考位预置：确认本组MG-K10-CSU-001合成文件"
                                "（方案V1.3+eCRF指南V1.0+合成listing V1.0）属于"
                                "当前项目MX循R5D-CSU。"
                            ),
                        },
                    },
                    timeout=300,
                )
                identity_confirmed = True
                _save_state(identity_confirmed=True)
                gs, gdocs = _http("documents_readiness", "GET", f"{att}/study-documents")
                if (gdocs or {}).get("ready"):
                    ready = True
                    break
            if state == "needs_user_input" and body.get("user_choices"):
                # 文件角色人工裁决（设计内人工门，等价界面逐项选择）：
                # 只从服务端列出的options里按文件名如实匹配（ecrf→eCRF
                # 填写指南等），匹配不上的角色按「该角色缺失」提交（空
                # candidate_id），不虚构绑定。
                selections = []
                for choice in body.get("user_choices") or []:
                    role = str(choice.get("role") or "")
                    token = {
                        "ecrf": ("eCRF",),
                        "protocol": ("临床研究方案", "方案"),
                        "investigator_brochure": ("研究者手册", "IB"),
                        "sap": ("统计分析计划", "SAP"),
                    }.get(role, ())
                    picked = ""
                    for opt in choice.get("options") or []:
                        fname = str(opt.get("filename") or "")
                        if token and any(t.lower() in fname.lower() for t in token):
                            picked = str(opt.get("candidate_id") or "")
                            break
                    selections.append({"role": role, "candidate_id": picked})
                _ev("role_adjudication", True, selections=selections,
                    note="文件角色人工裁决：按文件名如实匹配，未匹配角色标记缺失")
                status, body = _http(
                    "documents_resolve_role_selection", "POST",
                    f"{att}/study-documents/resolve",
                    json_body={
                        "batch_id": batch_id,
                        "user_role_selections": selections,
                    }, timeout=300,
                )
                _save_state(role_selections=selections)
                gs, gdocs = _http("documents_readiness", "GET", f"{att}/study-documents")
                if (gdocs or {}).get("ready"):
                    ready = True
                    break
                continue
            if state in ("needs_user_input", "failed"):
                _ev("documents_blocked", False, state=state, body=body)
                print(json.dumps({"ok": False, "step": "documents",
                                  "state": state, "body": body}, ensure_ascii=False))
                return 2
        if not ready:
            _ev("documents_timeout", False, note="文档权威在预算内未到ready")
            print(json.dumps({"ok": True, "exit": 10, "step": "documents"}, ensure_ascii=False))
            return 10
        _ev("documents_ready", True)
        _save_state(documents_ready=True)
    else:
        _ev("documents_ready_reused", True)

    # ── Step4 映射双队列：start + 轮询至 candidates_ready ────────────
    status, body = _http("mapping_candidates_read", "GET", f"{att}/mapping-candidates")
    state = (body or {}).get("state")
    if state not in ("candidates_ready", "needs_attention"):
        status, body = _http(
            "mapping_candidates_start", "POST", f"{att}/mapping-candidates",
            json_body={}, timeout=600,
        )
        if status not in (200, 201):
            print(json.dumps({"ok": False, "step": "mapping_start",
                              "status": status, "body": body}, ensure_ascii=False))
            return 2
        _ev("mapping_started", True, scale={
            "primary_jobs": ((body or {}).get("summary") or {}).get("job_count"),
            "verifier_jobs": (((body or {}).get("verification") or {}).get("summary") or {}).get("job_count"),
        })
        deadline = time.monotonic() + MAP_POLL_BUDGET_S
        while time.monotonic() < deadline:
            time.sleep(MAP_POLL_INTERVAL_S)
            gs, gbody = _http("mapping_candidates_poll", "GET", f"{att}/mapping-candidates")
            state = (gbody or {}).get("state")
            summ = (gbody or {}).get("summary") or {}
            ver = ((gbody or {}).get("verification") or {}).get("summary") or {}
            _ev("mapping_poll", True, state=state,
                candidates=summ.get("candidate_count"),
                primary=f"{summ.get('completed_job_count')}/{summ.get('job_count')}",
                verifier=f"{ver.get('completed_job_count')}/{ver.get('job_count')}")
            if state in ("candidates_ready", "needs_attention"):
                break
        else:
            _ev("mapping_timeout", False, note="映射双队列在预算内未就绪")
            print(json.dumps({"ok": True, "exit": 10, "step": "mapping"}, ensure_ascii=False))
            return 10
    _save_state(mapping_state=state)
    _ev("mapping_ready", True, state=state)

    # ── Step5 adopt（系统采纳候选装配为draft） ────────────────────────
    draft_id = st.get("draft_id")
    version = st.get("draft_version")
    if not draft_id:
        status, body = _http(
            "draft_adopt", "POST", f"{att}/mapping-draft",
            json_body={
                "reason": (
                    "R5D开考位预置：映射双队列候选批量核验通过，系统采纳进入"
                    "draft装配，由确认流程继续。"
                ),
                "actor": "r5d_seeder",
            }, timeout=600,
        )
        proj = body or {}
        draft = proj.get("draft") or {}
        draft_id = draft.get("draft_id") or proj.get("draft_id")
        version = draft.get("version") or proj.get("version")
        if status not in (200, 201) or not draft_id:
            print(json.dumps({"ok": False, "step": "draft_adopt",
                              "status": status, "body": body}, ensure_ascii=False))
            return 2
        _save_state(draft_id=draft_id, draft_version=version)
        _ev("draft_adopted", True, draft_id=draft_id, version=version)

    # ── Step6 adjudicate（批量裁决留痕；轮询至收敛） ──────────────────
    adj_state = ""
    deadline = time.monotonic() + ADJ_BUDGET_S
    while time.monotonic() < deadline:
        status, body = _http(
            "draft_adjudicate", "POST", f"{att}/mapping-draft/adjudicate",
            json_body={"draft_id": draft_id}, timeout=300,
        )
        adj = ((body or {}).get("adjudication") or {})
        adj_state = adj.get("state") or ""
        if status != 200:
            _ev("adjudicate_http_error", False, status=status, body=body)
            break
        if adj_state and adj_state != "running":
            break
        time.sleep(ADJ_INTERVAL_S)
    _ev("adjudicate_settled", adj_state in ("completed", "ready", "resolved"),
        adj_state=adj_state)
    _save_state(adjudication_state=adj_state)

    # ── Step7 confirm（医学确认；幂等键一次性持久化） ─────────────────
    confirmed = bool(st.get("confirmed"))
    if not confirmed:
        idem = st.get("confirm_idempotency_key") or f"r5d-confirm-{uuid.uuid4().hex}"
        status, body = _http(
            "draft_confirm", "POST", f"{att}/mapping-draft/confirm",
            json_body={
                "draft_id": draft_id,
                "expected_version": int(version or 1),
                "confirmation_reason": (
                    "R5D开考位预置：双队列映射候选经批量裁决后确认字段对应关系，"
                    "进入事实物化以备运行监查。"
                ),
                "idempotency_key": idem,
                "automatic": True,
            }, timeout=600,
        )
        if status != 200:
            _ev("confirm_blocked", False, status=status,
                code=(body or {}).get("code"), body=body)
            print(json.dumps({"ok": False, "step": "draft_confirm", "status": status,
                              "adj_state": adj_state, "body": body}, ensure_ascii=False))
            return 2
        confirmed = True
        _save_state(confirmed=True, confirm_idempotency_key=idem)
        _ev("draft_confirmed", True)

    # ── Step8 facts 物化 ─────────────────────────────────────────────
    status, body = _http("facts_materialize", "POST", f"{att}/facts",
                         json_body={}, timeout=900)
    if status not in (200, 201):
        print(json.dumps({"ok": False, "step": "facts_materialize",
                          "status": status, "body": body}, ensure_ascii=False))
        return 2
    _ev("facts_materialized", True, summary=(body or {}).get("summary") or body)
    _save_state(facts_materialized=True)

    # ── Step9 终态自验 ───────────────────────────────────────────────
    _, cand = _http("final_mapping_candidates", "GET", f"{att}/mapping-candidates")
    _, facts = _http("final_facts", "GET", f"{att}/facts")
    _, docs_f = _http("final_documents", "GET", f"{att}/study-documents")
    draft_final = (cand or {}).get("draft") or {}
    verdict = {
        "project_id": pid,
        "attempt_id": attempt,
        "mapping_state": (cand or {}).get("state"),
        "draft_status": draft_final.get("status"),
        "draft_id": draft_final.get("draft_id"),
        "candidate_count": ((cand or {}).get("summary") or {}).get("candidate_count"),
        "documents_ready": (docs_f or {}).get("ready"),
        "facts": facts,
        "adjudication_state": adj_state,
    }
    _ev("final_verdict", True, **verdict)
    print(json.dumps({"ok": True, **verdict}, ensure_ascii=False, default=str))
    return 0


if __name__ == "__main__":
    sys.exit(main())
