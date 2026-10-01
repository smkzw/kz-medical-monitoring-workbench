"""R11P 全链预检（第2次）：在隔离环境 8911 上用一次性预检项目「MX循R11P-CSU」
（精确名被占用则按API指引加-2后缀）把整条链从零真跑一遍，逐阶段计时。
驱动面继承 R10P 第3次全绿驱动（r10p_preflight3_csu.py，含 workspace/bootstrap
先种全局档、幂等键先持久化再重放两个关键工程事实），并补 R11D 轮新浮现的
ICF_TRACK.ICFVER/CM 裁决卡。

API 序列按 scripts/fullchain_sar_rerun_20260926/HANDOFF_SAR_RERUN_20260926.md
（sar_intake / sar_run_start / sar_publish_verify 的端点族）+ R5D-R9D 已在
8911 验证的驱动面（r5d/r8d/r9d_seed_csu.py）组装：

  建项 → 上传(data-admissions/upload) → 文档权威(study-documents
  analyze→resolve→ready，含身份确认+文件角色人工裁决两个设计内人工门)
  → 映射(candidates start/poll → adopt → 问题卡按数据实测作答 →
  adjudicate 收敛 → confirm) → facts → 运行(run-setup/options →
  prepare-and-start → 轮询 progress 至 run_state=completed，创建≠完成)
  → 发布(publication → available) → 结果(result-entry + overview 非空、
  受试者/发现数>0)。

原则（与 r9d_seed_csu.py 相同）：
  - 全部经 HTTP API 操作 8911，绝不触碰 8910/5177；
  - AI 作业真实产生、等待自然完成，不跳门、不伪造状态；
  - 已知状态碎片化家族（接入管线 confirmed vs 监查侧 unconfirmed）若在
    运行启动处拦截：fail-closed 退出码 3，捕获 console(/tmp/mm_api_8911.log)
    +API 双侧状态证据（r7 侧 draft.status/facts.state vs 409 detail 的
    readiness.implementation_status + source-manifest binding）；
  - 幂等：状态持久化 r11p2_preflight_state.json，已完成步骤直接复用；
  - 留痕：每步请求/响应摘要写 r11p2_preflight_evidence.jsonl。

退出码：0=全链通（8阶段全ok）；10=预算耗尽仍在推进（可重跑续）；
3=状态碎片化拦截（blockedAt 证据齐）；2=其他阻断/断言失败。
"""
from __future__ import annotations

import json
import subprocess
import sys
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path

import requests
from requests.adapters import HTTPAdapter

BASE = "http://127.0.0.1:8911"
CONSOLE_LOG = Path("/tmp/mm_api_8911.log")
STAGING = Path(
    "/Users/smkzw/Documents/康哲项目资料/AI/医学经理工作台"
    "/implementation/workbench/tester_staging_0927/synth_csu"
)
LISTING = STAGING / "MG-K10-CSU-001_合成测试数据_V1.0.xlsx"
PROTOCOL = STAGING / "MG-K10-CSU-001_临床研究方案_V1.3.docx"
ECRF = STAGING / "MG-K10-CSU-001_eCRF填写指南_V1.0.docx"

PROJECT_NAME = "MX循R11P-CSU"  # R11第1次已占用精确名（proj_user_d029b0208f85 在册
# 留原地待归档）；预期 409 同名→按 API 报错自指引加 -2 后缀（如实留痕）。
PROJECT_NAME_FALLBACK = "MX循R11P-CSU-2"
INDICATION = "慢性自发性荨麻疹"
PRODUCT_NAME = "MG-K10"
ACTOR = "r11p2_preflight"
PROJECT_NAME_FINAL = [PROJECT_NAME]  # 建项后回填实际生效名

HERE = Path(__file__).resolve().parent
STATE = HERE / "r11p2_preflight_state.json"
EVIDENCE = HERE / "r11p2_preflight_evidence.jsonl"

DOCS_POLL_BUDGET_S = 3600.0
DOCS_POLL_INTERVAL_S = 20.0
MAP_POLL_BUDGET_S = 7200.0
MAP_POLL_INTERVAL_S = 30.0
CONVERGE_BUDGET_S = 14400.0
CONVERGE_INTERVAL_S = 45.0
RUN_POLL_BUDGET_S = 10800.0   # 运行必须真正完成：3h预算
RUN_POLL_INTERVAL_S = 30.0
PUB_POLL_BUDGET_S = 1800.0
PUB_POLL_INTERVAL_S = 10.0
NO_PROGRESS_ROUNDS = 10

# ── 问题卡/裁决卡作答：R5D/R8D/R9D 同三份合成文件的数据实测结论 ──
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
# R10 本轮实测新增：两轮分歧裁决卡 CM/CMSTDAT + CM/CMENDAT（20261001T02:5x
# 卡片原文：主分析=独立复核=concomitant_medication_{start,end}_date，两侧
# 逐字相同——R3-01 家族表现）。作答依据：本轮 openpyxl 直读 CM 表实测：
# 表头=受试者编号/合并用药记录号/药物名称/用药目的/开始日期/结束日期/
# 目前是否持续；开始日期列32行合法日期、结束日期列33行合法日期、
# 同行 start≤end 32/33、药物名称35行全有值——起止结构成立。
R10_MEASURED_CARDS = {
    ("CM", "CMSTDAT"): ("concomitant_medication_start_date",
        "来源列标题'开始日期'（32行合法日期），与'结束日期'同行构成合并用药起止结构"),
    ("CM", "CMENDAT"): ("concomitant_medication_end_date",
        "来源列标题'结束日期'（33行合法日期，2026-02月集中），与'开始日期'同行配对（实测start≤end 32/33）"),
}
# R10P 第3次实测新增：DM 域4张「两侧判断逐字相同」矛盾卡（20261001本轮流
# 出，卡片原文主分析=独立复核=同值——R3-01 家族表现）。作答依据：本轮
# openpyxl 直读 DM 表实测：表头=受试者编号/中心编号/性别/年龄/试验分组/
# 随机日期/研究状态，第2行为CDISC变量名（SUBJID/SITEID/SEX/AGE/ARM/
# RANDDT/COMPSTATUS），数据16行（16名受试者）：
# 性别=男8/女8二值；年龄=16行全数值23~61；随机日期=16行全合法日期
# （2026-03-02~2026-04-01）；研究状态=16行全列唯一值'完成'。
R10P3_DM_CARDS = {
    ("DM", "AGE"): ("subject_age",
        "来源列标题'年龄'（变量名AGE），16行全数值（23~61岁），受试者人口学年龄"),
    ("DM", "COMPSTATUS"): ("study_completion_status",
        "来源列标题'研究状态'（变量名COMPSTATUS），16行全列唯一值'完成'，研究完成状态"),
    ("DM", "RANDDT"): ("randomization_date",
        "来源列标题'随机日期'（变量名RANDDT），16行全合法日期（2026-03-02~2026-04-01），随机化日期"),
    ("DM", "SEX"): ("sex",
        "来源列标题'性别'（变量名SEX），16行二值分布（男8/女8），受试者性别"),
}
# R11D 轮（20261001，同三份合成文件）第三轮复核浮现并实测作答的3张两轮裁决卡
# （r11d_seed_evidence.jsonl unknown_questions_fail_closed 后按 openpyxl 直读补答，
# confirm 200 / draft v71 confirmed）。依据：① CM 表起止日期33行全合法日期且
# 同行配对；② ICF_TRACK'知情版本'列16行全列唯一值'v2.1'，与'知情状态'同行。
R11_ROUND3_CARDS = {
    ("CM", "CMENDAT"): ("cm_end_date",
        "来源列标题'结束日期'（33行数据全为合法日期，如2026-02-15×3），"
        "与'开始日期'(CMSTDAT)/'目前是否持续'(CMONGO)同行配对，构成合并用药起止结构"),
    ("CM", "CMSTDAT"): ("cm_start_date",
        "来源列标题'开始日期'（33行数据全为合法日期，如2025-11-01×3），"
        "合并用药起始日期，与结束日期/持续标志同行"),
    ("ICF_TRACK", "ICFVER"): ("informed_consent_version",
        "来源列标题'知情版本'（16行数据全列唯一值'v2.1'），知情同意书版本号，"
        "与'知情状态'(ICFSTATE)同行配对"),
}

R9_ROUND4_CARDS = {
    ("CM", "CMINDC"): ("cm_indication",
        "来源列标题'用药目的'（33行有值：既往用药×32、哮喘病史长期用药×1），用药目的语义"),
    ("CM", "CMNUM"): ("cm_record_number",
        "来源列标题'合并用药记录号'（C001式34行全列唯一），域内记录标识"),
    ("CM", "CMONGO"): ("cm_ongoing_flag",
        "来源列标题'目前是否持续'（是17/否17二值分布）"),
    ("CM", "CMTRT"): ("cm_treatment_name",
        "来源列标题'药物名称'（氯雷他定/阿托伐他汀钙/苯磺酸氨氯地平/西替利嗪等药名）"),
    ("LB_HEM", "LBREF"): ("lab_reference_range",
        "来源列标题'参考范围'（125-350×64、9-50×64），与检验名称/结果同行配对"),
    ("LB_HEM", "LBTEST"): ("lab_test_name",
        "来源列标题'实验室指标名称'（血小板计数×64、ALT×64），检验项目名称"),
}


def known_decision(domain: str, source_field: str) -> dict | None:
    if (domain, source_field) == ("EX", "EXTRT"):
        return {"user_action": EXTRT_ANSWER}
    if (domain, source_field) == ("MH", "MHNUM"):
        return {"recommended_role": "metadata.record_id", "user_action": MHNUM_ANSWER}
    for table in (FINAL_CARDS, R8_ROUND2_CARDS, R9_ROUND4_CARDS, R10_MEASURED_CARDS,
                  R10P3_DM_CARDS, R11_ROUND3_CARDS):
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

STAGES: dict[str, dict] = {}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _ev(step: str, ok: bool, **detail: object) -> None:
    _ev_fh.write(
        json.dumps(
            {"ts": _now(), "run": "r11p2_preflight", "step": step, "ok": bool(ok), **detail},
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


def stage_begin(name: str) -> float:
    print(f"[STAGE {name}] begin {datetime.now().strftime('%H:%M:%S')}", flush=True)
    return time.monotonic()


def stage_end(name: str, t0: float, ok: bool, note: str) -> None:
    seconds = round(time.monotonic() - t0, 1)
    STAGES[name] = {"ok": bool(ok), "seconds": seconds, "note": note}
    _save_state(stages=STAGES)
    _ev("stage_result", ok, stage=name, seconds=seconds, note=note)
    print(f"[STAGE {name}] {'OK' if ok else 'FAIL'} {seconds:.0f}s — {note}", flush=True)


def patch_field(att: str, draft_id: str, domain: str, source_field: str,
                patch: dict) -> bool:
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
                "idempotency_key": f"r11p2-patch-{domain}-{source_field}-{uuid.uuid4().hex[:8]}",
            }, timeout=300,
        )
        if status in (200, 201):
            return True
        if status != 409:
            return False
        time.sleep(3)
    return False


def answer_known_questions(att: str, draft_id: str) -> tuple[bool, list]:
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
            applied_patch_keys=sorted(decision.keys()),
            basis="数据实测（同R5D/R8D/R9D三份合成文件）")
        ok = patch_field(att, draft_id, domain, field, decision)
        if not ok:
            _ev("question_card_answer_failed", False, domain=domain, source_field=field)
            return False, [q]
    if unknown:
        _ev("unknown_questions_fail_closed", False, unknown=unknown)
    return (not unknown), unknown


def job_counts(ai: str) -> tuple[dict, int]:
    _, body = _http("queue_jobs_read", "GET", f"{ai}/jobs?limit=500")
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


def console_tail(lines: int = 40) -> str:
    try:
        out = subprocess.run(["tail", "-n", str(lines), str(CONSOLE_LOG)],
                             capture_output=True, text=True, timeout=10)
        return (out.stdout or "")[-4000:]
    except Exception as exc:  # noqa: BLE001
        return f"<console read failed: {exc}>"


def ai_nodes_summary(pid: str) -> list[dict]:
    """从AI台账（module ai/jobs，即隔离实例的AI账本）按节点聚合路由与终态。"""
    ai = f"{BASE}/api/projects/{pid}/modules/medical-monitoring/ai"
    _, body = _http("ai_ledger_read", "GET", f"{ai}/jobs?limit=500")
    jobs = (body or {}).get("items") or []
    groups: dict[tuple, dict] = {}
    for j in jobs:
        bk = str(j.get("business_key") or "")
        role = "primary" if ":primary:" in bk else ("verifier" if ":verifier:" in bk else "pipeline")
        key = (str(j.get("task_type")), role)
        g = groups.setdefault(key, {
            "task_type": key[0], "role": key[1], "routes": {},
            "statuses": {}, "count": 0,
        })
        g["count"] += 1
        route = f"{j.get('provider')}/{j.get('response_model') or j.get('requested_model')}"
        g["routes"][route] = g["routes"].get(route, 0) + 1
        g["statuses"][j.get("status")] = g["statuses"].get(j.get("status"), 0) + 1
    return sorted(groups.values(), key=lambda g: (g["task_type"], g["role"]))


def fragmentation_evidence(pid: str, att: str, gate_step: str, gate_status: int,
                           gate_body: dict) -> dict:
    """状态碎片化拦截时 console/API 双侧证据采集。"""
    _, cand = _http("frag_mapping_state", "GET", f"{att}/mapping-candidates?focus=all")
    _, facts = _http("frag_facts_state", "GET", f"{att}/facts")
    _, manifest = _http("frag_source_manifest", "GET",
                        f"{BASE}/api/projects/{pid}/source-manifest")
    draft = (cand or {}).get("draft") or {}
    bindings = []
    if isinstance(manifest, dict):
        for m in (manifest.get("modules") or []):
            if isinstance(m, dict) and m.get("module") in (None, "medical_monitoring"):
                bindings.append({k: m.get(k) for k in
                                 ("module", "implementation_status", "status",
                                  "source_count") if k in m})
    detail = gate_body.get("detail") if isinstance(gate_body.get("detail"), dict) else gate_body
    ev = {
        "gate": {"step": gate_step, "http_status": gate_status,
                 "code": detail.get("code"),
                 "readiness": detail.get("readiness")},
        "api_side_r7_pipeline": {
            "mapping_state": (cand or {}).get("state"),
            "draft_status": draft.get("status"),
            "draft_id": draft.get("draft_id"),
            "facts_state": (facts or {}).get("state"),
        },
        "api_side_source_manifest_bindings": bindings or manifest,
        "console_tail_mm_api_8911": console_tail(),
    }
    _ev("fragmentation_evidence", False, **ev)
    return ev


def main() -> int:
    for p in (LISTING, PROTOCOL, ECRF):
        if not p.is_file():
            _ev("prerequisite", False, reason=f"missing {p}")
            print(f"FAIL: missing {p}")
            return 2
    st = _load_state()

    # ── 阶段1 建项（幂等：已有 project_id 复用） ─────────────────────
    pid = st.get("project_id")
    t0 = stage_begin("建项")
    if not pid:
        key = ""
        final_name = PROJECT_NAME
        status, body = 0, {}
        for attempt_name in (PROJECT_NAME, PROJECT_NAME_FALLBACK):
            key = f"r11p2-preflight-{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}-{uuid.uuid4().hex[:8]}"
            status, body = _http(
                "project_create", "POST", f"{BASE}/api/projects",
                json_body={
                    "project_name": attempt_name,
                    "indication": INDICATION,
                    "product_name": PRODUCT_NAME,
                    "modules": ["medical_monitoring"],
                    "actor": ACTOR,
                    "idempotency_key": key,
                },
            )
            if status == 201:
                final_name = attempt_name
                break
            _ev("project_create_rejected", False,
                attempted_name=attempt_name, http_status=status,
                body=str(body)[:400])
            if attempt_name is PROJECT_NAME:
                print(f"  [建项] 精确名 {attempt_name} 被拒 http={status}："
                      f"{str(body)[:200]}", flush=True)
                continue  # 预期内同名409→按API指引换-3后缀重试（幂等键不变）
            break
        proj = (body or {}).get("project") or {}
        if status != 201 or not proj.get("project_id"):
            stage_end("建项", t0, False, f"http={status} body={str(body)[:300]}")
            return 2
        pid = proj["project_id"]
        PROJECT_NAME_FINAL[0] = final_name
        _save_state(project_id=pid, create_key=key,
                    project_name=proj.get("project_name"))
    _ev("project_ready", True, project_id=pid)
    stage_end("建项", t0, True, f"project_id={pid} name={PROJECT_NAME_FINAL[0]}")

    mm = f"{BASE}/api/projects/{pid}/modules/medical-monitoring/r7"
    adm = f"{mm}/data-admissions"
    ai = f"{BASE}/api/projects/{pid}/modules/medical-monitoring/ai"

    # ── 阶段2 上传（synth_csu listing） ──────────────────────────────
    attempt = st.get("attempt_id")
    t0 = stage_begin("上传")
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
            stage_end("上传", t0, False, f"http={status} body={str(body)[:300]}")
            return 2
        _save_state(attempt_id=attempt)
    att = f"{adm}/{attempt}"
    _, up_read = _http("admission_readback", "GET", f"{att}")
    up_note = f"attempt={attempt} summary={str((up_read or {}).get('summary') or '')[:200]}"
    stage_end("上传", t0, True, up_note)

    # ── 阶段3 文档权威（双VLM analyze→resolve→ready） ────────────────
    t0 = stage_begin("文档权威")
    if not st.get("documents_ready"):
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
                    stage_end("文档权威", t0, False,
                              f"analyze http={status} body={str(body)[:300]}")
                    return 2
                batch_id = (body or {}).get("analysis_token")
                _save_state(docs_batch_id=batch_id)
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
                            "R11P第2次全链预检：确认本组MG-K10-CSU-001合成文件"
                            "（方案V1.3+eCRF指南V1.0+合成listing V1.0）属于"
                            f"当前项目{PROJECT_NAME_FINAL[0]}。"
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
                    identity_confirmed = True
                    _save_state(identity_confirmed=True)
                    continue
                if state == "needs_user_input" and body.get("user_choices"):
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
                    status, body = _http(
                        "documents_resolve_role_selection", "POST",
                        f"{att}/study-documents/resolve",
                        json_body={"batch_id": batch_id,
                                   "user_role_selections": selections},
                        timeout=300,
                    )
                    _save_state(role_selections=selections)
                    gs, gdocs = _http("documents_readiness", "GET", f"{att}/study-documents")
                    if (gdocs or {}).get("ready"):
                        ready = True
                        break
                    continue
                if state in ("needs_user_input", "failed"):
                    stage_end("文档权威", t0, False, f"state={state} body={str(body)[:300]}")
                    return 2
            if not ready:
                stage_end("文档权威", t0, False, "预算内未到ready（可重跑续）")
                return 10
        _save_state(documents_ready=True)
    _, docs_f = _http("final_documents", "GET", f"{att}/study-documents")
    stage_end("文档权威", t0, bool((docs_f or {}).get("ready")),
              f"ready={(docs_f or {}).get('ready')} headline={(docs_f or {}).get('headline')}")
    if not (docs_f or {}).get("ready"):
        return 2

    # ── 阶段4 映射确认（start→poll→adopt→问题卡→收敛→confirm） ──────
    t0 = stage_begin("映射确认")
    status, body = _http("mapping_candidates_read", "GET", f"{att}/mapping-candidates")
    state = (body or {}).get("state")
    if state not in ("candidates_ready", "needs_attention"):
        status, body = _http(
            "mapping_candidates_start", "POST", f"{att}/mapping-candidates",
            json_body={}, timeout=600,
        )
        if status not in (200, 201):
            stage_end("映射确认", t0, False,
                      f"start http={status} body={str(body)[:300]}")
            return 2
        deadline = time.monotonic() + MAP_POLL_BUDGET_S
        while time.monotonic() < deadline:
            time.sleep(MAP_POLL_INTERVAL_S)
            gs, gbody = _http("mapping_candidates_poll", "GET", f"{att}/mapping-candidates")
            state = (gbody or {}).get("state")
            summ = (gbody or {}).get("summary") or {}
            ver = ((gbody or {}).get("verification") or {}).get("summary") or {}
            print(f"  [map] state={state} primary={summ.get('completed_job_count')}/"
                  f"{summ.get('job_count')} verifier={ver.get('completed_job_count')}/"
                  f"{ver.get('job_count')}", flush=True)
            if state in ("candidates_ready", "needs_attention"):
                break
        else:
            stage_end("映射确认", t0, False, "映射双队列预算内未就绪（可重跑续）")
            return 10
    _save_state(mapping_state=state)

    draft_id = st.get("draft_id")
    version = st.get("draft_version")
    if not draft_id:
        status, body = _http(
            "draft_adopt", "POST", f"{att}/mapping-draft",
            json_body={
                "reason": "R11P第2次全链预检：映射双队列候选批量核验通过，系统采纳进入draft装配。",
                "actor": ACTOR,
            }, timeout=600,
        )
        proj = body or {}
        draft = proj.get("draft") or {}
        draft_id = draft.get("draft_id") or proj.get("draft_id")
        version = draft.get("version") or proj.get("version")
        if status not in (200, 201) or not draft_id:
            stage_end("映射确认", t0, False,
                      f"adopt http={status} body={str(body)[:300]}")
            return 2
        _save_state(draft_id=draft_id, draft_version=version)

    answered, unknown = answer_known_questions(att, draft_id)
    if not answered:
        stage_end("映射确认", t0, False, f"未知问题卡 fail-closed：{str(unknown)[:400]}")
        return 2

    adj_state = ""
    tc0 = time.monotonic()
    last_sig = None
    no_progress = 0
    while time.monotonic() - tc0 < CONVERGE_BUDGET_S:
        counts, total = job_counts(ai)
        inflight = counts.get("queued", 0) + counts.get("running", 0)
        print(f"  [conv {time.monotonic()-tc0:6.0f}s] jobs={counts}", flush=True)
        if inflight == 0:
            r = adjudicate(att, draft_id)
            adj_state = r.get("adj_state") or ""
            print(f"    adjudicate -> {r}", flush=True)
            if adj_state == "complete":
                break
            answered, unknown = answer_known_questions(att, draft_id)
            if not answered:
                stage_end("映射确认", t0, False,
                          f"收敛期未知裁决卡 fail-closed：{str(unknown)[:400]}")
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
                stage_end("映射确认", t0, False,
                          f"收敛停滞 last={r} counts={counts}")
                return 2
        time.sleep(CONVERGE_INTERVAL_S)
    else:
        stage_end("映射确认", t0, False, "复核收敛预算耗尽（可重跑续）")
        return 10

    if not st.get("confirmed"):
        idem = st.get("confirm_idempotency_key") or f"r11p2-confirm-{uuid.uuid4().hex}"
        confirmed = False
        for retry in range(10):
            _, gb = _http("pre_confirm_version", "GET",
                          f"{att}/mapping-candidates?focus=all")
            draft_now = (gb or {}).get("draft") or {}
            version = int(draft_now.get("version") or version or 1)
            if draft_now.get("user_questions"):
                answered, unknown = answer_known_questions(att, draft_id)
                if not answered:
                    stage_end("映射确认", t0, False,
                              f"confirm前未知问题卡：{str(unknown)[:400]}")
                    return 2
            status, body = _http(
                "draft_confirm", "POST", f"{att}/mapping-draft/confirm",
                json_body={
                    "draft_id": draft_id,
                    "expected_version": version,
                    "confirmation_reason": (
                        "R11P第2次全链预检：双队列映射候选经系统复核与批量裁决收敛后，"
                        "确认字段对应关系进入事实物化。"
                    ),
                    "idempotency_key": idem,
                    "automatic": True,
                }, timeout=600,
            )
            if status == 200:
                confirmed = True
                break
            code = (body or {}).get("code") or ((body or {}).get("detail") or {}).get("code")
            print(f"    confirm -> {status} {code}", flush=True)
            adjudicate(att, draft_id)
            time.sleep(10)
        if not confirmed:
            stage_end("映射确认", t0, False, "confirm 未通过")
            return 2
        _save_state(confirmed=True, confirm_idempotency_key=idem)
    _, cand = _http("final_mapping_candidates", "GET", f"{att}/mapping-candidates?focus=all")
    draft_final = (cand or {}).get("draft") or {}
    ok4 = draft_final.get("status") == "confirmed"
    stage_end("映射确认", t0, ok4,
              f"state={(cand or {}).get('state')} draft.status={draft_final.get('status')} "
              f"adj={adj_state} candidates={((cand or {}).get('summary') or {}).get('candidate_count')}")
    if not ok4:
        return 2

    # ── 阶段5 facts 物化 ─────────────────────────────────────────────
    t0 = stage_begin("facts")
    if not st.get("facts_materialized"):
        status, body = _http("facts_materialize", "POST", f"{att}/facts",
                             json_body={}, timeout=900)
        if status not in (200, 201):
            stage_end("facts", t0, False, f"http={status} body={str(body)[:300]}")
            return 2
        _save_state(facts_materialized=True)
    _, facts = _http("final_facts", "GET", f"{att}/facts")
    fstate = (facts or {}).get("state")
    fsumm = (facts or {}).get("summary") or {}
    ok5 = fstate == "ready"
    stage_end("facts", t0, ok5,
              f"state={fstate} summary={str(fsumm or str(facts)[:200])[:200]}")
    if not ok5:
        return 2

    # ── 阶段6 运行监查（必须真正完成 run_state=completed） ────────────
    t0 = stage_begin("运行")
    run_token = st.get("run_token")
    run_state_now = ""
    if not run_token:
        status, options = _http("run_setup_options", "GET", f"{mm}/run-setup/options",
                                timeout=300)
        if status != 200:
            frag = None
            code = (options or {}).get("code") or ((options or {}).get("detail") or {}).get("code")
            if code and "readiness" in str(code):
                frag = fragmentation_evidence(pid, att, "run-setup/options", status, options)
            stage_end("运行", t0, False,
                      f"run-setup/options http={status} code={code}"
                      + ("（状态碎片化拦截，证据已留痕）" if frag else ""))
            _save_state(blocked_at="运行启动", blocked_detail=frag or {"options": options})
            return 3 if frag else 2
        cur = options.get("current_data") or {}
        snapshot_token = cur.get("snapshot_token")
        modes = {m.get("mode"): m for m in options.get("modes", [])}
        daily = modes.get("daily") or {}
        basis = "full"
        # 产品既定步骤（HANDOFF_FULLCHAIN_20260923 关键工程事实：prepare-and-start
        # 需 workspace/bootstrap 先种全局档；新项目首次启动运行前执行一次）。
        if not st.get("workspace_bootstrapped"):
            bs_status, bs_body = _http(
                "workspace_bootstrap", "POST", f"{mm}/workspace/bootstrap",
                json_body={}, timeout=300,
            )
            if bs_status not in (200, 201, 202):
                stage_end("运行", t0, False,
                          f"workspace/bootstrap http={bs_status} body={str(bs_body)[:300]}")
                _save_state(blocked_at="运行启动", blocked_detail={"bootstrap": bs_body})
                return 2
            _save_state(workspace_bootstrapped=True)
        # 幂等键先持久化再用：prepare 中途失败会留孤儿 waiting_start 预约，
        # 重试必须用同一键重放（run_routes 的 replay 分支会补完同一运行），
        # 换新键会被 enforce_in_flight 以 409 in_flight_conflict 拒绝。
        run_idem = st.get("run_start_idem") or (
            f"r11p2-run-{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}-{uuid.uuid4().hex[:8]}"
        )
        if not st.get("run_start_idem"):
            _save_state(run_start_idem=run_idem)
        status, body = _http(
            "prepare_and_start", "POST", f"{mm}/runs/prepare-and-start",
            json_body={
                "mode": "daily",
                "execution_basis": basis,
                "current_snapshot_token": snapshot_token,
                "risk_rule_tokens": [],
                "idempotency_key": run_idem,
            }, timeout=600,
        )
        _save_state(run_start_idem=run_idem)
        if status not in (200, 201, 202):
            frag = None
            code = (body or {}).get("code") or ((body or {}).get("detail") or {}).get("code")
            if code and ("readiness" in str(code) or "source" in str(code)):
                frag = fragmentation_evidence(pid, att, "prepare-and-start", status, body)
            stage_end("运行", t0, False,
                      f"prepare-and-start http={status} code={code} msg={str((body or {}).get('message') or (body or {}).get('detail'))[:200]}"
                      + ("（状态碎片化拦截，证据已留痕）" if frag else ""))
            _save_state(blocked_at="运行启动", blocked_detail=frag or {"start_body": body})
            return 3 if frag else 2
        run_token = body.get("public_run_token")
        _save_state(run_token=run_token, run_id=body.get("run_id"))
        _ev("run_started", True, run_token=run_token,
            snapshot=str(snapshot_token)[:40],
            scope=cur.get("scope_description"))
    # 轮询至 completed（创建≠完成）
    deadline = time.monotonic() + RUN_POLL_BUDGET_S
    prog = {}
    last_line = 0.0
    while time.monotonic() < deadline:
        gs, prog = _http("run_progress", "GET",
                         f"{mm}/runs/{run_token}/progress", timeout=120)
        run_state_now = str((prog or {}).get("run_state") or "")
        if time.monotonic() - last_line > 60:
            counts, _ = job_counts(ai)
            print(f"  [run {time.monotonic()-(deadline-RUN_POLL_BUDGET_S):6.0f}s] "
                  f"run_state={run_state_now} jobs={counts}", flush=True)
            last_line = time.monotonic()
        if run_state_now == "completed":
            break
        if run_state_now in ("failed", "ended_incomplete"):
            break
        time.sleep(RUN_POLL_INTERVAL_S)
    else:
        stage_end("运行", t0, False,
                  f"运行在{RUN_POLL_BUDGET_S:.0f}s预算内未完成（可重跑续） last={run_state_now}")
        return 10
    result_available = bool((prog or {}).get("result_available"))
    ok6 = run_state_now == "completed"
    stage_end("运行", t0, ok6,
              f"run_state={run_state_now} result_available={result_available} "
              f"run_token={run_token}")
    if not ok6:
        _save_state(blocked_at="运行执行", blocked_detail={"run_state": run_state_now,
                                                            "progress": prog})
        return 2

    # ── 阶段7 发布（publication → available） ────────────────────────
    t0 = stage_begin("发布")
    pub = {}
    pub_state = ""
    status, pub = _http(
        "publication_post", "POST", f"{mm}/runs/{run_token}/publication",
        json_body={"idempotency_key":
                   f"r11p2-pub-{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}-{uuid.uuid4().hex[:8]}"},
        timeout=600,
    )
    if status not in (200, 201, 202):
        stage_end("发布", t0, False, f"http={status} body={str(pub)[:300]}")
        _save_state(blocked_at="发布", blocked_detail=pub)
        return 2
    pub_state = str(pub.get("publication_state") or "")
    deadline = time.monotonic() + PUB_POLL_BUDGET_S
    while pub_state != "available" and time.monotonic() < deadline:
        if pub_state in ("recoverable_failed", "blocked", "failed"):
            break
        time.sleep(PUB_POLL_INTERVAL_S)
        gs, pub = _http("publication_get", "GET", f"{mm}/runs/{run_token}/publication")
        pub_state = str(pub.get("publication_state") or "")
    ok7 = pub_state == "available"
    stage_end("发布", t0, ok7, f"publication_state={pub_state}")
    if not ok7:
        _save_state(blocked_at="发布", blocked_detail=pub)
        return 2
    result_context_token = str(pub.get("result_context_token") or "")
    _save_state(publication_state=pub_state, result_context_token=result_context_token)

    # ── 阶段8 结果可读（overview 非空、受试者/发现数>0） ─────────────
    t0 = stage_begin("结果")
    entry_status, entry = _http("result_entry", "GET",
                                f"{mm}/runs/{run_token}/result-entry")
    overview = {}
    if not result_context_token and isinstance(entry, dict):
        result_context_token = str(entry.get("result_context_token") or "")
    if result_context_token:
        ov_status, overview = _http(
            "result_overview", "GET",
            f"{mm}/results/{result_context_token}/overview", timeout=300)
    ov_str = json.dumps(overview or {}, ensure_ascii=False)
    finding_count = 0
    subject_count = 0
    risk_count = 0
    if isinstance(overview, dict):
        proj = overview.get("projection") or {}
        if not isinstance(proj, dict):
            proj = {}
        for key in ("finding_count", "findings_count", "total_findings"):
            if isinstance(overview.get(key), int):
                finding_count = max(finding_count, overview[key])
        # 实测 overview 形态（finding_dto_v1）：发现=projection.query_findings
        # （发布冻结发现包，query_findings_meta.total 为权威计数）；风险=
        # projection.current_risks；受试者=projection.subjects。
        qf = proj.get("query_findings")
        if isinstance(qf, list):
            finding_count = max(finding_count, len(qf))
        qfm = proj.get("query_findings_meta") or {}
        if isinstance(qfm.get("total"), int):
            finding_count = max(finding_count, qfm["total"])
        cr = proj.get("current_risks")
        if isinstance(cr, list):
            risk_count = len(cr)
        for key in ("subject_count", "subjects_count", "total_subjects"):
            if isinstance(overview.get(key), int):
                subject_count = max(subject_count, overview[key])
        subjects = proj.get("subjects") or overview.get("subjects")
        if isinstance(subjects, list):
            subject_count = max(subject_count, len(subjects))
        if finding_count == 0:
            finding_count = _deep_count(overview, ("finding",))
        if subject_count == 0:
            subject_count = _deep_count(overview, ("subject", "subjects_total"))
    ok8 = bool(ov_str.strip("{}")) and entry_status == 200 and (
        finding_count > 0 and subject_count > 0)
    stage_end("结果", t0, ok8,
              f"entry_http={entry_status} overview_bytes={len(ov_str)} "
              f"finding_count={finding_count} subject_count={subject_count} "
              f"current_risks={risk_count} "
              f"rct={result_context_token[:30]}")
    _save_state(result_verdict={"overview_bytes": len(ov_str),
                                "finding_count": finding_count,
                                "subject_count": subject_count})

    nodes = ai_nodes_summary(pid)
    _save_state(ai_nodes=nodes)
    print(json.dumps({"ok": all(v["ok"] for v in STAGES.values()),
                      "stages": STAGES, "ai_nodes": nodes},
                     ensure_ascii=False, default=str))
    return 0 if all(v["ok"] for v in STAGES.values()) else 2


def _deep_count(payload, tokens: tuple[str, ...]) -> int:
    best = 0
    if isinstance(payload, dict):
        for k, v in payload.items():
            kl = str(k).lower()
            if any(t in kl for t in tokens) and isinstance(v, int):
                best = max(best, v)
            else:
                best = max(best, _deep_count(v, tokens))
    elif isinstance(payload, list):
        for item in payload:
            best = max(best, _deep_count(item, tokens))
    return best


if __name__ == "__main__":
    sys.exit(main())
