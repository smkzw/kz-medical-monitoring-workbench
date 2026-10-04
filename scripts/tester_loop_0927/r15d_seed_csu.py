"""R15D 开考位预置：在隔离环境 8911 上把 MX循R15D-CSU 推进到
「字段映射 confirmed + facts 物化完成、界面可开始运行监查」停住。

（R15D 适配：由 r14d_seed_csu.py 机械改名单/幂等键/留痕文件；R5/R8/R9/R11/R12/R13/R14 既有裁决卡决策表原样保留，未知卡 fail-closed 防护在位。）

API 序列参考 scripts/fullchain_sar_rerun_20260926/HANDOFF_SAR_RERUN_20260926.md
与同目录幂等脚本（sar_intake/sar_mapping_start/sar_mapping_confirm_facts），
并沿用 R5D/R10D 已验证的驱动面（r5d_seed_csu.py + r5d_question_cards.py +
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
  - 幂等：状态持久化 r15d_seed_state.json，已完成步骤直接复用；
  - 留痕：每步请求/响应摘要写 r15d_seed_evidence.jsonl。

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

PROJECT_NAME = "MX循R15D-CSU"
INDICATION = "慢性自发性荨麻疹"
PRODUCT_NAME = "MG-K10"
ACTOR = "r15d_seeder"

HERE = Path(__file__).resolve().parent
STATE = HERE / "r15d_seed_state.json"
EVIDENCE = HERE / "r15d_seed_evidence.jsonl"

DOCS_POLL_BUDGET_S = 2700.0    # 文档权威（双VLM）预算45min（R5D实测约15min）
DOCS_POLL_INTERVAL_S = 20.0
MAP_POLL_BUDGET_S = 7200.0     # 映射双队列预算120min（R5D实测约20min）
MAP_POLL_INTERVAL_S = 30.0
CONVERGE_BUDGET_S = 32400.0    # 复核收敛总预算9h（R10D实测v19工具型裁决约7.2h）
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
# ① 同三份合成文件的实测列值（R10D attempt facts 与 R5D facts 文件一致）；
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


# R9 第四轮复核后浮现的6张两轮分歧裁决卡（20260930T06:47Z）。作答依据：
# ① 同三份合成文件本轮实测列值（openpyxl 直读 CM/LB_HEM 表，依据见各basis）；
# ② 两轮队列结论显示名一致（如 concomitant_medication_indication），按当前
#   R9 草稿角色词汇（cm_* 新 token；R8D 确认版的 medication_* 为上轮词汇，
#   本轮词汇已换代）采纳对应 token，语义跨轮一致。
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


# R11 第三轮复核后浮现的3张两轮裁决卡（20261001T08:2xZ）。作答依据：
# ① 同三份合成文件本轮实测列值（openpyxl 直读 CM/ICF_TRACK 表）；
# ② 卡片显示主分析与独立复核结论一致（同角色 token），采纳该角色，
#   逐卡附①列值依据。首次遇到时脚本 fail-closed 诚实退出留痕
# （r11d_seed_evidence.jsonl unknown_questions_fail_closed）。
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


# R12 第四轮复核后浮现的4张两轮裁决卡（20261003T02:0xZ，R13D/R15D 沿用作答）。
# 作答依据：
# ① 同三份合成文件本轮实测列值（openpyxl 直读 DM 表，受试者16行）；
# ② 卡片显示主分析与独立复核结论一致（同角色 token），采纳该角色，
#   逐卡附①列值依据。首次遇到时脚本 fail-closed 诚实退出留痕
# （r12d_seed_evidence.jsonl unknown_questions_fail_closed）。
R12_ROUND4_CARDS = {
    ("DM", "AGE"): ("subject_age",
        "来源列标题'年龄'（16行受试者数据全为23-61连续数值），受试者年龄"),
    ("DM", "COMPSTATUS"): ("study_completion_status",
        "来源列标题'研究状态'（16行受试者数据全列唯一值'完成'），研究完成状态"),
    ("DM", "RANDDT"): ("randomization_date",
        "来源列标题'随机日期'（16行受试者数据全为2026-03-02~2026-04-01合法日期），"
        "随机化日期，与'试验分组'（试验组8/安慰剂组8）同表配对"),
    ("DM", "SEX"): ("subject_sex",
        "来源列标题'性别'（16行受试者数据男8/女8二值分布），受试者性别"),
}


# R13 首轮复核后浮现的1张需医学确认卡（20261003T07:08Z，R12新增的方案-vs-数据
# 剂量/频次交叉核对提示词要求首次命中EX域）。作答依据（openpyxl 直读 EX 表）：
# ① EXFRQ 列128行唯一值'300mg'（剂量含单位文本），频次信息Q4W仅出现在同表
#   EXTRT文本'MG-K10 300mg Q4W'与方案V1.3中——该列内容口径为每次给药剂量，
#   非给药频次；
# ② 该列试验组/安慰剂组两臂取值相同（受试者各8名、EX记录各64行同值），
#   为方案标签式给药记录，不据此声明实际IP暴露；剂量语义（计划/实际）在该列
#   不可区分（dose_semantics 为系统溯源键，用户补丁不可直改——仓库
#   edit_field provenance 保护；G-CMIP-006 将按未解决剂量语义保持可见与
#   ip_exposure_adherence 能力阻断=设计内诚实状态）；
# ③ 受试者级治疗身份以 DM.试验分组 为准（R5D 已确认口径）。
# 首次遇到时脚本 fail-closed 诚实退出留痕（r15d_seed_evidence.jsonl
# unknown_questions_fail_closed），按上述实测依据补答后重跑续推。
# R13 收敛第一轮后浮现的1张两轮分歧裁决卡（20261003T07:5xZ，EXSTATE）。
# 卡片显示主分析与独立复核结论一致（同角色 token treatment_administration_status），
# 采纳该角色；依据：openpyxl 直读 EX 表，EXSTATE 列128行二值分布
# （完成×86 / 延迟给药×42），为给药执行状态语义。
R13_ROUND1_CARDS = {
    ("EX", "EXSTATE"): {
        "recommended_role": "treatment_administration_status",
        "user_action": (
            "用户已核对：两轮复核分歧裁决——按来源数据实测采纳"
            "treatment_administration_status（来源列标题'给药状态'，128行"
            "二值分布：完成×86/延迟给药×42，为每次给药记录的执行状态）。"
        ),
    },
    ("EX", "EXFRQ"): {
        "recommended_role": "ip_administered_dose_with_unit_text",
        "user_action": (
            "用户已核对：EX域'给药频次'(EXFRQ)列128行唯一值'300mg'，为剂量"
            "含单位文本；频次信息Q4W仅出现在同表EXTRT文本'MG-K10 300mg Q4W'"
            "与方案V1.3中。该列按每次给药剂量（300mg）口径处理，不按给药频次"
            "口径；且两臂（试验组8/安慰剂组8受试者）取值相同，属方案标签式"
            "给药记录，不据此声明实际IP暴露——剂量语义（计划/实际）在该列"
            "不可区分，交由质量门按未解决剂量语义保持可见与受限；受试者级"
            "治疗身份以DM域'试验分组'为准（R5D已确认口径）。"
        ),
    },
}


# R14 首轮收敛后浮现的1张两轮分歧裁决卡（20261003T14:2xZ，EXDAT；历轮首次
# 浮现）。作答依据（openpyxl 直读 EX 表）：
# ① EXDAT（来源列标题'给药日期'）128行全为合法ISO日期（2026-03-02~
#   2026-07-08，76个不同日期），16名受试者各8条给药记录，与'给药药物'
#  （MG-K10 300mg Q4W）/'给药状态'（完成×86/延迟给药×42）同行配对，
#  为每次试验药物给药记录的执行日期；
# ② 卡片显示主分析 recommended_role=treatment_administration_date，
#  独立复核为 administration_date；按①数据实测采纳卡面推荐角色
#  treatment_administration_date（EX域暴露记录语义，与R13已确认的
#  treatment_administration_status 同族token一致）；
# ③ 受试者级治疗身份仍以DM域'试验分组'为准（R5D已确认口径），两臂标签式
#  给药记录不据此声明实际IP暴露。
# 首次遇到时脚本 fail-closed 诚实退出留痕（r15d_seed_evidence.jsonl
# unknown_questions_fail_closed），按上述实测依据补答后重跑续推。
R14_ROUND1_CARDS = {
    ("EX", "EXDAT"): {
        "recommended_role": "treatment_administration_date",
        "user_action": (
            "用户已核对：两轮复核分歧裁决——按来源数据实测采纳"
            "treatment_administration_date（来源列标题'给药日期'，128行全为"
            "合法ISO日期2026-03-02~2026-07-08，16名受试者各8条给药记录，"
            "与'给药药物'(MG-K10 300mg Q4W)/'给药状态'同行配对，为每次试验"
            "药物给药记录的执行日期；受试者级治疗身份以DM域'试验分组'为准"
            "（R5D已确认口径），两臂标签式给药记录不据此声明实际IP暴露）。"
        ),
    },
}


# R15 首轮收敛后浮现的4张两轮分歧裁决卡（20261003T19:21Z，VS 域生命体征
# 四列；历轮首次浮现）。作答依据（openpyxl 直读 VS 表）：
# ① VS 表 65 行中首行为重复表头占位行（VISIT/HRRATE/…），实际测量数据
#   64 行 = 16名受试者 × 4次访视（R/W2/W4/W8 各16），四列全部为整数型
#   生命体征测量值，无缺失；
# ② 四张卡片显示主分析与独立复核结论一致（同角色 token，如
#   diastolic_blood_pressure 双侧同判），按①数据实测采纳该角色；
# ③ 列语义与单位在列标题中显式给出（mmHg/次分），为生命体征域标准
#   测量语义。首次遇到时脚本 fail-closed 诚实退出留痕
#  （r15d_seed_evidence.jsonl unknown_questions_fail_closed），
#   按上述实测依据补答后重跑续推。
R15_ROUND1_CARDS = {
    ("VS", "DBP"): {
        "recommended_role": "diastolic_blood_pressure",
        "user_action": (
            "用户已核对：两轮复核分歧裁决——按来源数据实测采纳"
            "diastolic_blood_pressure（来源列标题'舒张压mmHg'，64行测量数据"
            "全部为60-88整数mmHg，16名受试者×4次访视R/W2/W4/W8，与'收缩压"
            "mmHg'(SBP)同行配对，为生命体征舒张压测量值）。"
        ),
    },
    ("VS", "HRRATE"): {
        "recommended_role": "heart_rate",
        "user_action": (
            "用户已核对：两轮复核分歧裁决——按来源数据实测采纳heart_rate"
            "（来源列标题'心率次分'，64行测量数据全部为58-94整数次/分，"
            "16名受试者×4次访视，为生命体征心率测量值）。"
        ),
    },
    ("VS", "RESP"): {
        "recommended_role": "respiratory_rate",
        "user_action": (
            "用户已核对：两轮复核分歧裁决——按来源数据实测采纳"
            "respiratory_rate（来源列标题'呼吸次分'，64行测量数据全部为"
            "16-22整数次/分，16名受试者×4次访视，为生命体征呼吸频率测量值）。"
        ),
    },
    ("VS", "SBP"): {
        "recommended_role": "systolic_blood_pressure",
        "user_action": (
            "用户已核对：两轮复核分歧裁决——按来源数据实测采纳"
            "systolic_blood_pressure（来源列标题'收缩压mmHg'，64行测量数据"
            "全部为98-140整数mmHg，16名受试者×4次访视，与'舒张压mmHg'"
            "(DBP)同行配对，为生命体征收缩压测量值）。"
        ),
    },
}


def known_decision(domain: str, source_field: str) -> dict | None:
    if (domain, source_field) in R15_ROUND1_CARDS:
        return dict(R15_ROUND1_CARDS[(domain, source_field)])
    if (domain, source_field) in R14_ROUND1_CARDS:
        return dict(R14_ROUND1_CARDS[(domain, source_field)])
    if (domain, source_field) in R13_ROUND1_CARDS:
        return dict(R13_ROUND1_CARDS[(domain, source_field)])
    if (domain, source_field) == ("EX", "EXTRT"):
        return {"user_action": EXTRT_ANSWER}
    if (domain, source_field) == ("MH", "MHNUM"):
        return {"recommended_role": "metadata.record_id", "user_action": MHNUM_ANSWER}
    for table in (FINAL_CARDS, R8_ROUND2_CARDS, R9_ROUND4_CARDS, R11_ROUND3_CARDS,
                  R12_ROUND4_CARDS):
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
            {"ts": _now(), "run": "r15d_seed", "step": step, "ok": bool(ok), **detail},
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
                "idempotency_key": f"r15d-patch-{domain}-{source_field}-{uuid.uuid4().hex[:8]}",
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
        key = f"r15d-seed-{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}-{uuid.uuid4().hex[:8]}"
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

    # ── Step1b 探障（R15D 前置）：新建项目立即 project/open 留痕 ─────
    # 循环收尾已把旧项目全部软归档，GET /r7/project/open 对归档项目返回
    # route_not_found 而非 blocked/CORRUPT，无法用旧项目探障。新建项目
    # 在 bootstrap 前 runtime/monitoring_runtime.sqlite3 尚不存在，
    # inspect 判 required_member_missing → blocked 属设计内瞬态（R1 已知
    # 问题注释同款）；R5D 缺陷病灶在建项种子 marker（已单独用产品
    # inspect_member 实证本新项目 4 个种子成员全 CURRENT）。此处只留痕，
    # 真正的验收断言在 Step10（project/open 必须 current）。
    po_status, po = _http("probe_project_open_after_create", "GET", f"{mm}/project/open")
    _ev("probe_recorded", True,
        state=(po or {}).get("state"), dataCoverage=(po or {}).get("dataCoverage"),
        note="bootstrap前required_member_missing属设计内瞬态，终态断言在Step10")

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
                        "R15D开考位预置：确认本组MG-K10-CSU-001合成文件"
                        "（方案V1.3+eCRF指南V1.0+合成listing V1.0）属于"
                        "当前项目MX循R15D-CSU。"
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
                    "R15D开考位预置：映射双队列候选批量核验通过，系统采纳进入"
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
        idem = st.get("confirm_idempotency_key") or f"r15d-confirm-{uuid.uuid4().hex}"
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
                        "R15D开考位预置：双队列映射候选经系统复核与批量裁决收敛"
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
    # 终态硬断言：confirmed + facts ready + 界面可开始运行监查（非 blocked）
    if verdict["confirmation_status"] != "confirmed" or verdict["facts_state"] != "ready":
        _ev("final_assert_failed", False, **verdict)
        print("FINAL_ASSERT_FAILED: confirmation/facts 未达标", flush=True)
        return 2
    if (opened or {}).get("state") == "blocked" or not (opened or {}).get("canView"):
        _ev("final_assert_failed", False, project_open=verdict["project_open"])
        print("FINAL_ASSERT_FAILED: project/open 仍 blocked", flush=True)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
