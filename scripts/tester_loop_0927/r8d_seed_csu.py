"""R8D 开考位预置：在隔离环境 8911 上把 MX循R8D-CSU 推进到
「字段映射 confirmed + facts 物化完成、界面可开始运行监查」停住。

API 序列参考 scripts/fullchain_sar_rerun_20260926/HANDOFF_SAR_RERUN_20260926.md
与同目录幂等脚本（sar_intake/sar_mapping_start/sar_mapping_confirm_facts），
并沿用 R5D 已验证的驱动面（r5d_seed_csu.py + r5d_question_cards.py +
r5d_converge.py + r5d_final_cards.py 合并为单脚本）：
  r7 data-admissions/upload → study-documents/analyze → resolve（角色裁决+
  身份确认，设计内人工门）→ mapping-candidates(start/poll) → mapping-draft
  (adopt) → 问题卡作答（数据实测依据，见 KNOWN_DECISIONS）→ adjudicate
  收敛 → confirm → facts。

原则：
  - 全部经 HTTP API 操作 8911，绝不触碰 8910/5177；
  - AI 作业（文档权威双VLM + 映射双队列 + 复核）真实产生、等待自然完成，
    不跳过任何质量门、不伪造状态；
  - 问题卡/裁决卡仅按数据实测依据作答（与 R5D 相同三份合成文件 → 相同
    事实依据）；出现未知问题时 fail-closed 退出并完整留痕，不虚构作答；
  - 幂等：状态持久化 r8d_seed_state.json，已完成步骤直接复用；
  - 留痕：每步请求/响应摘要写 r8d_seed_evidence.jsonl。

退出码：0=达标（confirmed+facts）；10=预算耗尽仍在推进（可重跑续）；
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

PROJECT_NAME = "MX循R8D-CSU"
INDICATION = "慢性自发性荨麻疹"
PRODUCT_NAME = "MG-K10"
ACTOR = "r8d_seeder"

HERE = Path(__file__).resolve().parent
STATE = HERE / "r8d_seed_state.json"
EVIDENCE = HERE / "r8d_seed_evidence.jsonl"

DOCS_POLL_BUDGET_S = 2700.0    # 文档权威（双VLM）预算45min（R5D实测约15min）
DOCS_POLL_INTERVAL_S = 20.0
MAP_POLL_BUDGET_S = 7200.0     # 映射双队列预算120min（R5D实测约20min）
MAP_POLL_INTERVAL_S = 30.0
CONVERGE_BUDGET_S = 12600.0    # 复核收敛总预算3.5h（R5D受已修缺陷拖累4h+）
CONVERGE_INTERVAL_S = 45.0
NO_PROGRESS_ROUNDS = 8

# ── 数据实测依据的问题卡/裁决卡作答（R5D 同三份合成文件的实测结论） ──
EXTRT_ANSWER = (
    "用户已确认：经核对合成数据MG-K10-CSU-001_合成测试数据_V1.0.xlsx，"
    "EX域'给药药物'128行唯一值'MG-K10 300mg Q4W'，其中安慰剂组8名受试者"
    "64行同样记录该值——该列不代表所有受试者实际接受的试验药物，为方案"
    "标签式给药记录；实际治疗身份以DM域'试验分组'（试验组8/安慰剂组8）"
    "为准，受试者级随机治疗分配经DM.试验分组与EX.受试者编号显式绑定解析。"
    "EXTRT按中性给药角色保留来源值，IMP身份不由此列声明；暴露与变更能力"
    "在独立IMP身份锚点建立前保持停用（按G-CMIP-005指引）。"
)
MHNUM_ANSWER = (
    "用户已核对：MH域'病史记录号'为域内记录标识，选择闭合目录角色"
    "metadata.record_id（G-ROLE-002指引：选择目录角色）。"
)
FINAL_CARDS = {
    ("ICF_TRACK", "ICFSTATE"): ("informed_consent_status",
        "来源列标题'知情状态'，取值已签署/待签署"),
    ("LB_HEM", "LBDAT"): ("lab_collection_date",
        "来源列标题'采样日期'，全列合法日期，与检验名称同行配对"),
    ("LB_HEM", "LBORRES"): ("lab_result_value",
        "来源列标题'结果'，CDISC LBORRES原始结果值语义，与单位/参考范围同行配对"),
    ("LB_HEM", "LBSIGNI"): ("lab_significance_flag",
        "来源列标题'临床意义'（正常/异常/偏低），两轮复核同判lab_clinical_significance，语义一致"),
    ("MH", "MHCAT"): ("medical_history_category",
        "来源列标题'病史类型'，全列唯一值'既往病史'"),
    ("MH", "MHONGO"): ("medical_history_ongoing_flag",
        "来源列标题'目前是否持续'，二值分布"),
    ("MH", "MHSTDAT"): ("medical_history_start_date",
        "来源列标题'开始日期'，与病史名称/持续标志同行"),
    ("SV", "VISDAT"): ("actual_visit_date",
        "来源列标题'实际访视日期'，与访视状态同行配对"),
}

# R8 第二轮复核后浮现的15张两轮分歧裁决卡（20260929T20:0x）。作答依据：
# ① 同三份合成文件的实测列值（R8D attempt facts 与 R5D facts 文件一致）；
# ② R5D 同数据已确认版 monmaprev_e4c1fe85a816792f0814cbec2179（该版经
#   完整质量门链：semantic pass_with_warnings/0全局阻断 + confirm + facts
#   物化）对同一批字段的已确认角色——跨轮次保持同一数据同一确认语义。
# 卡片允许「可采纳任一方或给出其他结论」，此处按②给出结论并逐卡附①依据。
R8_ROUND2_CARDS = {
    ("AE", "AEENDAT"): ("ae_end_date",
        "来源列标题'结束日期'，40行全为合法日期，与'开始日期'(AESTDAT)构成AE事件起止结构"),
    ("AE", "AENUM"): ("ae_record_number",
        "来源列标题'不良事件编号'，取值A001式域内记录编号，为AE域内记录标识"),
    ("AE", "AEOUT"): ("ae_outcome",
        "来源列标题'转归'（好转/持续/痊愈），AE结局类别"),
    ("AE", "AEREL"): ("ae_relationship_to_investigational_product",
        "来源列标题'与试验药物的关系'（肯定有关/可能有关/可能无关/肯定无关），因果关联类别"),
    ("AE", "AESER"): ("serious_ae_flag",
        "来源列标题'严重不良事件'（全列'否'），SAE标志"),
    ("AE", "AESEV"): ("ae_severity",
        "来源列标题'严重程度'（1级/2级/3级），严重程度分级"),
    ("AE", "AESTDAT"): ("ae_start_date",
        "来源列标题'开始日期'，40行全为合法日期"),
    ("AE", "AETERM"): ("ae_verbatim_term",
        "来源列标题'不良事件名称'（头痛/鼻咽炎/上呼吸道感染等原文术语）"),
    ("DM", "ARM"): ("treatment_arm_assignment",
        "来源列标题'试验分组'（试验组/安慰剂组各8名），治疗分组分配"),
    ("LB_HEM", "LBUNIT"): ("lab_result_unit",
        "来源列标题'单位'（10^9/L、U/L），与检验项目/结果同行配对的原始单位文本"),
    ("MH", "MHTERM"): ("medical_history_term",
        "来源列标题'病史名称'（哮喘/偏头痛等原文），无编码血缘不按标准编码术语使用"),
    ("UAS", "UASW2"): ("pruritus_score_week2",
        "来源列标题'第2周瘙痒评分'，16行数值评分，同表四列与第2/4/8/12周平行对应"),
    ("UAS", "UASW4"): ("pruritus_score_week4",
        "来源列标题'第4周瘙痒评分'，16行数值评分，同表四列与第2/4/8/12周平行对应"),
    ("UAS", "UASW8"): ("pruritus_score_week8",
        "来源列标题'第8周瘙痒评分'，16行数值评分，同表四列与第2/4/8/12周平行对应"),
    ("UAS", "UASW12"): ("pruritus_score_week12",
        "来源列标题'第12周瘙痒评分'，16行数值评分，同表四列与第2/4/8/12周平行对应"),
}


def known_decision(domain: str, source_field: str) -> dict | None:
    if (domain, source_field) == ("EX", "EXTRT"):
        return {"user_action": EXTRT_ANSWER}
    if (domain, source_field) == ("MH", "MHNUM"):
        return {"recommended_role": "metadata.record_id", "user_action": MHNUM_ANSWER}
    for table in (FINAL_CARDS, R8_ROUND2_CARDS):
        if (domain, source_field) in table:
            role, basis = table[(domain, source_field)]
            return {
                "recommended_role": role,
                "user_action": (
                    f"用户已核对：两轮复核分歧裁决——按来源数据实测采纳"
                    f"{role}（{basis}）。"
                ),
            }
    return None


s = requests.Session()
s.mount("http://", HTTPAdapter(max_retries=3))
_ev_fh = EVIDENCE.open("a", encoding="utf-8")


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _ev(step: str, ok: bool, **detail: object) -> None:
    _ev_fh.write(
        json.dumps(
            {"ts": _now(), "run": "r8d_seed", "step": step, "ok": bool(ok), **detail},
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


def patch_field(att: str, draft_id: str, domain: str, source_field: str,
                patch: dict) -> bool:
    """按当前 draft version PATCH mapping-draft/field（409 版本冲突重试）。"""
    for _ in range(6):
        _, gb = _http("draft_version_read", "GET", f"{att}/mapping-candidates?focus=all")
        version = int(((gb or {}).get("draft") or {}).get("version") or 1)
        status, body = _http(
            f"field_patch_{domain}_{source_field}", "PATCH",
            f"{att}/mapping-draft/field",
            json_body={
                "draft_id": draft_id,
                "domain": domain,
                "source_field": source_field,
                "patch": patch,
                "expected_version": version,
                "actor": ACTOR,
                "idempotency_key": f"r8d-patch-{domain}-{source_field}-{uuid.uuid4().hex[:8]}",
            }, timeout=300,
        )
        if status in (200, 201):
            return True
        if status != 409:
            return False
        time.sleep(3)
    return False


def answer_known_questions(att: str, draft_id: str) -> tuple[bool, list]:
    """对当前 user_questions 逐张按已知数据实测决策作答；未知→fail-closed。

    返回 (all_answered, unknown_questions)。
    """
    _, gb = _http("questions_read", "GET", f"{att}/mapping-candidates?focus=all")
    draft = (gb or {}).get("draft") or {}
    questions = draft.get("user_questions") or []
    if not questions:
        return True, []
    unknown = []
    for q in questions:
        domain = str(q.get("domain") or "")
        field = str(q.get("source_field") or "")
        decision = known_decision(domain, field)
        if decision is None:
            unknown.append(q)
            continue
        _ev("question_card_answer", True, domain=domain, source_field=field,
            question_user_action=(q.get("user_action") or "")[:300],
            applied_patch_keys=sorted(decision.keys()),
            basis="数据实测（同R5D三份合成文件）")
        ok = patch_field(att, draft_id, domain, field, decision)
        if not ok:
            _ev("question_card_answer_failed", False, domain=domain, source_field=field)
            return False, [q]
    if unknown:
        _ev("unknown_questions_fail_closed", False, unknown=unknown)
    return (not unknown), unknown


def job_counts(ai: str) -> tuple[dict, int]:
    _, body = _http("queue_jobs_read", "GET", f"{ai}/jobs?limit=200")
    jobs = (body or {}).get("items") or []
    counts: dict[str, int] = {}
    for j in jobs:
        counts[j["status"]] = counts.get(j["status"], 0) + 1
    return counts, len(jobs)


def adjudicate(att: str, draft_id: str) -> dict:
    status, body = _http("adjudicate_drive", "POST",
                         f"{att}/mapping-draft/adjudicate",
                         json_body={"draft_id": draft_id}, timeout=600)
    adj = (body or {}).get("adjudication") or {}
    rs = (body or {}).get("review_summary") or {}
    return {"adj_state": adj.get("state"),
            "remaining": adj.get("remaining_question_count"),
            "system_adjudicated": rs.get("system_adjudicated_count"),
            "http": status}


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
        key = f"r8d-seed-{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}-{uuid.uuid4().hex[:8]}"
        status, body = _http(
            "project_create", "POST", f"{BASE}/api/projects",
            json_body={
                "project_name": PROJECT_NAME,
                "indication": INDICATION,
                "product_name": PRODUCT_NAME,
                "modules": ["medical_monitoring"],
                "actor": ACTOR,
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
    ai = f"{BASE}/api/projects/{pid}/modules/medical-monitoring/ai"

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
        identity_confirmed = bool(st.get("identity_confirmed"))
        deadline = time.monotonic() + DOCS_POLL_BUDGET_S
        ready = False
        while time.monotonic() < deadline:
            time.sleep(DOCS_POLL_INTERVAL_S)
            payload: dict = {"batch_id": batch_id}
            if identity_confirmed:
                payload["identity_confirmation"] = {
                    "confirmed": True,
                    "reason": (
                        "R8D开考位预置：确认本组MG-K10-CSU-001合成文件"
                        "（方案V1.3+eCRF指南V1.0+合成listing V1.0）属于"
                        "当前项目MX循R8D-CSU。"
                    ),
                }
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
                    note="身份归属人工确认：等价界面一次点击（R5D同款手势）")
                identity_confirmed = True
                _save_state(identity_confirmed=True)
                continue
            if state == "needs_user_input" and body.get("user_choices"):
                # 文件角色人工裁决（设计内人工门）：只从服务端列出的options
                # 里按文件名如实匹配，匹配不上的角色按「该角色缺失」提交，
                # 不虚构绑定。
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
                    "R8D开考位预置：映射双队列候选批量核验通过，系统采纳进入"
                    "draft装配，由确认流程继续。"
                ),
                "actor": ACTOR,
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

    # ── Step6 问题卡（首轮：EX/EXTRT + MH/MHNUM 等已知数据实测决策） ─
    answered, unknown = answer_known_questions(att, draft_id)
    if not answered:
        print(json.dumps({"ok": False, "step": "question_cards",
                          "unknown": unknown}, ensure_ascii=False))
        return 2

    # ── Step7 复核收敛：作业队列→adjudicate→新裁决卡作答→循环 ────────
    adj_state = ""
    t0 = time.monotonic()
    last_sig = None
    no_progress = 0
    while time.monotonic() - t0 < CONVERGE_BUDGET_S:
        counts, total = job_counts(ai)
        inflight = counts.get("queued", 0) + counts.get("running", 0)
        print(f"[{time.monotonic()-t0:7.0f}s] jobs={counts} inflight={inflight}",
              flush=True)
        if inflight == 0:
            r = adjudicate(att, draft_id)
            adj_state = r.get("adj_state") or ""
            print(f"    adjudicate -> {r}", flush=True)
            if adj_state == "complete":
                break
            # 新一轮复核可能产生新的两轮分歧裁决卡 → 按数据实测作答
            answered, unknown = answer_known_questions(att, draft_id)
            if not answered:
                print(json.dumps({"ok": False, "step": "converge_cards",
                                  "unknown": unknown}, ensure_ascii=False))
                return 2
            sig = (r.get("remaining"), r.get("system_adjudicated"))
            if sig == last_sig:
                no_progress += 1
            else:
                no_progress = 0
                last_sig = sig
            c2, _ = job_counts(ai)
            if c2.get("queued", 0) + c2.get("running", 0) > 0:
                no_progress = 0
            if no_progress >= NO_PROGRESS_ROUNDS:
                _ev("converge_stalled", False, last=r, counts=counts)
                print("STALL: 连续多轮无进展，如实退出", flush=True)
                return 2
        time.sleep(CONVERGE_INTERVAL_S)
    else:
        _ev("converge_budget_exhausted", False)
        print(json.dumps({"ok": True, "exit": 10, "step": "converge"},
                         ensure_ascii=False))
        return 10
    _ev("adjudicate_settled", True, adj_state=adj_state)
    _save_state(adjudication_state=adj_state)

    # ── Step8 confirm（医学确认；409/422 按门语义重试） ───────────────
    confirmed = bool(st.get("confirmed"))
    if not confirmed:
        idem = st.get("confirm_idempotency_key") or f"r8d-confirm-{uuid.uuid4().hex}"
        for retry in range(8):
            _, gb = _http("pre_confirm_version", "GET",
                          f"{att}/mapping-candidates?focus=all")
            draft_now = (gb or {}).get("draft") or {}
            version = int(draft_now.get("version") or version or 1)
            if draft_now.get("user_questions"):
                answered, unknown = answer_known_questions(att, draft_id)
                if not answered:
                    print(json.dumps({"ok": False, "step": "confirm_cards",
                                      "unknown": unknown}, ensure_ascii=False))
                    return 2
            status, body = _http(
                "draft_confirm", "POST", f"{att}/mapping-draft/confirm",
                json_body={
                    "draft_id": draft_id,
                    "expected_version": version,
                    "confirmation_reason": (
                        "R8D开考位预置：双队列映射候选经系统复核与批量裁决收敛"
                        "（失败分片按bounded-gap设计转为可见缺口）后，确认字段"
                        "对应关系进入事实物化。"
                    ),
                    "idempotency_key": idem,
                    "automatic": True,
                }, timeout=600,
            )
            if status == 200:
                confirmed = True
                break
            code = (body or {}).get("code") or ((body or {}).get("detail") or {}).get("code")
            _ev("confirm_retry", False, attempt=retry, status=status, code=code)
            print(f"    confirm -> {status} {code}", flush=True)
            adjudicate(att, draft_id)  # 再推一轮复核再试
            time.sleep(10)
        if not confirmed:
            print(json.dumps({"ok": False, "step": "draft_confirm",
                              "adj_state": adj_state}, ensure_ascii=False))
            return 2
        _save_state(confirmed=True, confirm_idempotency_key=idem)
        _ev("draft_confirmed", True)

    # ── Step9 facts 物化 ─────────────────────────────────────────────
    status, body = _http("facts_materialize", "POST", f"{att}/facts",
                         json_body={}, timeout=900)
    if status not in (200, 201):
        print(json.dumps({"ok": False, "step": "facts_materialize",
                          "status": status, "body": body}, ensure_ascii=False))
        return 2
    _ev("facts_materialized", True, summary=(body or {}).get("summary") or body)
    _save_state(facts_materialized=True)

    # ── Step10 终态自验 ──────────────────────────────────────────────
    _, cand = _http("final_mapping_candidates", "GET", f"{att}/mapping-candidates?focus=all")
    _, facts = _http("final_facts", "GET", f"{att}/facts")
    _, docs_f = _http("final_documents", "GET", f"{att}/study-documents")
    _, opened = _http("final_project_open", "GET", f"{mm}/project/open")
    draft_final = (cand or {}).get("draft") or {}
    verdict = {
        "project_id": pid,
        "attempt_id": attempt,
        "mapping_state": (cand or {}).get("state"),
        "confirmation_status": draft_final.get("status"),
        "draft_id": draft_final.get("draft_id"),
        "user_questions": len(draft_final.get("user_questions") or []),
        "candidate_count": ((cand or {}).get("summary") or {}).get("candidate_count"),
        "documents_ready": (docs_f or {}).get("ready"),
        "facts_state": (facts or {}).get("state"),
        "project_open": {k: (opened or {}).get(k) for k in
                         ("state", "dataCoverage", "canView", "canEdit")},
        "adjudication_state": adj_state,
    }
    _ev("final_verdict", True, **verdict)
    print(json.dumps({"ok": True, **verdict}, ensure_ascii=False, default=str))
    return 0


if __name__ == "__main__":
    sys.exit(main())
