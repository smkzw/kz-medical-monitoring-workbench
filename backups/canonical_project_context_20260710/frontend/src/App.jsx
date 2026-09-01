import { useEffect, useMemo, useRef, useState } from "react";
import { EditorContent, useEditor } from "@tiptap/react";
import StarterKit from "@tiptap/starter-kit";
import { Table } from "@tiptap/extension-table";
import { TableCell } from "@tiptap/extension-table-cell";
import { TableHeader } from "@tiptap/extension-table-header";
import { TableRow } from "@tiptap/extension-table-row";
import {
  AlertTriangle,
  ArrowDownUp,
  Bell,
  Bold,
  BookOpenText,
  CheckCircle2,
  ChevronRight,
  ClipboardCheck,
  Clock3,
  Database,
  FileCheck2,
  FileText,
  Filter,
  GitCompare,
  Heading1,
  History,
  Italic,
  LayoutDashboard,
  List,
  ListOrdered,
  ListChecks,
  MessageSquareText,
  PanelRightOpen,
  PencilLine,
  Search,
  ShieldAlert,
  Sparkles,
  Upload,
  UserRoundCheck,
  XCircle,
} from "lucide-react";
import logo from "./assets/header_logo.png";

const PROJECT_ID = import.meta.env.VITE_PROJECT_ID || "proj_mgk10_sar_demo";
const DEFAULT_SUBJECT_ID = import.meta.env.VITE_SUBJECT_ID || "";
const RAW_ELIGIBILITY_PROJECT_ID = import.meta.env.VITE_RAW_ELIGIBILITY_PROJECT_ID || "d001_raw_intake";
const RAW_MONITORING_PROJECT_ID = import.meta.env.VITE_RAW_MONITORING_PROJECT_ID || "proj_rux_03_002";
const RAW_TFL_PROJECT_ID = import.meta.env.VITE_RAW_TFL_PROJECT_ID || "proj_rux_03_002";
const RAW_SAFETY_PROJECT_ID = import.meta.env.VITE_RAW_SAFETY_PROJECT_ID || "my009_uc_monitoring_raw";

const navItems = [
  { key: "overview", label: "项目总看板", icon: LayoutDashboard },
  { key: "evidenceDesign", label: "证据调研与方案设计", icon: Search },
  { key: "eligibility", label: "入排审核", icon: UserRoundCheck },
  { key: "monitoring", label: "医学监查", icon: ShieldAlert },
  { key: "tfl", label: "数据分析与TFL", icon: Database },
  { key: "writing", label: "医学写作", icon: BookOpenText },
  { key: "safety", label: "安全信号与PV协同", icon: AlertTriangle },
  { key: "approvals", label: "审批中心", icon: ClipboardCheck },
];

const moduleLabels = {
  dashboard: "项目总看板",
  evidence_design: "证据调研与方案设计",
  eligibility_review: "入排审核",
  medical_monitoring: "医学监查",
  data_analysis_tfl: "数据分析与TFL",
  medical_writing: "医学写作",
  safety_pv: "安全信号与PV协同",
  approvals: "审批中心",
};

const moduleToPage = {
  dashboard: "overview",
  evidence_design: "evidenceDesign",
  eligibility_review: "eligibility",
  medical_monitoring: "monitoring",
  data_analysis_tfl: "tfl",
  medical_writing: "writing",
  safety_pv: "safety",
  approvals: "approvals",
};

const pageToModule = {
  overview: "dashboard",
  evidenceDesign: "evidence_design",
  eligibility: "eligibility_review",
  monitoring: "medical_monitoring",
  subjectTimeline: "medical_monitoring",
  patientProfile: "medical_monitoring",
  tfl: "data_analysis_tfl",
  writing: "medical_writing",
  safety: "safety_pv",
  approvals: "approvals",
};

const pageSourceProjectIds = {
  eligibility: RAW_ELIGIBILITY_PROJECT_ID,
  monitoring: RAW_MONITORING_PROJECT_ID,
  subjectTimeline: RAW_MONITORING_PROJECT_ID,
  patientProfile: RAW_MONITORING_PROJECT_ID,
  tfl: RAW_TFL_PROJECT_ID,
  safety: RAW_SAFETY_PROJECT_ID,
};

const fallbackDashboard = {
  project: {
    project_code: "MG-K10-SAR-DEMO",
    project_name: "MG-K10 SAR 医学经理工作台演示项目",
    indication: "季节性过敏性鼻炎",
    product_name: "MG-K10",
    study_phase: "III",
    protocol_version: "V2.1",
  },
  latest_batch: {
    batch_id: "batch_003",
    batch_label: "原始数据 listing Batch 003",
    extract_date: "2026-06-28",
    subject_count: 175,
    site_count: 25,
  },
  modules: [
    { module: "dashboard", label: "项目总看板", completion_rate: 0.35, open_risk_count: 0, pending_task_count: 4, pending_approval_count: 2 },
    { module: "evidence_design", label: "证据调研与方案设计", completion_rate: 0.12, open_risk_count: 0, pending_task_count: 6, pending_approval_count: 0 },
    { module: "eligibility_review", label: "入排审核", completion_rate: 0.58, open_risk_count: 1, pending_task_count: 12, pending_approval_count: 3 },
    { module: "medical_monitoring", label: "医学监查", completion_rate: 0.46, open_risk_count: 11, pending_task_count: 28, pending_approval_count: 2 },
    { module: "data_analysis_tfl", label: "数据分析与TFL", completion_rate: 0.1, open_risk_count: 0, pending_task_count: 5, pending_approval_count: 0 },
    { module: "medical_writing", label: "医学写作", completion_rate: 0.41, open_risk_count: 3, pending_task_count: 14, pending_approval_count: 7 },
    { module: "safety_pv", label: "安全信号与PV协同", completion_rate: 0.08, open_risk_count: 0, pending_task_count: 4, pending_approval_count: 0 },
    { module: "approvals", label: "审批中心", completion_rate: 0.3, open_risk_count: 0, pending_task_count: 0, pending_approval_count: 17 },
  ],
  risk_counts_by_severity: { critical: 1, high: 5, medium: 13, low: 19 },
  pending_approvals: [],
  recent_risks: [],
};

const heatmapTypes = [
  { key: "AE/MH漏报", note: "病历、病史或用药提示事件，但 AE/MH listing 未完整记录；不含单纯实验室数值异常。" },
  { key: "实验室异常未解释", note: "实验室结果异常、CTCAE 分级变化或危急值流程待核对，尚未形成明确医学解释。" },
  { key: "禁限用药/洗脱", note: "禁用药、限制用药、洗脱不足、救援用药或相关 PD 登记风险。" },
  { key: "疗效偏离", note: "疗效评分恶化、缺失、窗口偏离或受合并用药/依从性影响。" },
  { key: "数据质量/字段漂移", note: "字段新增、访视窗口、缺失数据、Query 或 source 追溯问题。" },
];

function apiErrorText(error) {
  return error?.message || error?.status || "network";
}

function apiDetailText(payload, fallback = "") {
  const detail = payload?.detail;
  if (typeof detail === "string") return detail;
  if (detail && typeof detail === "object") return detail.detail || detail.message || JSON.stringify(detail);
  return fallback;
}

function readJsonOrThrow(response) {
  if (response.ok) return response.json();
  return response
    .json()
    .catch(() => ({}))
    .then((payload) => {
      throw new Error(apiDetailText(payload, `${response.status}`));
    });
}

const riskRows = [
  { id: "risk_s6_cm_10008", title: "10008 随机前抗组胺药洗脱不足", subject: "10008", site: "10", type: "禁用药/洗脱违规", severity: "high", status: "需行动", batch: "003", owner: "医学经理", source: "KRI-07 / 规则", age: "3h" },
  { id: "risk_s6_ae_06021", title: "06021 眼部异常与 AE 记录不一致", subject: "06021", site: "06", type: "AE/MH漏报", severity: "medium", status: "复核中", batch: "003", owner: "医学经理", source: "医学规则", age: "1d" },
  { id: "risk_s6_lab_10021", title: "10021 ALT 升高 Grade 2 未见医学解释", subject: "10021", site: "18", type: "实验室异常未解释", severity: "medium", status: "待确认", batch: "003", owner: "医学经理", source: "QTL-05 / 实验室", age: "1d" },
  { id: "risk_s6_eff_10045", title: "10045 rTNSS 连续两访视恶化且用药增加", subject: "10045", site: "03", type: "疗效偏离", severity: "medium", status: "复核中", batch: "003", owner: "医学经理", source: "趋势规则", age: "2d" },
  { id: "risk_s6_visit_10031", title: "10031 W4 访视窗口偏离 5 天", subject: "10031", site: "12", type: "访视偏离", severity: "low", status: "已关闭", batch: "002", owner: "CRA", source: "数据质量", age: "5d" },
];

function monitoringRiskRowsFromInbox(workbenchInbox) {
  return (workbenchInbox?.items || [])
    .filter((item) => item.module === "medical_monitoring" && item.item_type === "risk")
    .map((item) => ({
      id: item.item_id,
      inboxItemId: item.item_id,
      title: item.title,
      subject: item.target_id || item.source_id || "-",
      site: item.target_id?.startsWith("S") ? item.target_id.slice(1, 3) : "-",
      type: item.source_type === "rux_monitoring_risk" ? "RUX医学监查规则" : item.source_type,
      severity: item.priority,
      status: item.status,
      batch: item.source_version?.split(":")?.[0] || "-",
      owner: item.owner_role || "医学经理",
      source: [
        item.source_refs?.some((ref) => ref.source_type === "protocol_rule") ? "方案条款定位" : "",
        item.source_refs?.some((ref) => ref.source_type === "listing_data_row") ? "原始数据 listing 行" : "",
      ].filter(Boolean).join(" / ") || item.source_id,
      age: item.unread ? "未读" : "已读",
      unread: item.unread,
      needsAction: item.needs_action,
      rationale: item.summary,
      recommendedAction: item.action_label || "进入医学复核",
      boundaryNote: item.boundary_note,
      sourceRefs: item.source_refs || [],
      sourceVersion: item.source_version,
      dispositionState: ruxDispositionStateFromStatus(item.status),
    }))
    .sort((left, right) => {
      const severityRank = { critical: 0, high: 1, medium: 2, low: 3 };
      return (severityRank[left.severity] ?? 9) - (severityRank[right.severity] ?? 9)
        || String(left.subject).localeCompare(String(right.subject), "zh-CN", { numeric: true })
        || String(left.id).localeCompare(String(right.id));
    });
}

function ruxDispositionStateFromStatus(status) {
  return {
    "待医学复核": "pending_review",
    "已医学复核": "reviewed",
    "Query草稿": "query_draft",
    "已提交审批": "submitted_for_approval",
    "已提交内部审批": "submitted_for_approval",
  }[status] || "pending_review";
}

function ruxDispositionStepTone(state, step) {
  const order = ["pending_review", "reviewed", "query_draft", "submitted_for_approval"];
  const stateIndex = order.indexOf(state);
  const stepIndex = order.indexOf(step);
  if (state === step) return "warning";
  if (stateIndex > stepIndex) return "success";
  return "neutral";
}

const demoListingSheets = [
  {
    sheet_name: "CM",
    rows: [
      { SUBJID: "10008", SITEID: "10", VISIT: "SCR", RANDDTC: "2026-07-06", CMTRT: "氯雷他定", CMSTDTC: "2026-06-30", CMENDTC: "2026-07-05", CMINDC: "鼻痒、喷嚏", CHANGE_FLAG: "new" },
      { SUBJID: "06021", SITEID: "06", VISIT: "W2", CMTRT: "人工泪液", CMSTDTC: "2026-07-18", CMENDTC: "", CMINDC: "眼痒", CHANGE_FLAG: "changed" },
    ],
  },
  {
    sheet_name: "MH",
    rows: [
      { SUBJID: "06021", SITEID: "06", VISIT: "SCR", MHTERM: "过敏性结膜炎史", MHSTDTC: "2024-05", CHANGE_FLAG: "new" },
    ],
  },
  {
    sheet_name: "AE",
    rows: [
      { SUBJID: "10008", SITEID: "10", VISIT: "W1", AETERM: "头痛", AESTDTC: "2026-07-13", AESEV: "轻度", AESER: "N", AESI_FLAG: "N", CHANGE_FLAG: "new" },
    ],
  },
  {
    sheet_name: "LB",
    rows: [
      { SUBJID: "10021", SITEID: "18", VISIT: "W2", LBTEST: "ALT", LBSTRESN: "165", LBSTRESU: "U/L", LBNRIND: "HIGH", LBTOXGR: "2", CHANGE_FLAG: "new" },
    ],
  },
  {
    sheet_name: "QS",
    rows: [
      { SUBJID: "10045", SITEID: "03", VISIT: "W4", QSTEST: "rTNSS", QSSTRESN: "8.1", QSDTC: "2026-07-27", CHANGE_FLAG: "changed" },
    ],
  },
];

const subjects = [
  {
    id: "10008",
    site: "10",
    status: "高风险复核",
    profile: "男 / 31岁 / 随机 D1 / ITT",
    efficacy: [
      { visit: "筛选", rTNSS: 8.6, iTNSS: 8.9, quality: 62 },
      { visit: "D1", rTNSS: 8.2, iTNSS: 8.5, quality: 64 },
      { visit: "W1", rTNSS: 6.9, iTNSS: 7.0, quality: 70 },
      { visit: "W2", rTNSS: 7.6, iTNSS: 7.4, quality: 66 },
      { visit: "W4", rTNSS: 7.8, iTNSS: 7.9, quality: 63 },
    ],
    timeline: [
      { day: "筛选-7", lane: "MH", label: "SAR 诊断史 5年", risk: "source" },
      { day: "筛选-3", lane: "CM", label: "氯雷他定开始", risk: "warning" },
      { day: "D1", lane: "访视", label: "随机", risk: "normal" },
      { day: "D2", lane: "CM", label: "氯雷他定结束", risk: "critical" },
      { day: "W1", lane: "疗效", label: "rTNSS 改善", risk: "good" },
      { day: "W2", lane: "疗效", label: "症状反弹", risk: "warning" },
      { day: "W4", lane: "PD", label: "潜在洗脱不足", risk: "critical" },
    ],
    risks: ["随机前4天内使用抗组胺药", "PD listing 未见对应记录", "W2 后疗效改善不稳定"],
    labs: [
      { name: "ALT", value: "28 U/L", trend: "稳定", flag: "normal" },
      { name: "EOS", value: "0.62 x10^9/L", trend: "升高", flag: "warning" },
      { name: "IgE", value: "198 IU/mL", trend: "基线高", flag: "info" },
    ],
    queries: ["CM 用药结束日期待中心确认", "是否构成方案偏离待医学确认"],
  },
  {
    id: "06021",
    site: "06",
    status: "中风险复核",
    profile: "女 / 42岁 / W4 / 安全集",
    efficacy: [
      { visit: "筛选", rTNSS: 7.9, iTNSS: 8.1, quality: 58 },
      { visit: "D1", rTNSS: 7.7, iTNSS: 8.0, quality: 59 },
      { visit: "W1", rTNSS: 6.3, iTNSS: 6.8, quality: 68 },
      { visit: "W2", rTNSS: 5.8, iTNSS: 6.1, quality: 72 },
      { visit: "W4", rTNSS: 5.5, iTNSS: 5.9, quality: 76 },
    ],
    timeline: [
      { day: "筛选", lane: "MH", label: "过敏性结膜炎史", risk: "source" },
      { day: "D1", lane: "访视", label: "随机", risk: "normal" },
      { day: "W1", lane: "AE", label: "眼痒记录于病历", risk: "warning" },
      { day: "W2", lane: "实验室", label: "EOS 下降", risk: "good" },
      { day: "W4", lane: "AE", label: "AE listing 未见眼部事件", risk: "warning" },
    ],
    risks: ["病历记录眼部症状但 AE listing 缺失", "同靶点 IB 眼部风险需医学复核"],
    labs: [
      { name: "ALT", value: "22 U/L", trend: "稳定", flag: "normal" },
      { name: "EOS", value: "0.31 x10^9/L", trend: "下降", flag: "normal" },
      { name: "结膜评分", value: "2", trend: "新增", flag: "warning" },
    ],
    queries: ["请中心确认眼部症状是否应作为 AE 记录"],
  },
];

const writingSections = [
  { id: "synopsis", title: "方案概要", status: "已批准", coverage: 100, revisions: 0 },
  { id: "background", title: "研究背景", status: "AI 草稿", coverage: 68, revisions: 2 },
  { id: "endpoints", title: "研究目的与终点", status: "医学审阅中", coverage: 35, revisions: 3 },
  { id: "population", title: "研究人群", status: "医学审阅中", coverage: 76, revisions: 1 },
  { id: "eligibility", title: "入选与排除标准", status: "AI 草稿", coverage: 72, revisions: 2 },
  { id: "soa", title: "研究流程与评估时间表", status: "医学审阅中", coverage: 58, revisions: 1 },
  { id: "safety", title: "安全性评估", status: "AI 草稿", coverage: 64, revisions: 1 },
  { id: "statistics", title: "统计学考虑", status: "未开始", coverage: 18, revisions: 0 },
];

const approvalItems = [
  { id: "apv-001", type: "医学写作", title: "研究目的与终点章节", state: "医学审阅中", ai: "AI 修订 3 条", risk: "证据不足", owner: "医学经理", blockers: ["证据索引覆盖不足", "开放 revision thread 2 条"] },
  { id: "apv-002", type: "医学监查", title: "Batch 003 风险冻结包", state: "待医学批准", ai: "规则运行", risk: "高风险 2 条未关闭", owner: "医学经理", blockers: ["高风险 2 条未关闭", "Query 1 条待中心答复"] },
  { id: "apv-003", type: "入排审核", title: "中心 31 入排审核报告", state: "退回补证", ai: "AI 结论覆盖 1 条", risk: "pass_verify 待溯源", owner: "中心/医学", blockers: ["历史诊断证据待补充"] },
  { id: "apv-004", type: "医学写作", title: "方案概要已批准版本", state: "待医学批准", ai: "无开放 AI 修订", risk: "无阻断项", owner: "医学总监", blockers: [] },
];

function severityLabel(severity) {
  return { critical: "紧急", high: "高", medium: "中", low: "低" }[severity] || severity;
}

function riskStatusLabel(status) {
  return {
    action_required: "需行动",
    in_review: "复核中",
    triaged: "已分诊",
    new: "新识别",
    accepted_no_action: "接受不处理",
    resolved: "已解决",
    closed: "已关闭",
  }[status] || status;
}

function statusClass(value) {
  if (["critical", "高风险复核", "需行动", "不通过"].includes(value)) return "danger";
  if (["failed"].includes(value)) return "danger";
  if (["high", "中风险复核", "复核中", "待确认", "待补证", "医学审阅中", "待医学批准", "溯源提醒", "blocked"].includes(value)) return "warning";
  if (["已关闭", "通过", "已批准", "可进入筛选", "completed"].includes(value)) return "success";
  return "info";
}

function verdictLabel(value) {
  return {
    pass: "通过",
    pass_verify: "通过（需溯源验证）",
    fail: "不通过",
    insufficient: "证据不足",
    investigator: "需研究者判定",
    needs_evidence: "需补充资料",
    not_reviewed: "未审核",
    parse_error: "解析失败",
    na: "不适用",
  }[value] || value || "未审核";
}

function verdictTone(value) {
  if (value === "fail" || value === "parse_error") return "danger";
  if (["insufficient", "investigator", "needs_evidence", "pass_verify"].includes(value)) return "warning";
  if (value === "pass") return "success";
  return "info";
}

function ruleTypeLabel(value) {
  return value === "exclusion" ? "排除标准" : "入选标准";
}

function candidateStatusLabel(value) {
  return {
    pending: "待处理",
    processing: "处理中",
    reviewed: "已审核",
    error: "异常",
    ready_for_review: "待审核",
    action_required: "需行动",
    awaiting_site_response: "待中心回复",
    ready_for_randomization: "可随机",
    screen_failed: "筛败",
  }[value] || value || "未记录";
}

function shortPath(value) {
  if (!value) return "";
  const parts = String(value).split("/");
  return parts.slice(-4).join("/");
}

function sourceTypeLabel(value) {
  return {
    XLSX: "XLSX",
    CSV: "CSV",
    DOCX: "DOCX",
    Directory: "目录",
  }[value] || value;
}

function parserStatusLabel(status) {
  return {
    parsed: "已解析",
    inventory_only: "仅登记清单",
    document_registered: "已登记文件",
    pending: "待解析",
    failed: "解析失败",
  }[status] || status;
}

function sourceKindLabel(kind) {
  return {
    listing_file: "列表数据",
    protocol_docx: "研究方案",
    raw_subject_bundle_inventory: "受试者资料清单",
    tfl_dataset_package_inventory: "TFL数据包清单",
    tfl_output_package_inventory: "TFL输出包清单",
    safety_signal_package_inventory: "安全资料包清单",
    pv_safety_package_inventory: "PV资料包清单",
    clinical_safety_summary_inventory: "安全总结清单",
  }[kind] || kind;
}

function aiTaskDisplayName(task) {
  return {
    disease_background_research: "适应症背景调研",
    competitive_intelligence: "竞品情报整理",
    protocol_design_synthesis: "方案设计建议综合分析",
    picos_design_coach: "PICOS问答式设计",
    tfl_generation_assist: "TFL清单与字段映射辅助",
    analysis_result_explanation: "分析结果医学解释",
    safety_case_medical_review: "安全个案医学复核建议",
    signal_narrative_synthesis: "安全信号叙述草案",
  }[task] || task;
}

function tflOutputTypeLabel(value) {
  return {
    table: "表",
    figure: "图",
    listing: "Listing",
    document: "文档",
  }[value] || value;
}

function tflReviewActionLabel(action) {
  return {
    mark_reviewed: "标记医学已审阅",
    request_statistical_review: "发起统计复核",
    create_writing_candidate: "标记写作引用候选",
    return_for_dataset_check: "退回数据集核对",
    reset_review: "重置状态",
  }[action] || action;
}

function safetyReviewActionLabel(action) {
  return {
    mark_medical_reviewed: "保存医学意见",
    request_pv_confirmation: "标记PV协同确认",
    return_for_source_check: "退回补充资料",
    accept_no_action: "关闭为暂无需处理",
    reset_review: "重置处置",
  }[action] || action;
}

function parserStatusDisplay(status) {
  return {
    parsed: "已读取",
    inventory_only: "仅登记清单",
    document_registered: "已登记文件",
    inventory_only_sas7bdat_requires_pyreadstat: "仅登记清单，需SAS解析器",
    parse_failed: "读取失败",
    pending: "待解析",
  }[status] || status || "未记录";
}

function formatMaybeNumber(value) {
  return value === null || value === undefined ? "未读取" : Number(value).toLocaleString("zh-CN");
}

function safetyGateTone(status) {
  return {
    ok: "success",
    warning: "warning",
    blocker: "danger",
    blocked: "danger",
  }[status] || "info";
}

function gateStatusLabel(status) {
  return {
    ok: "通过",
    warning: "需确认",
    blocker: "阻断",
    blocked: "阻断",
  }[status] || status || "未记录";
}

function picosStatusTone(status) {
  return {
    写作候选: "success",
    待医学确认: "warning",
    待补医学理由: "warning",
    退回补证: "danger",
    待用户确认: "info",
  }[status] || statusClass(status);
}

function picosActionLabel(action) {
  return {
    select_option: "选择候选",
    save_rationale: "保存理由",
    mark_writing_candidate: "标记写作候选",
    return_for_evidence: "退回补证",
    reset_decision: "重置",
  }[action] || action;
}

function riskToneFromEvent(event) {
  if (["protocol_deviation", "query"].includes(event.event_type)) return "critical";
  if (event.related_risk_ids?.length) return event.event_type === "lab" ? "warning" : "critical";
  if (event.event_type === "efficacy_score") return "good";
  if (event.event_type === "medical_history") return "source";
  return "normal";
}

function subjectStatusFromPrompts(prompts = []) {
  if (prompts.some((item) => ["critical", "high"].includes(item.severity))) return "高风险复核";
  if (prompts.some((item) => item.severity === "medium")) return "中风险复核";
  return "医学复核";
}

function buildSubjectView(profile, subjectId, risk, subjectCatalog = subjects) {
  const local = subjectCatalog.find((item) => item.id === subjectId);
  if (!profile) {
    return local || {
      id: subjectId,
      site: risk?.site || "-",
      status: "待载入",
      profile: "完整个例下钻资料待生成；当前仅显示风险登记入口。",
      rawProfile: null,
      efficacyMetrics: [],
      safetyMetrics: [],
      efficacy: [],
      timeline: [{ day: "-", lane: "数据", label: "暂无 Subject Timeline", risk: "warning" }],
      risks: risk ? [risk.title] : ["暂无风险提示"],
      labs: [],
      queries: [],
      prompts: [],
      reviewFocus: [],
    };
  }

  const primaryEfficacy = profile.efficacy_trends?.[0];
  const efficacy = primaryEfficacy?.points?.map((point) => ({
    visit: point.visit_code || point.visit_label,
    rTNSS: point.value,
    risk: point.risk_flag ? "warning" : "normal",
  })) || [];

  const timeline = (profile.timeline || []).map((event) => ({
    day: event.visit_code || `D${event.study_day}`,
    lane: laneForEvent(event),
    label: event.title,
    risk: riskToneFromEvent(event),
  }));

  const labs = (profile.safety_trends || []).map((metric) => {
    const latest = metric.points?.[metric.points.length - 1] || {};
    const abnormal = latest.risk_flag || (latest.normality && !["normal", "not_applicable"].includes(latest.normality));
    return {
      name: metric.metric_label,
      value: latest.value !== undefined ? `${latest.value}${metric.unit ? ` ${metric.unit}` : ""}` : "-",
      trend: abnormal ? "需复核" : "最新正常",
      flag: abnormal ? "warning" : "normal",
    };
  });

  return {
    id: profile.subject_id,
    site: profile.subject?.site_id || "-",
    status: subjectStatusFromPrompts(profile.risk_prompts),
    rawProfile: profile,
    efficacyMetrics: profile.efficacy_trends || [],
    safetyMetrics: profile.safety_trends || [],
    profile: [
      profile.subject?.treatment_arm,
      profile.subject?.latest_visit_label,
      profile.subject?.enrollment_status,
    ].filter(Boolean).join(" / "),
    efficacy,
    timeline,
    risks: (profile.risk_prompts || []).map((prompt) => prompt.title),
    labs,
    queries: (profile.risk_prompts || []).filter((prompt) => prompt.query_id).map((prompt) => `${prompt.query_id}：${prompt.recommended_action}`),
    prompts: profile.risk_prompts || [],
    reviewFocus: profile.review_focus || [],
  };
}

function parseCsvLine(line) {
  const cells = [];
  let current = "";
  let quoted = false;
  for (let index = 0; index < line.length; index += 1) {
    const char = line[index];
    const next = line[index + 1];
    if (char === '"' && quoted && next === '"') {
      current += '"';
      index += 1;
    } else if (char === '"') {
      quoted = !quoted;
    } else if (char === "," && !quoted) {
      cells.push(current.trim());
      current = "";
    } else {
      current += char;
    }
  }
  cells.push(current.trim());
  return cells;
}

function parseCsv(text) {
  const lines = text.split(/\r?\n/).map((line) => line.trim()).filter(Boolean);
  if (lines.length < 2) return [];
  const headers = parseCsvLine(lines[0]);
  return lines.slice(1).map((line) => {
    const cells = parseCsvLine(line);
    return headers.reduce((row, header, index) => ({ ...row, [header]: cells[index] || "" }), {});
  });
}

function sheetNameFromFileName(name) {
  const upper = name.toUpperCase();
  for (const domain of ["AE", "CM", "MH", "LB", "QS", "PD", "SV"]) {
    if (upper.includes(domain)) return domain;
  }
  return "LISTING";
}

function formatBatchDisplay(batch) {
  if (!batch) return "Batch 003";
  if (batch.batch_label) return batch.batch_label;
  if (batch.batch_id) return batch.batch_id.replace("batch_", "Batch ");
  return "Batch 003";
}

function sourceProjectIdForPage(activePage) {
  return pageSourceProjectIds[activePage] || PROJECT_ID;
}

function sourceContextForPage(activePage, sourceManifests) {
  const moduleKey = pageToModule[activePage] || "dashboard";
  const projectId = sourceProjectIdForPage(activePage);
  const manifest = sourceManifests?.[projectId] || sourceManifests?.[PROJECT_ID] || null;
  const binding = manifest?.route_bindings?.[moduleKey] || null;
  const header = manifest?.header_project || null;
  const label = binding?.label || moduleLabels[moduleKey] || "当前模块";
  const sourceCode = header?.project_code || projectId;
  const sourceMode = manifest?.source_mode || "unknown";
  const isCrossProject = Boolean(header?.project_id && header.project_id !== PROJECT_ID);
  return {
    moduleKey,
    label,
    projectId,
    manifest,
    binding,
    header,
    sourceCode,
    sourceMode,
    displayBatch: binding?.display_batch || null,
    isCrossProject,
  };
}

function AppShell({ activePage, setActivePage, dashboard, sourceManifests, workbenchInbox, children }) {
  const project = dashboard.project || fallbackDashboard.project;
  const latestBatch = dashboard.latest_batch || fallbackDashboard.latest_batch;
  const visibleActivePage = ["subjectTimeline", "patientProfile"].includes(activePage) ? "monitoring" : activePage;
  const sourceContext = sourceContextForPage(activePage, sourceManifests);
  const activeBatch = sourceContext.displayBatch?.batch_label ? sourceContext.displayBatch : latestBatch;
  const activeBatchDate = activeBatch?.extract_date || "";
  const workItems = workbenchInbox?.items || [];
  const pendingApprovalCount = workItems.filter((item) => item.item_type === "approval").length || dashboard.pending_approvals?.length || 0;
  const highRiskCount = workItems.filter((item) => item.item_type === "risk" && ["critical", "high"].includes(item.priority)).length;
  const needsActionCount = workItems.filter((item) => item.needs_action).length;
  return (
    <div className="app">
      <aside className="sidebar">
        <button className="brand" onClick={() => setActivePage("overview")} aria-label="返回项目总看板">
          <img src={logo} alt="康哲药业" />
        </button>
        <nav className="nav">
          {navItems.map((item) => {
            const Icon = item.icon;
            return (
              <button
                key={item.key}
                className={`nav-item ${visibleActivePage === item.key ? "active" : ""}`}
                onClick={() => setActivePage(item.key)}
              >
                <Icon size={18} />
                <span>{item.label}</span>
              </button>
            );
          })}
        </nav>
        <div className="sidebar-footer">
          <span>最后更新</span>
          <strong>09:00</strong>
        </div>
      </aside>
      <section className="workspace">
        <header className="topbar">
          <div className="project-meta">
            <div>
              <span className="meta-label">项目</span>
              <strong>{project.project_code}</strong>
            </div>
            <div>
              <span className="meta-label">适应症</span>
              <strong>{project.indication}</strong>
            </div>
            <div>
              <span className="meta-label">方案版本</span>
              <strong>{project.protocol_version}</strong>
            </div>
            <div>
              <span className="meta-label">数据批次</span>
              <strong>{formatBatchDisplay(activeBatch)}</strong>
              {activeBatchDate ? <small>{activeBatchDate}</small> : null}
            </div>
            <div className={sourceContext.isCrossProject ? "cross-source-context" : ""}>
              <span className="meta-label">当前来源</span>
              <strong>{sourceContext.label}</strong>
              <small>{sourceContext.sourceCode}{sourceContext.isCrossProject ? " · 跨项目源" : ""}</small>
            </div>
          </div>
          <div className="top-actions">
            <Metric icon={Bell} label="未读" value={workbenchInbox?.unread_count ?? 0} tone="danger" />
            <Metric icon={Clock3} label="待我处理" value={needsActionCount} tone="warning" />
            <Metric icon={AlertTriangle} label="高风险开放" value={highRiskCount} tone="danger" />
            <Metric icon={Sparkles} label="跨模块交接" value={workbenchInbox?.handoff_count ?? 0} tone="info" />
            <Metric icon={FileCheck2} label="待审批" value={pendingApprovalCount} tone="success" />
            <button className="icon-button" title="通知">
              <Bell size={18} />
            </button>
          </div>
        </header>
        {children}
      </section>
    </div>
  );
}

function Metric({ icon: Icon, label, value, tone }) {
  return (
    <div className={`metric ${tone}`}>
      <Icon size={17} />
      <span>{label}</span>
      <strong>{value}</strong>
    </div>
  );
}

function SectionTitle({ eyebrow, title, action }) {
  return (
    <div className="section-title">
      <div>
        {eyebrow && <span>{eyebrow}</span>}
        <h2>{title}</h2>
      </div>
      {action}
    </div>
  );
}

function Tag({ children, tone = "neutral" }) {
  return <span className={`tag ${tone}`}>{children}</span>;
}

function Progress({ value }) {
  return (
    <div className="progress">
      <span style={{ width: `${Math.round(value * 100)}%` }} />
      <em>{Math.round(value * 100)}%</em>
    </div>
  );
}

function priorityTone(priority) {
  if (priority === "critical" || priority === "high") return "danger";
  if (priority === "medium") return "warning";
  if (priority === "low") return "info";
  return "neutral";
}

function itemTypeLabel(type) {
  return {
    risk: "风险",
    approval: "审批",
    handoff: "交接",
    ai_review: "AI",
    picos_decision: "PICOS",
    quality_gate: "质量门",
    source_ready: "来源登记",
    data_health: "数据健康",
    eligibility_action: "入排待办",
  }[type] || type;
}

function compactLabel(value, maxLength = 42) {
  if (!value) return "";
  const text = String(value);
  return text.length > maxLength ? `${text.slice(0, maxLength - 1)}…` : text;
}

function safeSourceRefLabel(value, maxLength = 58) {
  if (!value) return "";
  const text = String(value)
    .replace(/\/Users\/[^\s；，,]+/gi, "本地来源已隐藏")
    .replace(/file:\/\/[^\s；，,]+/gi, "本地来源已隐藏")
    .replace(/\b(root_path|file_path|absolute_path|allowed_roots|content_hash|preview_hash|storage_key|server_path|source_record_id)\b/gi, "来源字段已隐藏");
  return compactLabel(text, maxLength);
}

function workItemObjectLabel(item) {
  return compactLabel(item.source_refs?.[0]?.label || item.target_id || item.source_id || item.item_id);
}

function sourceRefTypeLabel(type) {
  return {
    protocol_rule: "方案条款定位",
    listing_data_row: "原始数据 listing 行",
    evidence_span: "证据片段",
    rule: "规则ID",
  }[type] || type;
}

function OverviewPage({ dashboard, workbenchInbox, setActivePage, setSelectedSubject, aiGatewayStatus, aiRuns, refreshWorkbenchInbox }) {
  const modules = dashboard.modules?.length ? dashboard.modules : fallbackDashboard.modules;
  const workItems = workbenchInbox?.items || [];
  const allNeedsActionItems = workItems.filter((item) => item.needs_action);
  const needsActionItems = allNeedsActionItems.slice(0, 8);
  const handoffItems = workItems.filter((item) => item.item_type === "handoff").slice(0, 5);
  const sourceHealthItems = workItems.filter((item) => ["source_ready", "data_health"].includes(item.item_type)).slice(0, 4);
  const openItem = async (item) => {
    if (item.unread) {
      try {
        const response = await fetch(`/api/projects/${PROJECT_ID}/workbench-inbox/${encodeURIComponent(item.item_id)}/actions`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ action: "mark_read", actor: "medical_manager", comment: "opened_from_overview" }),
        });
        if (response.ok) {
          const data = await response.json();
          refreshWorkbenchInbox?.(data);
        }
      } catch {
        refreshWorkbenchInbox?.();
      }
    }
    if (item.module === "medical_monitoring" && item.target_id) {
      setSelectedSubject?.(item.target_id);
    }
    setActivePage(item.target_page || moduleToPage[item.module] || "overview");
  };
  return (
    <main className="page">
      <SectionTitle
        eyebrow="项目全览"
        title={`统一工作收件箱（未读 ${workbenchInbox?.unread_count ?? 0} / 待我 ${allNeedsActionItems.length} / 交接 ${workbenchInbox?.handoff_count ?? 0}）`}
        action={<button className="primary-button" onClick={() => setActivePage(workItems[0]?.target_page || "monitoring")}>处理最高优先级</button>}
      />
      <section className="triage-panel workbench-inbox-panel">
        <div className="table-header inbox-cols">
          <span>优先级</span>
          <span>来源模块</span>
          <span>事项</span>
          <span>对象</span>
          <span>下一步</span>
          <span>状态</span>
        </div>
        {workItems.slice(0, 10).map((item) => (
          <button
            className={`table-row inbox-cols clickable ${item.unread ? "unread-row" : "read-row"}`}
            key={item.item_id}
            onClick={() => openItem(item)}
            title={item.boundary_note}
          >
            <span><Tag tone={priorityTone(item.priority)}>{severityLabel(item.priority)}</Tag></span>
            <span>{item.module_label}</span>
            <strong>
              {item.unread && <em className="unread-dot" aria-label="未读" />}
              {item.title}
              <small>{item.summary}</small>
            </strong>
            <span title={item.source_refs?.[0]?.label || item.target_id || item.source_id}>{workItemObjectLabel(item)}</span>
            <span>{item.action_label}</span>
            <span><Tag tone={item.needs_action ? "warning" : "info"}>{item.status || itemTypeLabel(item.item_type)}</Tag></span>
          </button>
        ))}
        {!workItems.length && (
          <div className="empty-unread">
            当前无开放工作项。已读内容仍保留在审计和模块记录中，不因重新进入项目自动消失。
          </div>
        )}
        <p className="inbox-boundary-note">收件箱聚合风险、审批、AI审计、PICOS决策、来源登记、数据健康、入排待办、TFL引用候选和安全/PV交接候选；所有AI和交接内容均需医学经理确认，不自动形成正式批准结论。</p>
      </section>
      <div className="overview-grid">
        <section className="panel">
          <SectionTitle title="模块状态矩阵" />
          <div className="module-list">
            {modules.map((module) => (
              <button className="module-row" key={module.module} onClick={() => setActivePage(moduleToPage[module.module] || "overview")}>
                <div>
                  <strong>{moduleLabels[module.module] || module.label}</strong>
                  <span>
                    未读 {workbenchInbox?.module_summaries?.find((item) => item.module === module.module)?.unread_count ?? 0}
                    {" · "}待我 {workbenchInbox?.module_summaries?.find((item) => item.module === module.module)?.needs_action_count ?? module.pending_task_count}
                    {" · "}交接 {workbenchInbox?.module_summaries?.find((item) => item.module === module.module)?.handoff_count ?? 0}
                  </span>
                </div>
                <Progress value={module.completion_rate} />
                <ChevronRight size={16} />
              </button>
            ))}
          </div>
        </section>
        <section className="panel">
          <SectionTitle title="风险热力图" />
          <div className="heatmap">
            {["中心 03", "中心 06", "中心 10", "中心 18", "全研究"].map((site, siteIndex) => (
              <div className="heat-row" key={site}>
                <span>{site}</span>
                {heatmapTypes.map((type, typeIndex) => (
                  <button key={type.key} className={`heat-cell level-${(siteIndex + typeIndex) % 4}`} title={type.note} onClick={() => setActivePage("monitoring")}>
                    <b>{type.key}</b>
                    <em>{(siteIndex + typeIndex + 1) % 7}</em>
                  </button>
                ))}
              </div>
            ))}
          </div>
          <div className="heatmap-note">
            {heatmapTypes.map((type) => <p key={type.key}><strong>{type.key}</strong>：{type.note}</p>)}
          </div>
        </section>
        <section className="panel">
          <SectionTitle title="独立 AI 状态" />
          <AiGatewayPanel status={aiGatewayStatus} runs={aiRuns} />
          <SectionTitle title="来源与数据健康" />
          <SourceHealthList items={sourceHealthItems} onOpen={openItem} />
          <SectionTitle title="跨模块交接台账" />
          <HandoffList items={handoffItems} onOpen={openItem} />
          <SectionTitle title="我的任务队列" />
          <TaskList items={needsActionItems} onOpen={openItem} />
        </section>
      </div>
    </main>
  );
}

function AiGatewayPanel({ status, runs = [] }) {
  const configured = Boolean(status?.configured);
  const recentRuns = runs.slice(-3).reverse();
  return (
    <div className="ai-gateway-card">
      <div className="ai-gateway-header">
        <Tag tone={configured ? "success" : "warning"}>{configured ? "已接入" : "未配置"}</Tag>
        <span>{status?.provider || "openai_compatible"} · {status?.model || "not_configured"}</span>
      </div>
      <div className="ai-gateway-grid">
        <div>
          <strong>{status?.semantic_ai_tasks_enabled ? "可运行" : "不可运行"}</strong>
          <span>语义 AI 任务</span>
        </div>
        <div>
          <strong>{status?.codex_runtime_dependency ? "存在" : "不存在"}</strong>
          <span>Codex 运行依赖</span>
        </div>
      </div>
      {status?.missing_env?.length > 0 && (
        <p className="ai-gateway-warning">缺少 {status.missing_env.join(" / ")}，方案解构、listing 语义映射、风险解释和医学写作不会自动调用 AI。</p>
      )}
      <div className="ai-run-list">
        {recentRuns.length ? recentRuns.map((run) => (
          <div key={run.run_id}>
            <Tag tone={statusClass(run.status)}>{run.status}</Tag>
            <strong>{moduleLabels[run.module] || run.module}</strong>
            <span>{run.task_type}</span>
          </div>
        )) : <p className="quiet-text">暂无 AI run 审计记录。</p>}
      </div>
    </div>
  );
}

function SourceHealthList({ items, onOpen }) {
  if (!items.length) {
    return <p className="quiet-text">暂无来源或数据健康告警。</p>;
  }
  return (
    <div className="source-health-list">
      {items.map((item) => (
        <button className="source-health-row" key={item.item_id} onClick={() => onOpen(item)} title={item.boundary_note}>
          <span><Tag tone={item.item_type === "data_health" ? "warning" : "info"}>{item.status}</Tag></span>
          <strong>{item.title}</strong>
          <small>{item.module_label} · {item.action_label}</small>
        </button>
      ))}
    </div>
  );
}

function HandoffList({ items, onOpen }) {
  if (!items.length) {
    return <p className="quiet-text">暂无跨模块交接候选。TFL写作引用候选、安全/PV确认候选和PICOS写作候选会在这里汇总。</p>;
  }
  return (
    <div className="handoff-list">
      {items.map((item) => (
        <button className="handoff-row" key={item.item_id} onClick={() => onOpen(item)} title={item.boundary_note}>
          <span><Tag tone={priorityTone(item.priority)}>{item.module_label}</Tag></span>
          <strong>{item.title}</strong>
          <small>{item.summary}</small>
        </button>
      ))}
    </div>
  );
}

function TaskList({ items, onOpen }) {
  if (!items.length) {
    return <p className="quiet-text">当前无待我处理项。</p>;
  }
  return (
    <div className="task-list">
      {items.map((item) => (
        <button className="task-row" key={item.item_id} onClick={() => onOpen(item)}>
          <span><Tag tone={priorityTone(item.priority)}>{severityLabel(item.priority)}</Tag></span>
          <strong>{item.title}</strong>
          <span>{item.module_label}</span>
          <span>{item.status}</span>
        </button>
      ))}
    </div>
  );
}

function MonitoringPage({ monitoringProjectId, sourceManifest, selectedSubject, setSelectedSubject, subjectProfile, setActivePage, refreshDashboard, workbenchInbox, refreshWorkbenchInbox }) {
  const [selectedRiskId, setSelectedRiskId] = useState("");
  const [uploadGateOpen, setUploadGateOpen] = useState(false);
  const [mappingReady, setMappingReady] = useState(false);
  const [intakeResult, setIntakeResult] = useState(null);
  const [intakeLoading, setIntakeLoading] = useState(false);
  const [intakeError, setIntakeError] = useState("");
  const [listingSheets, setListingSheets] = useState([]);
  const [listingFile, setListingFile] = useState(null);
  const [uploadedFileName, setUploadedFileName] = useState("");
  const [riskActionLoading, setRiskActionLoading] = useState(false);
  const [riskActionMessage, setRiskActionMessage] = useState("");
  const [rawMonitoring, setRawMonitoring] = useState(null);
  const [rawMonitoringLoading, setRawMonitoringLoading] = useState(false);
  const [rawMonitoringError, setRawMonitoringError] = useState("");
  const severityRank = { critical: 0, high: 1, medium: 2, low: 3 };
  const realInboxRiskRows = useMemo(() => monitoringRiskRowsFromInbox(workbenchInbox), [workbenchInbox]);
  const generatedRiskRows = (intakeResult?.generated_risks || [])
    .map((risk) => ({
      id: risk.risk_id,
      title: risk.title,
      subject: risk.subject_id || "-",
      site: risk.site_id || "-",
      type: risk.risk_type,
      severity: risk.severity,
      status: riskStatusLabel(risk.status),
      batch: risk.source_batch_id?.replace("batch_", "") || "-",
      owner: "医学经理",
      source: risk.rule_id,
      age: "刚刚",
      rationale: risk.rationale,
      recommendedAction: risk.recommended_action,
    }))
    .sort((left, right) => (severityRank[left.severity] ?? 9) - (severityRank[right.severity] ?? 9));
  const visibleRiskRows = generatedRiskRows.length
    ? generatedRiskRows
    : realInboxRiskRows.length
      ? realInboxRiskRows
      : riskRows;
  const usingRealInboxRisks = !generatedRiskRows.length && realInboxRiskRows.length > 0;
  const monitoringSourceHeader = sourceManifest?.header_project;
  const monitoringSourceLabel = monitoringSourceHeader
    ? `${monitoringSourceHeader.project_code} ${monitoringSourceHeader.indication}`
    : monitoringProjectId;
  const selectedRisk = visibleRiskRows.find((risk) => risk.id === selectedRiskId)
    || visibleRiskRows.find((risk) => risk.subject === selectedSubject)
    || visibleRiskRows[0]
    || riskRows[0];
  const subject = buildSubjectView(subjectProfile, selectedSubject, selectedRisk);
  const openRiskCount = visibleRiskRows.filter((risk) => risk.status !== "已关闭").length;
  const loadedRows = listingSheets.reduce((sum, sheet) => sum + sheet.rows.length, 0);
  const mappingRows = intakeResult?.field_mappings?.length ? intakeResult.field_mappings.slice(0, 7) : [
    { source_field: "SUBJID", standard_field: "subject_id", status: "auto_mapped" },
    { source_field: "CMTRT / CMENDTC", standard_field: "conmed_name / conmed_end_date", status: "auto_mapped" },
    { source_field: "AESI_FLAG", standard_field: "safety_interest_flag", status: mappingReady ? "confirmed" : "requires_confirmation" },
    { source_field: "QSDTC", standard_field: "assessment_date", status: "auto_mapped" },
  ];
  useEffect(() => {
    if (selectedRisk?.id && selectedRisk.id !== selectedRiskId) {
      setSelectedRiskId(selectedRisk.id);
    }
  }, [selectedRisk?.id, selectedRiskId]);
  useEffect(() => {
    let cancelled = false;
    setRawMonitoringLoading(true);
    setRawMonitoringError("");
    fetch(`/api/projects/${monitoringProjectId}/monitoring/raw-intake`)
      .then((response) => (response.ok ? response.json() : Promise.reject(response)))
      .then((data) => {
        if (!cancelled) setRawMonitoring(data);
      })
      .catch((response) => {
        if (!cancelled) setRawMonitoringError(`原始监查资料读取失败：${response.status || "network"}`);
      })
      .finally(() => {
        if (!cancelled) setRawMonitoringLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [monitoringProjectId]);
  const runMonitoringRules = async () => {
    setIntakeLoading(true);
    setIntakeError("");
    try {
      const query = new URLSearchParams({
        batch_label: "原始数据 listing Batch 004",
        extract_date: "2026-07-07",
        previous_batch_id: "batch_003",
        uploaded_by: "medical_manager",
      });
      let response;
      if (listingFile && !listingSheets.length) {
        query.set("filename", listingFile.name);
        query.set("confirm_aesi_flag", mappingReady ? "true" : "false");
        response = await fetch(`/api/projects/${monitoringProjectId}/monitoring/intake/file?${query.toString()}`, {
          method: "POST",
          headers: { "Content-Type": "application/octet-stream" },
          body: listingFile,
        });
      } else {
        response = await fetch(`/api/projects/${monitoringProjectId}/monitoring/intake`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            batch_label: "原始数据 listing Batch 004",
            extract_date: "2026-07-07",
            previous_batch_id: "batch_003",
            uploaded_by: "medical_manager",
            mapping_confirmations: mappingReady ? { AESI_FLAG: "safety_interest_flag" } : {},
            sheets: listingSheets.length ? listingSheets : demoListingSheets,
          }),
        });
      }
      if (!response.ok) throw new Error(`API ${response.status}`);
      const payload = await response.json();
      setIntakeResult(payload);
      refreshDashboard?.();
      if (payload.generated_risks?.length) {
        const sortedRisks = [...payload.generated_risks].sort(
          (left, right) => (severityRank[left.severity] ?? 9) - (severityRank[right.severity] ?? 9)
        );
        const first = sortedRisks[0];
        setSelectedRiskId(first.risk_id);
        if (first.subject_id) setSelectedSubject(first.subject_id);
      }
    } catch (error) {
      setIntakeError(`规则运行失败：${error.message}`);
    } finally {
      setIntakeLoading(false);
    }
  };
  const handleListingFile = async (event) => {
    const file = event.target.files?.[0];
    if (!file) return;
    setUploadedFileName(file.name);
    setListingFile(file);
    setIntakeResult(null);
    setIntakeError("");
    if (!file.name.toLowerCase().endsWith(".csv")) {
      setListingSheets([]);
      return;
    }
    const text = await file.text();
    const rows = parseCsv(text);
    setListingSheets([{ sheet_name: sheetNameFromFileName(file.name), rows }]);
    setListingFile(null);
  };
  const markRiskRead = async (risk) => {
    if (!risk?.inboxItemId) {
      setRiskActionMessage("当前风险来自本次上传规则结果，进入收件箱后才能写入已读审计。");
      return;
    }
    setRiskActionLoading(true);
    setRiskActionMessage("");
    try {
      const response = await fetch(`/api/projects/${monitoringProjectId}/workbench-inbox/${encodeURIComponent(risk.inboxItemId)}/actions`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ action: "mark_read", actor: "medical_manager", comment: "opened_from_monitoring_detail" }),
      });
      const payload = await response.json();
      if (!response.ok) throw new Error(payload.detail || `API ${response.status}`);
      refreshWorkbenchInbox?.(payload);
      setRiskActionMessage("已标记已读并写入收件箱审计。");
    } catch (error) {
      setRiskActionMessage(`已读动作失败：${error.message}`);
    } finally {
      setRiskActionLoading(false);
    }
  };
  const applyRiskDisposition = async (risk, action, payload = {}) => {
    if (!risk?.inboxItemId) {
      setRiskActionMessage("当前风险来自本次上传规则结果，进入收件箱后才能写入医学处置审计。");
      return;
    }
    setRiskActionLoading(true);
    setRiskActionMessage("");
    try {
      const response = await fetch(`/api/projects/${monitoringProjectId}/workbench-inbox/${encodeURIComponent(risk.inboxItemId)}/rux-risk-disposition`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          action,
          actor: "medical_manager",
          comment: payload.comment || "",
          query_draft_text: payload.query_draft_text || "",
          expected_source_version: payload.expected_source_version || risk.sourceVersion,
        }),
      });
      const result = await response.json();
      if (!response.ok) throw new Error(result.detail || `API ${response.status}`);
      refreshWorkbenchInbox?.(result);
      if (action === "submitted_for_approval") refreshDashboard?.();
      setRiskActionMessage({
        reviewed: "已记录医学复核，风险仍保留在医学监查闭环中。",
        query_draft: "已记录Query草稿，尚未执行对外动作或归档动作。",
        submitted_for_approval: "已提交内部审批，仍待医学批准后才能外发或归档。",
      }[action] || "医学处置已写入审计。");
    } catch (error) {
      setRiskActionMessage(`医学处置失败：${error.message}`);
    } finally {
      setRiskActionLoading(false);
    }
  };
  return (
    <main className="page monitoring-page">
      <SectionTitle
        eyebrow="医学监查"
        title="原始数据批次驱动的风险复核"
        action={<button className="primary-button" onClick={() => setUploadGateOpen((open) => !open)}><Upload size={16} /> 上传新批次</button>}
      />
      <section className="monitoring-toolbar">
        <div className="batch-box">
          <Database size={18} />
          <div>
            <strong>{usingRealInboxRisks ? `${monitoringSourceLabel} 原始数据 listing` : "Batch 003 vs Batch 002"}</strong>
            <span>
              {usingRealInboxRisks
                ? `真实监查风险锚点 ${realInboxRiskRows.length} 条 · 来源于 ${monitoringSourceLabel} listing 与方案条款`
                : "新增 36 行 · 升级 12 条 · 可能解决 20 条 · 字段漂移 6 项"}
            </span>
          </div>
        </div>
        <div className="mapping-alert">
          <AlertTriangle size={17} />
          {usingRealInboxRisks
            ? `当前${monitoringSourceLabel} P0仅展示已验证医学监查风险锚点，不代表全量医学监查完成。`
            : "AESI_FLAG 为新增字段，需确认是否映射到安全性关注事件。"}
        </div>
        <div className="filter-strip">
          {["中心", "受试者", "风险类型", "严重程度", "状态", "KRI/QTL"].map((label) => (
            <button key={label}><Filter size={14} /> {label}</button>
          ))}
        </div>
      </section>
      <section className="monitoring-raw-intake panel">
        <div className="raw-intake-head">
          <div>
            <span>原始监查资料链路</span>
            <strong>{rawMonitoring?.project_label || `${monitoringSourceLabel} 原始 listing + 方案`}</strong>
          </div>
          <Tag tone={rawMonitoringLoading ? "warning" : rawMonitoring?.ai_gateway_status?.configured ? "success" : "warning"}>
            {rawMonitoringLoading ? "读取中" : rawMonitoring?.ai_gateway_status?.configured ? "外部AI已配置" : "外部AI待配置"}
          </Tag>
        </div>
        <div className="monitoring-raw-grid">
          <div>
            <strong>{rawMonitoring?.listing?.sheet_count ?? "-"} sheets</strong>
            <span>{rawMonitoring?.listing?.row_count ?? "-"} 行 listing</span>
          </div>
          <div>
            <strong>{rawMonitoring?.listing?.subject_count ?? "-"} 名</strong>
            <span>受试者；字段 {rawMonitoring?.listing?.subject_id_fields?.join(" / ") || "-"}</span>
          </div>
          <div>
            <strong>{rawMonitoring?.protocol?.span_count ?? "-"} 段</strong>
            <span>方案文本结构，待抽取医学监查规则</span>
          </div>
          <div>
            <strong>{rawMonitoring?.domain_groups?.study_drug_change?.sheet_names?.length ?? "-"} 个</strong>
            <span>试验药物变更 sheet，与 CM 分离</span>
          </div>
        </div>
        <p>
          {rawMonitoringError || `CM/CM1 仅作为非试验用药；试验药物暂停、重启、剂量调整走独立 domain。当前展示 raw-source 发现与任务计划，全量 AE/MH漏报、禁用药违背和个例趋势仍需外部 AI/OCR/VLM 与医学确认。`}
        </p>
      </section>
      {uploadGateOpen && (
        <section className="panel upload-gate">
          <SectionTitle eyebrow="数据接入门禁" title="上传、映射、差异分析、规则运行" />
          <div className="gate-steps">
            {["上传 listing", "字段识别", "映射确认", "运行规则"].map((step, index) => (
              <div className={(index === 0 && (loadedRows > 0 || listingFile || !uploadedFileName)) || (index === 1 && mappingRows.length) || (index === 2 && mappingReady) || (index === 3 && intakeResult) ? "done" : ""} key={step}>
                <CheckCircle2 size={16} />
                <span>{step}</span>
              </div>
            ))}
          </div>
          <div className="upload-grid">
            <label className="drop-zone">
              <Upload size={22} />
              <strong>原始数据 listing Batch 004</strong>
              <span>{uploadedFileName || "未选择文件时使用内置 Batch 004 demo listing；CSV 前端解析，XLS/XLSX/XLSM 后端解析"}</span>
              <input type="file" accept=".xls,.xlsx,.xlsm,.csv" onChange={handleListingFile} />
            </label>
            <div className="mapping-table">
              <div><strong>原始字段</strong><strong>标准字段</strong><strong>状态</strong></div>
              {mappingRows.map((item) => (
                <div key={`${item.source_field}-${item.standard_field}`}>
                  <span>{item.source_field}</span>
                  <span>{item.standard_field}</span>
                  <Tag tone={item.status === "confirmed" || item.status === "auto_mapped" ? "success" : item.status === "requires_confirmation" ? "warning" : "info"}>
                    {item.status === "confirmed" ? "已确认" : item.status === "auto_mapped" ? "已识别" : item.status === "requires_confirmation" ? "待确认" : "未映射"}
                  </Tag>
                </div>
              ))}
            </div>
            <div className="diff-summary">
              <strong>{intakeResult ? `${intakeResult.batch.batch_id.replace("batch_", "Batch ")} vs ${intakeResult.diff_summary.previous_batch_id?.replace("batch_", "Batch ")}` : "Batch 004 vs Batch 003"}</strong>
              {intakeResult ? (
                <p>
                  新增行 {intakeResult.diff_summary.added_row_count}，改值行 {intakeResult.diff_summary.changed_row_count}，
                  受试者 {intakeResult.diff_summary.subject_count} 例，中心 {intakeResult.diff_summary.site_count} 个；
                  规则生成风险 {intakeResult.rule_run.generated_risk_count} 条。
                </p>
              ) : (
                <p>待运行 API：将返回字段映射、批次差异、规则结果和审计预览。</p>
              )}
              <div className="button-row">
                <button onClick={() => setMappingReady(true)}>确认 AESI_FLAG 映射</button>
                <button className="primary-button" disabled={!mappingReady || intakeLoading} onClick={runMonitoringRules}>
                  {intakeLoading ? "规则运行中" : "运行医学规则"}
                </button>
              </div>
              {loadedRows > 0 && <p className="upload-status">已解析 {loadedRows} 行 CSV listing。</p>}
              {listingFile && !loadedRows && <p className="upload-status">已选择原始 listing 文件，点击运行后由后端解析。</p>}
              {!loadedRows && !uploadedFileName && <p className="upload-status">当前将使用内置 Batch 004 demo listing 运行。</p>}
              {intakeError && <p className="gate-error">{intakeError}</p>}
              {intakeResult && intakeResult.rule_run.messages.map((message) => <p className="gate-result" key={message}>{message}</p>)}
            </div>
          </div>
        </section>
      )}
      <div className="monitoring-layout">
        <section className="panel ledger-panel">
          <div className="risk-ledger-head">
            <div>
              <strong>风险列表</strong>
              <span>按严重度、中心和风险类型筛选；点击后进入右侧风险详情。</span>
            </div>
            <Tag tone="warning">未关闭 {openRiskCount}</Tag>
          </div>
          {visibleRiskRows.map((risk) => (
            <button
              key={risk.id}
              className={`risk-card-row ${selectedRisk.id === risk.id ? "selected" : ""}`}
              onClick={() => {
                setSelectedRiskId(risk.id);
                setRiskActionMessage("");
                setSelectedSubject(risk.subject);
              }}
            >
              <div className="risk-card-title">
                <strong>{risk.title}</strong>
                <Tag tone={statusClass(risk.severity)}>{severityLabel(risk.severity)}</Tag>
              </div>
              <div className="risk-card-meta">
                {risk.unread && <span className="risk-unread">未读</span>}
                <span>受试者 {risk.subject}</span>
                <span>中心 {risk.site}</span>
                <span>{risk.type}</span>
                <span>{risk.status}</span>
              </div>
              <div className="risk-card-source">{risk.source} · Batch {risk.batch} · {risk.age}</div>
            </button>
          ))}
        </section>
        <RiskDetail
          risk={selectedRisk}
          subject={subject}
          setActivePage={setActivePage}
          onMarkRead={() => markRiskRead(selectedRisk)}
          onApplyDisposition={applyRiskDisposition}
          actionLoading={riskActionLoading}
          actionMessage={riskActionMessage}
        />
      </div>
    </main>
  );
}

function RiskDetail({ risk, subject, setActivePage, onMarkRead, onApplyDisposition, actionLoading, actionMessage }) {
  const dispositionState = risk.dispositionState || ruxDispositionStateFromStatus(risk.status);
  const [dispositionComment, setDispositionComment] = useState("已核对原始listing、方案条款和个例时间线，需进入医学处置闭环。");
  const [queryDraftText, setQueryDraftText] = useState(`请中心确认${risk.subject}该风险相关原始记录、AE/PD/试验药物变更记录及医学解释，并补充必要说明。`);
  useEffect(() => {
    setDispositionComment("已核对原始listing、方案条款和个例时间线，需进入医学处置闭环。");
    setQueryDraftText(`请中心确认${risk.subject}该风险相关原始记录、AE/PD/试验药物变更记录及医学解释，并补充必要说明。`);
  }, [risk.id, risk.subject]);
  const dispositionSteps = [
    ["pending_review", "待医学复核"],
    ["reviewed", "已医学复核"],
    ["query_draft", "Query草稿"],
    ["submitted_for_approval", "已提交内部审批"],
  ];
  const applyDisposition = (action) => {
    const payload = {
      comment: action === "query_draft" ? queryDraftText : dispositionComment,
      query_draft_text: action === "query_draft" ? queryDraftText : "",
      expected_source_version: risk.sourceVersion,
    };
    onApplyDisposition?.(risk, action, payload);
  };
  const canReview = dispositionState === "pending_review" && dispositionComment.trim();
  const canDraftQuery = dispositionState === "reviewed" && queryDraftText.trim();
  const canSubmitApproval = dispositionState === "query_draft" && dispositionComment.trim();
  return (
    <section className="panel risk-detail">
      <SectionTitle eyebrow="风险详情" title={risk.title} />
      <div className="risk-meta">
        <Tag tone={statusClass(risk.severity)}>{severityLabel(risk.severity)}</Tag>
        <Tag tone="warning">{risk.status}</Tag>
        <Tag tone="info">{risk.source}</Tag>
      </div>
      <div className="evidence-chain">
        <h3>证据链</h3>
        {risk.rationale ? (
          <>
            <p>{risk.rationale}</p>
            <p>推荐动作：{risk.recommendedAction}</p>
          </>
        ) : (
          <>
            <p>方案条款：抗组胺药随机前需停用 4 天。</p>
            <p>原始 CM listing 行：受试者 {risk.subject} 用药记录与随机窗口存在重叠。</p>
            <p>推荐动作：核对 CM、PD、病历和中心说明，必要时发起 query。</p>
          </>
        )}
        {risk.boundaryNote && <p className="boundary-note">{risk.boundaryNote}</p>}
        {risk.sourceRefs?.length > 0 && (
          <div className="source-ref-list">
            {risk.sourceRefs.slice(0, 6).map((ref) => {
              const safeLabel = safeSourceRefLabel(ref.label, 58);
              return (
                <span key={`${ref.source_type}-${ref.source_id}-${ref.label}`} title={safeLabel}>
                  {sourceRefTypeLabel(ref.source_type)} · {safeLabel}
                </span>
              );
            })}
          </div>
        )}
      </div>
      <div className="checklist">
        <h3>医学复核 checklist</h3>
        {["患者安全影响", "关键疗效/安全性数据影响", "是否需要发起Query", "是否影响锁库/导出"].map((item, index) => (
          <label key={item}>
            <input type="checkbox" defaultChecked={index < 2} />
            <span>{item}</span>
          </label>
        ))}
      </div>
      <div className="query-box">
        <h3>医学处置闭环</h3>
        <div className="disposition-steps">
          {dispositionSteps.map(([step, label]) => (
            <span key={step} className={`disposition-step ${step === dispositionState ? "current" : ""}`}>
              <Tag tone={ruxDispositionStepTone(dispositionState, step)}>{label}</Tag>
            </span>
          ))}
        </div>
        <label className="disposition-field">
          医学处置意见
          <textarea value={dispositionComment} onChange={(event) => setDispositionComment(event.target.value)} disabled={actionLoading || dispositionState === "submitted_for_approval"} />
        </label>
        <label className="disposition-field">
          Query草稿
          <textarea value={queryDraftText} onChange={(event) => setQueryDraftText(event.target.value)} disabled={actionLoading || dispositionState === "submitted_for_approval"} />
        </label>
        <p className="quiet-text">Query草稿为待审批内容；提交内部审批不代表对外动作、归档动作或医学定稿已经完成。</p>
        <div className="button-row">
          <button className={canReview ? "primary-button" : ""} disabled={actionLoading || !risk.inboxItemId || !canReview} onClick={() => applyDisposition("reviewed")}>
            {actionLoading ? "写入中" : "标记已复核"}
          </button>
          <button className={canDraftQuery ? "primary-button" : ""} disabled={actionLoading || !risk.inboxItemId || !canDraftQuery} onClick={() => applyDisposition("query_draft")}>
            {actionLoading ? "写入中" : "记录Query草稿"}
          </button>
          <button className={canSubmitApproval ? "primary-button" : ""} disabled={actionLoading || !risk.inboxItemId || !canSubmitApproval} onClick={() => applyDisposition("submitted_for_approval")}>
            {actionLoading ? "写入中" : "提交内部审批"}
          </button>
          <button disabled={actionLoading || !risk.inboxItemId || !risk.unread} onClick={onMarkRead}>
            {actionLoading ? "写入中" : risk.unread ? "标记已读" : "已读"}
          </button>
        </div>
        {actionMessage && <p className="gate-result">{actionMessage}</p>}
      </div>
      <div className="subject-shortcut">
        <div>
          <strong>{subject.id} 个例工作面</strong>
          <span>{subject.profile}</span>
        </div>
        <div className="button-row">
          <button onClick={() => setActivePage("subjectTimeline")}>进入 Subject Timeline</button>
          <button onClick={() => setActivePage("patientProfile")}>进入 Patient Profile</button>
        </div>
      </div>
    </section>
  );
}

function SubjectProfile({ subject, setSelectedSubject }) {
  const hasEfficacy = subject.efficacy.length > 0;
  return (
    <section className="subject-grid">
      <div className="panel">
        <SectionTitle
          eyebrow="Subject Timeline"
          title={`${subject.id} 疗效/安全性历时数据`}
          action={
            <div className="segmented">
              {subjects.map((item) => (
                <button key={item.id} className={item.id === subject.id ? "active" : ""} onClick={() => setSelectedSubject(item.id)}>
                  {item.id}
                </button>
              ))}
            </div>
          }
        />
        <div className="timeline">
          {subject.timeline.map((event, index) => (
            <div className={`timeline-event ${event.risk}`} key={`${event.day}-${event.label}`} style={{ gridColumn: index + 1 }}>
              <span>{event.day}</span>
              <strong>{event.lane}</strong>
              <em>{event.label}</em>
            </div>
          ))}
        </div>
      </div>
      <div className="panel">
        <SectionTitle title="疗效趋势" />
        <div className="trend-chart">
          {hasEfficacy ? subject.efficacy.map((point) => (
            <div className="trend-col" key={point.visit}>
              <span style={{ height: `${point.rTNSS * 9}px` }} />
              <b>{point.rTNSS}</b>
              <em>{point.visit}</em>
            </div>
          )) : <div className="empty-state">等待生成疗效趋势</div>}
        </div>
        <div className="trend-note">rTNSS 越低越好；风险提示贴在相邻时间点。</div>
      </div>
      <div className="panel">
        <SectionTitle title="Patient Profile" />
        <div className="profile-summary">
          <strong>{subject.status}</strong>
          <span>{subject.profile}</span>
          <div className="lab-list">
            {subject.labs.length ? subject.labs.map((lab) => (
              <div key={lab.name}>
                <span>{lab.name}</span>
                <strong>{lab.value}</strong>
                <Tag tone={lab.flag === "warning" ? "warning" : lab.flag === "info" ? "info" : "success"}>{lab.trend}</Tag>
              </div>
            )) : <div><span>安全性指标</span><strong>待生成</strong><Tag tone="warning">未载入</Tag></div>}
          </div>
          <div className="risk-list">
            {subject.risks.map((risk) => (
              <p key={risk}><AlertTriangle size={14} /> {risk}</p>
            ))}
          </div>
          {subject.reviewFocus?.length > 0 && (
            <div className="review-focus">
              <h3>医学复核重点</h3>
              {subject.reviewFocus.map((item) => <p key={item}>{item}</p>)}
            </div>
          )}
        </div>
      </div>
    </section>
  );
}

const timelineLaneDefs = [
  { key: "AE", label: "AE", types: ["adverse_event"] },
  { key: "IP", label: "试验药物变更", types: ["dose_adjustment"] },
  { key: "CM", label: "合并用药（非试验用药）", types: ["concomitant_medication"] },
  { key: "MH", label: "病史", types: ["medical_history"] },
  { key: "LAB", label: "实验室/疗效", types: ["lab", "efficacy_score"] },
  { key: "PD_QUERY", label: "PD / Query", types: ["protocol_deviation", "query"] },
];

function eventTone(event) {
  if (event.related_risk_ids?.length || ["protocol_deviation", "query"].includes(event.event_type)) return "critical";
  if (event.event_type === "lab" && event.clinical_interpretation) return "warning";
  if (event.event_type === "efficacy_score" && event.clinical_interpretation) return "warning";
  if (event.event_type === "efficacy_score") return "good";
  if (event.event_type === "medical_history") return "source";
  return "normal";
}

function timelineLaneClassName(laneKey) {
  return `lane-${String(laneKey).toLowerCase().replace(/_/g, "-")}`;
}

const timelineEventCategoryDefs = {
  adverse_event: { label: "AE记录", className: "event-category-adverse-event" },
  adverse_event_review: { label: "AE复核提示", className: "event-category-adverse-event-review" },
  dose_adjustment: { label: "试验药物变更", className: "event-category-dose-adjustment" },
  dose_adjustment_paused: { label: "试验药物暂停", className: "event-category-dose-adjustment-paused" },
  dose_adjustment_resumed: { label: "试验药物恢复", className: "event-category-dose-adjustment-resumed" },
  concomitant_medication: { label: "CM非试验用药", className: "event-category-concomitant-medication" },
  concomitant_medication_risk: { label: "禁限用药/洗脱风险", className: "event-category-concomitant-medication-risk" },
  medical_history: { label: "病史", className: "event-category-medical-history" },
  lab: { label: "实验室", className: "event-category-lab" },
  lab_hematology: { label: "血常规异常", className: "event-category-lab-hematology" },
  lab_chemistry: { label: "血生化异常", className: "event-category-lab-chemistry" },
  efficacy_score: { label: "疗效", className: "event-category-efficacy-score" },
  protocol_deviation: { label: "PD", className: "event-category-protocol-deviation" },
  query: { label: "Query", className: "event-category-query" },
};

function timelineEventCategoryKey(event) {
  const text = [event.title, event.detail, event.clinical_interpretation].filter(Boolean).join(" ");
  if (event.event_type === "dose_adjustment") {
    if (text.includes("暂停用药")) return "dose_adjustment_paused";
    if (text.includes("重新用药") || text.includes("恢复")) return "dose_adjustment_resumed";
    return "dose_adjustment";
  }
  if (event.event_type === "lab") {
    if (event.source_domain === "LBHEMA") return "lab_hematology";
    if (event.source_domain === "LBCHEM") return "lab_chemistry";
    return "lab";
  }
  if (event.event_type === "concomitant_medication") {
    if (/禁用|限制|洗脱|违背|风险|PD|query/i.test(text)) return "concomitant_medication_risk";
    return "concomitant_medication";
  }
  if (event.event_type === "adverse_event") {
    if (event.related_risk_ids?.length || /复核|漏报|给药调整|实验室|关系|医学/.test(text)) return "adverse_event_review";
    return "adverse_event";
  }
  return event.event_type;
}

function timelineEventCategoryDef(event) {
  return timelineEventCategoryDefs[timelineEventCategoryKey(event)] || {
    label: event.source_domain || "事件",
    className: "event-category-other",
  };
}

function eventCategoryClassName(event) {
  return timelineEventCategoryDef(event).className;
}

function timelineEventCategoryLabel(event) {
  return timelineEventCategoryDef(event).label;
}

function timelineLegendItems(lanes = []) {
  const seen = new Set();
  return lanes.flatMap((lane) => lane.events.map(({ event }) => {
    const category = timelineEventCategoryDef(event);
    const key = `${lane.key}-${timelineEventCategoryKey(event)}-${category.className}`;
    if (seen.has(key)) return null;
    seen.add(key);
    return { ...category, key, laneLabel: lane.label };
  })).filter(Boolean);
}

function visitAxisFromEvents(events = []) {
  const visits = events
    .filter((event) => event.event_type === "visit")
    .map((event) => ({
      code: event.visit_code || `D${event.study_day}`,
      label: event.visit_label || event.title,
      day: event.study_day,
      date: event.event_date,
      title: event.title,
    }));
  if (visits.length) return visits.sort((left, right) => left.day - right.day);
  const byVisit = new Map();
  for (const event of events) {
    const code = event.visit_code || `D${event.study_day}`;
    if (!byVisit.has(code)) {
      byVisit.set(code, {
        code,
        label: event.visit_label || code,
        day: event.study_day,
        date: event.event_date,
        title: event.visit_label || code,
      });
    }
  }
  return [...byVisit.values()].sort((left, right) => left.day - right.day);
}

function dateAtStudyDay(baselineDate, studyDay) {
  if (!baselineDate) return "";
  const parsed = new Date(`${baselineDate}T00:00:00`);
  if (Number.isNaN(parsed.getTime())) return "";
  parsed.setDate(parsed.getDate() + studyDay - 1);
  return parsed.toISOString().slice(0, 10);
}

function plannedVisitAxis(subject, events = []) {
  const rawVisits = visitAxisFromEvents(events);
  const rawByCode = new Map(rawVisits.map((visit) => [visit.code, visit]));
  const rawByDay = new Map(rawVisits.map((visit) => [visit.day, visit]));
  const baselineDate = subject.rawProfile?.subject?.baseline_visit_date || rawByCode.get("D1")?.date || rawByDay.get(1)?.date || "";
  const scr = rawByCode.get("SCR") || rawVisits.find((visit) => visit.day < 1);
  const planned = [
    { code: "V1D-7~D-1", day: scr?.day ?? -7, date: scr?.date || dateAtStudyDay(baselineDate, -7), label: "筛选" },
    { code: "V2D1", day: 1, date: rawByCode.get("D1")?.date || dateAtStudyDay(baselineDate, 1), label: "随机/给药" },
    { code: "V3D8", day: 8, date: rawByCode.get("W1")?.date || dateAtStudyDay(baselineDate, 8), label: "第1周" },
    { code: "V4D15", day: 15, date: rawByCode.get("W2")?.date || dateAtStudyDay(baselineDate, 15), label: "第2周" },
    { code: "V5D29", day: 29, date: rawByCode.get("W4")?.date || dateAtStudyDay(baselineDate, 29), label: "第4周" },
    { code: "V6D57", day: 57, date: dateAtStudyDay(baselineDate, 57), label: "第8周" },
    { code: "V7D85", day: 85, date: dateAtStudyDay(baselineDate, 85), label: "第12周" },
  ];
  return planned.filter((visit) => visit.date || visit.day <= 29);
}

function laneForEvent(event) {
  return timelineLaneDefs.find((lane) => lane.types.includes(event.event_type))?.key || "LAB";
}

function referenceTimelineLanes(events = []) {
  const coreLaneKeys = new Set(["AE", "IP", "CM", "MH"]);
  return timelineLaneDefs
    .map((lane) => {
      const laneEvents = events
        .filter((event) => laneForEvent(event) === lane.key)
        .sort((left, right) => (left.study_day ?? 0) - (right.study_day ?? 0) || String(left.event_id).localeCompare(String(right.event_id)))
        .map((event, index) => ({
          event,
          displayLabel: shortTimelineEventLabel(event, index),
        }));
      return { ...lane, events: laneEvents };
    })
    .filter((lane) => lane.events.length || coreLaneKeys.has(lane.key));
}

function referenceEventTooltip(event, label) {
  return [
    label,
    event.source_record_id,
    event.visit_code || `D${event.study_day}`,
    event.title,
    event.detail,
    event.clinical_interpretation,
  ].filter(Boolean).join("｜");
}

function timelineHeaderMeta(subject) {
  const overview = subject.rawProfile?.subject;
  const windowStart = overview?.baseline_visit_date ? dateAtStudyDay(overview.baseline_visit_date, -7) : "";
  const windowEnd = overview?.baseline_visit_date ? dateAtStudyDay(overview.baseline_visit_date, 85) : "";
  return {
    subjectId: subject.id,
    arm: overview?.treatment_arm || "安慰剂组",
    randomization: overview?.randomization_number || subject.id,
    site: overview?.site_id || subject.site || "-",
    center: subject.site === "10" ? "首都医科大学附属北京同仁医院" : "河北省中医院",
    window: [windowStart, windowEnd].filter(Boolean).join(" ~ "),
    sexAgeStatus: subject.id === "10008" ? "男 | 31岁 | 治疗期" : "女 | 42岁 | 治疗期",
  };
}

function referenceRiskCards(subject) {
  const prompts = subject.rawProfile?.risk_prompts || [];
  const events = subject.rawProfile?.timeline || [];
  const cmEvent = events.find((event) => event.source_domain === "CM");
  const pdEvent = events.find((event) => event.source_domain === "PD");
  const aeEvent = events.find((event) => event.source_domain === "AE");
  const labEvent = events.find((event) => event.source_domain === "LB" && event.related_risk_ids?.length);
  const washoutPrompt = prompts.find((prompt) => prompt.risk_type?.includes("washout")) || prompts[0];
  const aePrompt = prompts.find((prompt) => prompt.risk_type?.includes("ae") || prompt.risk_type?.includes("lab")) || prompts[1] || prompts[0];
  return [
    {
      title: "潜在合并用药违背",
      body: cmEvent
        ? `${cmEvent.title.replace("筛选期使用", "")} | ${cmEvent.detail.replace("用于", "| 用于")} | ${cmEvent.event_date} | ${pdEvent ? "PD/Query待关闭" : "需医学确认"}`
        : washoutPrompt?.prompt_text || "合并用药与访视窗口需要医学复核。",
      accent: "strong",
    },
    {
      title: "潜在入排违背PD",
      body: pdEvent?.detail || washoutPrompt?.recommended_action || "未按当前规则识别到筛选时仍持续命中排除标准的病史风险。",
      accent: "plain",
    },
    {
      title: "潜在AE评估不当",
      body: aeEvent
        ? `${aeEvent.title} 说明书/IB：感染/实验室风险 | ${labEvent?.title || "同访视安全性信号"} | 关系 ${aePrompt?.status === "resolved" ? "已确认" : "需复核"} | ${aeEvent.event_date}`
        : aePrompt?.prompt_text || "AE、MH、CM、实验室与疗效趋势需要联合复核。",
      accent: "strong",
    },
  ];
}

function shortTimelineEventLabel(event, laneIndex) {
  const prefix = {
    adverse_event: "AE",
    dose_adjustment: "DA",
    concomitant_medication: "CM",
    medical_history: "MH",
    lab: "LB",
    efficacy_score: "QS",
    protocol_deviation: "PD",
    query: "Q",
  }[event.event_type] || event.source_domain || "E";
  return `${prefix}${laneIndex + 1}`;
}

function ReferenceTimelineSvg({ visits, lanes }) {
  const width = 1500;
  const left = 150;
  const right = 120;
  const dayValues = visits.map((visit) => visit.day).filter((value) => Number.isFinite(value));
  const minDay = Math.min(...dayValues, -7);
  const maxDay = Math.max(...dayValues, 85);
  const span = Math.max(maxDay - minDay, 1);
  const xFor = (day) => left + ((Math.min(Math.max(day, minDay), maxDay) - minDay) / span) * (width - left - right);

  const visitLayout = [];
  let cluster = [];
  const flushCluster = () => {
    cluster.forEach((item, index) => {
      visitLayout.push({
        ...item,
        side: index % 2 === 0 ? "below" : "above",
        level: Math.floor(index / 2),
      });
    });
    cluster = [];
  };
  visits.forEach((visit) => {
    const x = xFor(visit.day);
    if (cluster.length && Math.abs(x - cluster[cluster.length - 1].x) >= 108) flushCluster();
    cluster.push({ visit, x });
  });
  flushCluster();

  const maxAbove = Math.max(0, ...visitLayout.filter((item) => item.side === "above").map((item) => item.level));
  const maxBelow = Math.max(0, ...visitLayout.filter((item) => item.side === "below").map((item) => item.level));
  const tagGap = 38;
  const axisY = 96 + maxAbove * tagGap;
  let cursorY = axisY + 76 + maxBelow * tagGap;
  const rowGap = 20;
  const laneGap = 22;
  const laneLayouts = lanes.map((lane) => {
    const height = Math.max(48, Math.max(lane.events.length, 1) * rowGap + 14);
    const layout = { lane, y: cursorY, height };
    cursorY += height + laneGap;
    return layout;
  });
  const height = cursorY + 24;

  return (
    <svg viewBox={`0 0 ${width} ${height}`} className="reference-timeline-svg" role="img" aria-label="受试者时间线">
      <line x1={left} y1={axisY} x2={width - right} y2={axisY} className="reference-svg-axis" />
      <text x={left} y="30" className="reference-svg-date">{visits[0]?.date}</text>
      <text x={width - right} y="30" textAnchor="end" className="reference-svg-date">{visits[visits.length - 1]?.date}</text>
      {visitLayout.map((item) => {
        const labelY = item.side === "above" ? axisY - 38 - item.level * tagGap : axisY + 28 + item.level * tagGap;
        const dateY = item.side === "above" ? axisY - 20 - item.level * tagGap : axisY + 46 + item.level * tagGap;
        return (
          <g key={`${item.visit.code}-${item.visit.day}`}>
            <line x1={item.x} y1={axisY - 16} x2={item.x} y2={height - 30} className="reference-svg-visit-line" />
            <circle cx={item.x} cy={axisY} r="4.5" className="reference-svg-visit-dot">
              <title>{[item.visit.code, item.visit.date, item.visit.label].filter(Boolean).join("｜")}</title>
            </circle>
            <text x={item.x} y={labelY} textAnchor="middle" className="reference-svg-visit-label">{item.visit.code}</text>
            <text x={item.x} y={dateY} textAnchor="middle" className="reference-svg-visit-date">{item.visit.date}</text>
          </g>
        );
      })}
      {laneLayouts.map(({ lane, y, height: laneHeight }) => (
        <g key={lane.key}>
          <text x="22" y={y + 14} className="reference-svg-lane-title">{lane.label}</text>
          <line x1={left} y1={y - 14} x2={width - right} y2={y - 14} className="reference-svg-lane-rule" />
          {lane.events.length ? lane.events.map(({ event, displayLabel }, index) => {
            const eventY = y + index * rowGap;
            const eventX = xFor(event.study_day);
            const eventBlockX = Math.min(Math.max(eventX, left), width - right - 30);
            return (
              <g key={event.event_id}>
                <text x="142" y={eventY + 13} textAnchor="end" className="reference-svg-event-label">{displayLabel}</text>
                <rect
                  x={eventBlockX}
                  y={eventY}
                  width="30"
                  height="17"
                  rx="3"
                  className={`reference-svg-event-block ${timelineLaneClassName(lane.key)} ${eventCategoryClassName(event)} ${eventTone(event)}`}
                >
                  <title>{referenceEventTooltip(event, displayLabel)}</title>
                </rect>
              </g>
            );
          }) : (
            <text x="142" y={y + 13} textAnchor="end" className="reference-svg-event-empty">暂无</text>
          )}
          <line x1={left} y1={y + laneHeight + 6} x2={width - right} y2={y + laneHeight + 6} className="reference-svg-lane-rule soft" />
        </g>
      ))}
    </svg>
  );
}

function subjectCenterGroups(items = subjects) {
  const groups = new Map();
  items.forEach((item) => {
    const center = item.site || "未分中心";
    if (!groups.has(center)) groups.set(center, []);
    groups.get(center).push(item);
  });
  return Array.from(groups.entries())
    .sort(([left], [right]) => String(left).localeCompare(String(right), "zh-CN", { numeric: true }))
    .map(([center, centerSubjects]) => ({
      center,
      subjects: centerSubjects.sort((left, right) => String(left.id).localeCompare(String(right.id), "zh-CN", { numeric: true })),
    }));
}

function profileSubjectMeta(subject) {
  const raw = subject.rawProfile?.subject;
  return [
    { label: "中心", value: raw?.site_id || subject.site },
    { label: "筛选号", value: raw?.screening_number },
    { label: "随机号", value: raw?.randomization_number },
    { label: "治疗组", value: raw?.treatment_arm },
    { label: "入组状态", value: raw?.enrollment_status },
    { label: "基线/随机日期", value: raw?.baseline_visit_date },
    { label: "首次给药", value: raw?.first_dose_date },
    { label: "最近访视", value: [raw?.latest_visit_code, raw?.latest_visit_label, raw?.latest_visit_date].filter(Boolean).join(" / ") },
  ].filter((item) => item.value);
}

function metricRiskCount(metric) {
  return (metric.points || []).filter((point) => point.risk_flag || ["high", "low"].includes(point.normality)).length;
}

function relatedTimelineEvents(events, types) {
  return events.filter((event) => types.includes(event.event_type));
}

function SubjectCatalogControl({ subjectCatalog = subjects, selectedSubject, setSelectedSubject, className = "" }) {
  if (subjectCatalog.length > 12) {
    return (
      <label className={`subject-catalog-select ${className}`}>
        <select value={selectedSubject} onChange={(event) => setSelectedSubject(event.target.value)}>
          {subjectCatalog.map((item) => (
            <option key={item.id} value={item.id}>
              {item.id} | 中心 {item.site || "-"} | {item.status || "状态未记录"}
            </option>
          ))}
        </select>
      </label>
    );
  }
  return (
    <div className={`segmented subject-switch ${className}`}>
      {subjectCatalog.map((item) => (
        <button key={item.id} className={item.id === selectedSubject ? "active" : ""} onClick={() => setSelectedSubject(item.id)}>
          {item.id}
        </button>
      ))}
    </div>
  );
}

function TrendSparkline({ metric, compact = false }) {
  const points = metric?.points || [];
  if (!points.length) return <div className="empty-state">暂无 {metric?.metric_label || "指标"} 趋势</div>;
  const width = 620;
  const height = compact ? 132 : 170;
  const pad = { left: 42, right: 18, top: 18, bottom: 30 };
  const values = points.map((point) => point.value);
  const refs = points.flatMap((point) => [point.reference_low, point.reference_high]).filter((value) => typeof value === "number");
  const minValue = Math.min(...values, ...refs);
  const maxValue = Math.max(...values, ...refs);
  const yMin = minValue === maxValue ? minValue - 1 : minValue - (maxValue - minValue) * 0.12;
  const yMax = minValue === maxValue ? maxValue + 1 : maxValue + (maxValue - minValue) * 0.12;
  const xFor = (index) => pad.left + (points.length === 1 ? 0 : (index / (points.length - 1)) * (width - pad.left - pad.right));
  const yFor = (value) => pad.top + ((yMax - value) / (yMax - yMin || 1)) * (height - pad.top - pad.bottom);
  const line = points.map((point, index) => `${xFor(index)},${yFor(point.value)}`).join(" ");
  const refLow = points.find((point) => typeof point.reference_low === "number")?.reference_low;
  const refHigh = points.find((point) => typeof point.reference_high === "number")?.reference_high;
  return (
    <div className="metric-chart">
      <div className="metric-chart-head">
        <div>
          <strong>{metric.metric_label}</strong>
          <span>{metric.unit || "分值"} · {metric.direction === "lower_is_better" ? "越低越好" : metric.direction === "stable_range" ? "参考范围内稳定" : "越高越好"}</span>
        </div>
        <Tag tone={metricRiskCount(metric) ? "warning" : "success"}>{metricRiskCount(metric) ? `${metricRiskCount(metric)} 个关注点` : "趋势可读"}</Tag>
      </div>
      <svg viewBox={`0 0 ${width} ${height}`} role="img" aria-label={`${metric.metric_label} 历时趋势`}>
        <line x1={pad.left} y1={height - pad.bottom} x2={width - pad.right} y2={height - pad.bottom} className="chart-axis-line" />
        <line x1={pad.left} y1={pad.top} x2={pad.left} y2={height - pad.bottom} className="chart-axis-line" />
        {typeof refLow === "number" && <line x1={pad.left} y1={yFor(refLow)} x2={width - pad.right} y2={yFor(refLow)} className="chart-ref-line" />}
        {typeof refHigh === "number" && <line x1={pad.left} y1={yFor(refHigh)} x2={width - pad.right} y2={yFor(refHigh)} className="chart-ref-line" />}
        <polyline points={line} className="chart-line" />
        {points.map((point, index) => (
          <g key={point.point_id || `${metric.metric_key}-${point.visit_code}`}>
            <circle cx={xFor(index)} cy={yFor(point.value)} r={point.risk_flag ? 5 : 4} className={point.risk_flag ? "chart-point risk" : "chart-point"} />
            <text x={xFor(index)} y={height - 10} textAnchor="middle" className="chart-label">{point.visit_code}</text>
            <text x={xFor(index)} y={yFor(point.value) - 8} textAnchor="middle" className="chart-value">{point.value}</text>
          </g>
        ))}
      </svg>
      <div className="metric-point-list">
        {points.map((point) => (
          <div key={point.point_id || `${metric.metric_key}-${point.visit_code}`}>
            <strong>{point.visit_code}</strong>
            <span>
              {point.assessment_date} · {point.value}{metric.unit ? ` ${metric.unit}` : ""}
              {typeof point.change_from_baseline === "number" ? ` · 较基线 ${point.change_from_baseline}` : ""}
            </span>
            <Tag tone={point.risk_flag ? "warning" : point.normality === "high" || point.normality === "low" ? "warning" : "success"}>
              {point.risk_flag ? "风险点" : point.normality === "not_applicable" ? "已记录" : point.normality}
            </Tag>
          </div>
        ))}
      </div>
    </div>
  );
}

function ProfileFilterBar({ selectedCenter, setSelectedCenter, search, setSearch, visibleSubjects, selectedSubject, setSelectedSubject, allSubjects = subjects }) {
  const centers = subjectCenterGroups(allSubjects).map((group) => group.center);
  return (
    <section className="panel profile-filter-bar">
      <div>
        <strong>中心筛选</strong>
        <div className="segmented">
          <button className={selectedCenter === "all" ? "active" : ""} onClick={() => setSelectedCenter("all")}>全部</button>
          {centers.map((center) => (
            <button key={center} className={selectedCenter === center ? "active" : ""} onClick={() => setSelectedCenter(center)}>
              {center}
            </button>
          ))}
        </div>
      </div>
      <div>
        <strong>受试者切换</strong>
        <SubjectCatalogControl
          subjectCatalog={visibleSubjects}
          selectedSubject={selectedSubject}
          setSelectedSubject={setSelectedSubject}
        />
      </div>
      <label>
        <strong>检索</strong>
        <span>
          <Search size={15} />
          <input value={search} onChange={(event) => setSearch(event.target.value)} placeholder="受试者、中心、状态" />
        </span>
      </label>
    </section>
  );
}

function ProfileSubjectTree({ selectedCenter, search, selectedSubject, setSelectedSubject, allSubjects = subjects }) {
  const query = search.trim().toLowerCase();
  const groups = subjectCenterGroups(allSubjects)
    .filter((group) => selectedCenter === "all" || group.center === selectedCenter)
    .map((group) => ({
      ...group,
      subjects: group.subjects.filter((item) => {
        const haystack = [item.id, item.site, item.status, item.profile].filter(Boolean).join(" ").toLowerCase();
        return !query || haystack.includes(query);
      }),
    }))
    .filter((group) => group.subjects.length);

  return (
    <aside className="panel profile-subject-list">
      <SectionTitle title="中心 / 受试者树" />
      <div className="profile-tree">
        {groups.map((group) => (
          <div className="profile-tree-group" key={group.center}>
            <div className="profile-tree-center">
              <strong>中心 {group.center}</strong>
              <span>{group.subjects.length} 例</span>
            </div>
            {group.subjects.map((item) => (
              <button key={item.id} className={item.id === selectedSubject ? "selected" : ""} onClick={() => setSelectedSubject(item.id)}>
                <strong>{item.id}</strong>
                <span>{item.profile || `中心 ${item.site}`}</span>
                <Tag tone={statusClass(item.status)}>{item.status}</Tag>
              </button>
            ))}
          </div>
        ))}
        {!groups.length && <div className="empty-state">当前筛选下无受试者。</div>}
      </div>
    </aside>
  );
}

function ProfilePanel({ title, eyebrow, children, action }) {
  return (
    <section className="panel profile-section">
      <SectionTitle eyebrow={eyebrow} title={title} action={action} />
      {children}
    </section>
  );
}

function SubjectTimelinePageLegacy({ subject, setSelectedSubject, setActivePage }) {
  return (
    <main className="page timeline-page">
      <SectionTitle
        eyebrow="医学监查 / Subject Timeline"
        title={`${subject.id} 受试者时间线与风险锚点`}
        action={<button onClick={() => setActivePage("monitoring")}>返回风险复核</button>}
      />
      <section className="timeline-toolbar panel">
        <div>
          <strong>受试者</strong>
          <div className="segmented">
            {subjects.map((item) => (
              <button key={item.id} className={item.id === subject.id ? "active" : ""} onClick={() => setSelectedSubject(item.id)}>
                {item.id}
              </button>
            ))}
          </div>
        </div>
        <div>
          <strong>筛选</strong>
          <input placeholder="搜索 AE、DA、MH、CM、PD、Query、风险" />
        </div>
        <div>
          <strong>当前复核状态</strong>
          <Tag tone={statusClass(subject.status)}>{subject.status}</Tag>
        </div>
      </section>
      <section className="timeline-risk-cards">
        {subject.risks.map((risk) => (
          <div className="timeline-risk-card" key={risk}>
            <strong>{risk}</strong>
            <span>已锚定到相应访视/事件；点击事件后可回到风险复核。</span>
          </div>
        ))}
      </section>
      <section className="panel timeline-canvas">
        <div className="timeline-axis">
          {subject.timeline.map((event) => (
            <div className="axis-point" key={`${event.day}-${event.label}`}>
              <span>{event.day}</span>
              <b />
              <em>{event.label}</em>
            </div>
          ))}
        </div>
        <div className="timeline-lanes">
          {["AE", "试验药物变更", "合并用药（非试验用药）", "病史", "访视/PD/Query"].map((lane) => (
            <div className="lane-row" key={lane}>
              <strong>{lane}</strong>
              <div>
                {subject.timeline
                  .filter((event) => {
                    if (lane === "AE") return ["AE"].includes(event.lane);
                    if (lane === "试验药物变更") return ["IP"].includes(event.lane);
                    if (lane === "合并用药（非试验用药）") return ["CM"].includes(event.lane);
                    if (lane === "病史") return ["MH"].includes(event.lane);
                    return !["AE", "IP", "CM", "MH"].includes(event.lane);
                  })
                  .map((event) => <button className={`lane-event ${event.risk}`} key={`${lane}-${event.day}-${event.label}`}>{event.day} · {event.label}</button>)}
              </div>
            </div>
          ))}
        </div>
      </section>
      <section className="timeline-detail-grid">
        <div className="panel">
          <SectionTitle title="AE 明细" />
          <p>眼部症状、头痛、感染相关事件按发生时间和转归展示；正式版需从 AE listing 保留 source row。</p>
        </div>
        <div className="panel">
          <SectionTitle title="合并用药（非试验用药）" />
          <p>仅展示非试验用合并用药；非药物治疗、试验药物暂停/恢复和剂量调整需单列域展示。</p>
        </div>
        <div className="panel">
          <SectionTitle title="试验药物变更" />
          <p>单列试验药物暂停、恢复、剂量调整和其他研究治疗相关变更，避免与 CM 混淆。</p>
        </div>
        <div className="panel">
          <SectionTitle title="PD / Query 登记" />
          {subject.queries.length ? subject.queries.map((query) => <p key={query}>{query}</p>) : <p>当前无开放 Query。</p>}
        </div>
      </section>
    </main>
  );
}

function PatientProfilePageLegacy({ subject, setSelectedSubject, setActivePage }) {
  const hasEfficacy = subject.efficacy.length > 0;
  return (
    <main className="page patient-profile-page">
      <section className="profile-hero">
        <div>
          <span>医学监查 / Patient Profile</span>
          <h2>{subject.id} 疗效、安全性和医学解释画像</h2>
          <p>{subject.profile}</p>
        </div>
        <button onClick={() => setActivePage("monitoring")}>返回风险复核</button>
      </section>
      <div className="profile-workbench">
        <aside className="panel profile-subject-list">
          <SectionTitle title="受试者" />
          {subjects.map((item) => (
            <button key={item.id} className={item.id === subject.id ? "selected" : ""} onClick={() => setSelectedSubject(item.id)}>
              <strong>{item.id}</strong>
              <span>中心 {item.site}</span>
              <Tag tone={statusClass(item.status)}>{item.status}</Tag>
            </button>
          ))}
        </aside>
        <section className="profile-main">
          <div className="panel profile-summary-band">
            <div><strong>{subject.status}</strong><span>当前医学复核状态</span></div>
            <div><strong>{subject.efficacy.length || "-"}</strong><span>疗效访视点</span></div>
            <div><strong>{subject.labs.length || "-"}</strong><span>安全性指标</span></div>
            <div><strong>{subject.risks.length}</strong><span>开放风险提示</span></div>
          </div>
          <section className="panel">
            <SectionTitle title="疗效指标历时变化" />
            {hasEfficacy ? (
              <div className="profile-trend-table">
                <div><strong>访视</strong><strong>rTNSS</strong><strong>解释</strong></div>
                {subject.efficacy.map((point) => (
                  <div key={point.visit}>
                    <span>{point.visit}</span>
                    <strong>{point.rTNSS}</strong>
                    <span>{point.risk === "warning" ? "受风险点影响，需结合 Query/PD 解释" : "可用于趋势判断"}</span>
                  </div>
                ))}
              </div>
            ) : <div className="empty-state">等待生成疗效趋势</div>}
          </section>
          <section className="profile-two-col">
            <div className="panel">
              <SectionTitle title="实验室 / 安全性趋势" />
              <div className="lab-list">
                {subject.labs.map((lab) => (
                  <div key={lab.name}>
                    <span>{lab.name}</span>
                    <strong>{lab.value}</strong>
                    <Tag tone={lab.flag === "warning" ? "warning" : lab.flag === "info" ? "info" : "success"}>{lab.trend}</Tag>
                  </div>
                ))}
              </div>
            </div>
            <div className="panel">
              <SectionTitle title="医学复核重点" />
              <div className="risk-list">
                {[...subject.risks, ...(subject.reviewFocus || [])].map((risk) => (
                  <p key={risk}><AlertTriangle size={14} /> {risk}</p>
                ))}
              </div>
            </div>
          </section>
        </section>
      </div>
    </main>
  );
}

function SubjectTimelinePage({ subject, setSelectedSubject, setActivePage, subjectCatalog = subjects }) {
  const rawProfile = subject.rawProfile;
  const rawEvents = rawProfile?.timeline || [];
  const visits = plannedVisitAxis(subject, rawEvents);
  const nonVisitEvents = rawEvents.filter((event) => event.event_type !== "visit");
  const meta = timelineHeaderMeta(subject);
  const riskCards = referenceRiskCards(subject);
  const displayLanes = referenceTimelineLanes(nonVisitEvents);
  const legendItems = timelineLegendItems(displayLanes);

  return (
    <main className="page timeline-page reference-timeline-page">
      <section className="reference-subject-head">
        <div>
          <h2>{meta.subjectId}</h2>
          <strong>{meta.arm} | {meta.randomization}</strong>
          <p>{meta.site} | {meta.center} | {meta.arm} | {meta.randomization} | 研究窗口 {meta.window}</p>
        </div>
        <div className="reference-subject-actions">
          <span>{meta.sexAgeStatus}</span>
          <button onClick={() => setActivePage("monitoring")}>返回医学监查</button>
        </div>
      </section>

      <section className="reference-subject-switch">
        <span>受试者</span>
        <SubjectCatalogControl
          subjectCatalog={subjectCatalog}
          selectedSubject={subject.id}
          setSelectedSubject={setSelectedSubject}
        />
      </section>

      <section className="reference-risk-cards">
        {riskCards.map((card) => (
          <div className={`reference-risk-card ${card.accent}`} key={card.title}>
            <h3>{card.title}</h3>
            <p>{card.body}</p>
          </div>
        ))}
      </section>

      <section className="reference-timeline-shell">
        <div className="timeline-category-legend" aria-label="事件类别颜色图例">
          {legendItems.map((item) => (
            <span className={`timeline-category-chip ${item.className}`} key={item.key}>
              <span aria-hidden="true" />
              {item.laneLabel} · {item.label}
            </span>
          ))}
        </div>
        <div className="reference-timeline-scroll">
          <div className="reference-timeline-canvas">
            <ReferenceTimelineSvg visits={visits} lanes={displayLanes} />
          </div>
        </div>
      </section>

      <section className="timeline-detail-grid">
        {displayLanes.map((lane) => {
          return (
            <div className="panel timeline-detail-card" key={lane.key}>
              <SectionTitle title={`${lane.label} 明细`} />
              {lane.events.length ? lane.events.map(({ event, displayLabel }) => (
                <div className={`timeline-detail-row ${eventCategoryClassName(event)}`} key={event.event_id}>
                  <Tag tone={eventTone(event) === "critical" ? "danger" : eventTone(event) === "warning" ? "warning" : "info"}>{timelineEventCategoryLabel(event)}</Tag>
                  <div>
                    <strong>{displayLabel} · {event.visit_code || `D${event.study_day}`} · {event.title}</strong>
                    <span>{event.source_domain ? `${event.source_domain} · ` : ""}{event.detail}</span>
                    {event.clinical_interpretation && <em>{event.clinical_interpretation}</em>}
                  </div>
                </div>
              )) : <p className="quiet-text">当前受试者该域暂无事件。</p>}
            </div>
          );
        })}
      </section>
    </main>
  );
}

function PatientProfilePage({ subject, setSelectedSubject, setActivePage, subjectCatalog = subjects }) {
  const [selectedCenter, setSelectedCenter] = useState(subject.site || "all");
  const [search, setSearch] = useState("");
  const rawProfile = subject.rawProfile;
  const efficacyMetrics = subject.efficacyMetrics || [];
  const safetyMetrics = subject.safetyMetrics || [];
  const prompts = rawProfile?.risk_prompts || subject.prompts || [];
  const events = rawProfile?.timeline || [];
  const query = search.trim().toLowerCase();
  const visibleSubjects = useMemo(() => subjectCatalog.filter((item) => {
    const matchesCenter = selectedCenter === "all" || item.site === selectedCenter;
    const haystack = [item.id, item.site, item.status, item.profile].filter(Boolean).join(" ").toLowerCase();
    return matchesCenter && (!query || haystack.includes(query));
  }), [selectedCenter, query, subjectCatalog]);
  const subjectMeta = profileSubjectMeta(subject);
  const medicalContext = rawProfile?.subject?.key_medical_context || [];
  const pdQueryEvents = relatedTimelineEvents(events, ["protocol_deviation", "query"]);
  const pdQueryPrompts = prompts.filter((prompt) => prompt.query_id || prompt.pd_id);
  const nonVisitEvents = events.filter((event) => event.event_type !== "visit");
  const totalTrendPoints = [...efficacyMetrics, ...safetyMetrics].reduce((sum, metric) => sum + (metric.points?.length || 0), 0);

  useEffect(() => {
    if (!visibleSubjects.length || visibleSubjects.some((item) => item.id === subject.id)) return;
    setSelectedSubject(visibleSubjects[0].id);
  }, [subject.id, visibleSubjects, setSelectedSubject]);

  return (
    <main className="page patient-profile-page">
      <section className="profile-hero">
        <div>
          <span>医学监查 / Patient Profile</span>
          <h2>{subject.id} 疗效、安全性和医学解释画像</h2>
          <p>{rawProfile?.subject?.key_medical_context?.join("；") || subject.profile}</p>
        </div>
        <button onClick={() => setActivePage("monitoring")}>返回医学监查</button>
      </section>

      <ProfileFilterBar
        selectedCenter={selectedCenter}
        setSelectedCenter={setSelectedCenter}
        search={search}
        setSearch={setSearch}
        visibleSubjects={visibleSubjects}
        selectedSubject={subject.id}
        setSelectedSubject={setSelectedSubject}
        allSubjects={subjectCatalog}
      />

      <div className="profile-workbench">
        <ProfileSubjectTree
          selectedCenter={selectedCenter}
          search={search}
          selectedSubject={subject.id}
          setSelectedSubject={setSelectedSubject}
          allSubjects={subjectCatalog}
        />
        <section className="profile-main">
          <div className="panel profile-summary-band">
            <div><strong>{subject.status}</strong><span>当前医学复核状态</span></div>
            <div><strong>{efficacyMetrics.length || "-"}</strong><span>疗效指标</span></div>
            <div><strong>{safetyMetrics.length || "-"}</strong><span>安全性指标</span></div>
            <div><strong>{totalTrendPoints || prompts.length}</strong><span>趋势点 / 风险提示</span></div>
          </div>

          <ProfilePanel title="基本信息" eyebrow="Profile">
            <div className="profile-info-grid">
              {subjectMeta.length ? subjectMeta.map((item) => (
                <div key={item.label}>
                  <span>{item.label}</span>
                  <strong>{item.value}</strong>
                </div>
              )) : (
                <div>
                  <span>个例资料</span>
                  <strong>{subject.profile || "待生成完整个例下钻资料"}</strong>
                </div>
              )}
            </div>
            <div className="profile-context-list">
              {(medicalContext.length ? medicalContext : [subject.profile || "完整个例下钻资料待生成；当前仅显示风险登记入口。"]).map((item) => (
                <p key={item}>{item}</p>
              ))}
            </div>
          </ProfilePanel>

          <ProfilePanel title="疗效指标历时变化" eyebrow="Efficacy" action={<Tag tone={efficacyMetrics.length ? "info" : "warning"}>{efficacyMetrics.length || 0} 个指标</Tag>}>
            <div className="metric-chart-grid">
              {efficacyMetrics.length ? efficacyMetrics.map((metric) => (
                <TrendSparkline metric={metric} key={metric.metric_key || metric.metric_label} />
              )) : <div className="empty-state">等待生成疗效趋势</div>}
            </div>
          </ProfilePanel>

          <ProfilePanel title="安全性历时变化" eyebrow="Safety" action={<Tag tone={safetyMetrics.some(metricRiskCount) ? "warning" : "info"}>{safetyMetrics.length || 0} 个指标</Tag>}>
            <div className="metric-chart-grid">
              {safetyMetrics.length ? safetyMetrics.map((metric) => (
                <TrendSparkline metric={metric} key={metric.metric_key || metric.metric_label} compact />
              )) : <div className="empty-state">等待生成安全性趋势</div>}
            </div>
          </ProfilePanel>

          <ProfilePanel title="PD / Query" eyebrow="Protocol Deviation">
            <div className="profile-pd-query-grid">
              <div>
                <h3>开放 PD / Query</h3>
                {pdQueryPrompts.length ? pdQueryPrompts.map((prompt) => (
                  <div className="profile-query-card" key={prompt.prompt_id || prompt.title}>
                    <Tag tone={statusClass(prompt.severity)}>{severityLabel(prompt.severity)}</Tag>
                    <div>
                      <strong>{prompt.query_id || prompt.pd_id || prompt.visit_code} · {prompt.title}</strong>
                      <span>{prompt.recommended_action}</span>
                    </div>
                  </div>
                )) : <p className="quiet-text">当前未识别到开放 PD / Query 提示。</p>}
              </div>
              <div>
                <h3>时间线事件</h3>
                {pdQueryEvents.length ? pdQueryEvents.map((event) => (
                  <div className="profile-query-card" key={event.event_id}>
                    <Tag tone={event.event_type === "query" ? "info" : "warning"}>{event.source_domain}</Tag>
                    <div>
                      <strong>{event.visit_code || `D${event.study_day}`} · {event.title}</strong>
                      <span>{event.detail}</span>
                    </div>
                  </div>
                )) : <p className="quiet-text">当前受试者暂无 PD / Query 时间线事件。</p>}
              </div>
            </div>
          </ProfilePanel>

          <section className="profile-two-col">
            <ProfilePanel title="风险提示" eyebrow="Risk">
              <div className="risk-list profile-risk-prompts">
                {prompts.length ? prompts.map((prompt) => (
                  <p key={prompt.prompt_id || prompt.title}>
                    <AlertTriangle size={14} />
                    <span><strong>{prompt.visit_code}</strong> {prompt.title}：{prompt.prompt_text || prompt.recommended_action}</span>
                  </p>
                )) : subject.risks.map((risk) => <p key={risk}><AlertTriangle size={14} /> {risk}</p>)}
              </div>
              {subject.reviewFocus?.length > 0 && (
                <div className="profile-review-focus">
                  {subject.reviewFocus.map((item) => <p key={item}>{item}</p>)}
                </div>
              )}
            </ProfilePanel>
            <ProfilePanel title="关联事件索引" eyebrow="Source Events">
              <div className="profile-event-index">
                {nonVisitEvents.slice(0, 12).map((event) => (
                  <div key={event.event_id}>
                    <Tag tone={event.related_risk_ids?.length ? "warning" : "info"}>{event.source_domain}</Tag>
                    <span>{event.visit_code || `D${event.study_day}`} · {event.title}</span>
                  </div>
                ))}
                {!nonVisitEvents.length && <p className="quiet-text">当前暂无可索引事件。</p>}
              </div>
            </ProfilePanel>
          </section>
        </section>
      </div>
    </main>
  );
}

function EligibilityPage() {
  const [dataset, setDataset] = useState(null);
  const [rawIntake, setRawIntake] = useState(null);
  const [query, setQuery] = useState({ subjectId: "", phaseId: "" });
  const [search, setSearch] = useState("");
  const [loading, setLoading] = useState(false);
  const [rawLoading, setRawLoading] = useState(false);
  const [error, setError] = useState("");
  const [rawError, setRawError] = useState("");

  useEffect(() => {
    let cancelled = false;
    const params = new URLSearchParams();
    if (query.subjectId) params.set("subject_id", query.subjectId);
    if (query.phaseId) params.set("phase_id", query.phaseId);
    setLoading(true);
    setError("");
    fetch(`/api/projects/${PROJECT_ID}/eligibility${params.toString() ? `?${params.toString()}` : ""}`)
      .then((response) => (response.ok ? response.json() : Promise.reject(response)))
      .then((data) => {
        if (!cancelled) setDataset(data);
      })
      .catch((response) => {
        if (!cancelled) setError(`入排审核数据读取失败：${response.status || "network"}`);
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [query.subjectId, query.phaseId]);

  useEffect(() => {
    let cancelled = false;
    setRawLoading(true);
    setRawError("");
    fetch(`/api/projects/${RAW_ELIGIBILITY_PROJECT_ID}/eligibility/raw-intake`)
      .then((response) => (response.ok ? response.json() : Promise.reject(response)))
      .then((data) => {
        if (!cancelled) setRawIntake(data);
      })
      .catch((response) => {
        if (!cancelled) setRawError(`原始资料池读取失败：${response.status || "network"}`);
      })
      .finally(() => {
        if (!cancelled) setRawLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, []);

  const legacyDataset = dataset;
  const rawTaskPlan = rawIntake?.ai_task_plan || [];
  const rawForbiddenInputs = rawIntake?.forbidden_legacy_inputs || [];
  const rawAiStatuses = rawIntake?.ai_task_plan?.map((task) => task.status) || [];
  const rawAiBlocked = rawAiStatuses.some((status) => status === "blocked_external_ai_not_configured");
  const rawSourceTypes = rawIntake?.subject_pool?.source_type_counts || {};
  const rawSourceTypeLabel = Object.entries(rawSourceTypes)
    .map(([key, value]) => `${key} ${value}`)
    .join(" / ");
  const rawProtocolRulesReady = rawTaskPlan.some((task) => task.task_type === "protocol_rule_extraction" && task.status === "completed");
  const rawEligibilityReviewReady = rawTaskPlan.some((task) => task.task_type === "eligibility_rule_review" && task.status === "completed");
  const phases = [];
  const activePhaseId = "";
  const subjectRows = [];
  const filteredRows = [];
  const selected = null;
  const ruleReviews = [];
  const passVerifyRules = [];
  const evidenceRows = [];
  const actionItems = [];

  return (
    <main className="page">
      <SectionTitle
        eyebrow="入排审核"
        title="项目期别、受试者审核节点与逐条规则复核"
        action={<button className="primary-button">导出审核报告</button>}
      />
      <section className="eligibility-status panel">
        <div>
          <strong>{rawIntake?.project_label || "CMS-D001 原始入排资料池"}</strong>
          <span>{rawIntake ? `${rawIntake.protocol?.filename || "方案文件"} · ${rawIntake.source_system}` : "读取原始入排资料中"}</span>
        </div>
        <div>
          <strong>{rawIntake?.subject_pool?.unique_subject_count ?? "-"} 名受试者</strong>
          <span>原始文件 {rawIntake?.subject_pool?.total_files ?? "-"} · 待 OCR/VLM {rawIntake?.subject_pool?.needs_ocr_vlm_count ?? "-"}</span>
        </div>
        <div>
          <strong>{rawProtocolRulesReady ? "规则已生成" : "IN/EX 规则待生成"}</strong>
          <span>必须从当前方案抽取原始编号，不复用 legacy 规则树</span>
        </div>
        <div>
          <strong>{rawEligibilityReviewReady ? "逐条审核已生成" : "逐条审核待生成"}</strong>
          <span>生成后仍需医学确认，当前不输出正式入排结论</span>
        </div>
      </section>

      <section className="eligibility-raw-intake panel">
        <div className="raw-intake-head">
          <div>
            <span>原始资料链路</span>
            <strong>{rawIntake?.project_label || "D001 原始入排资料池"}</strong>
          </div>
          <Tag tone={rawLoading ? "warning" : rawAiBlocked ? "warning" : "success"}>
            {rawLoading ? "读取中" : rawAiBlocked ? "外部AI待配置" : "外部AI已配置"}
          </Tag>
        </div>
        <div className="raw-intake-grid">
          <div>
            <strong>{rawIntake?.subject_pool?.unique_subject_count ?? "-"} 名</strong>
            <span>从原始资料识别的受试者</span>
          </div>
          <div>
            <strong>{rawIntake?.subject_pool?.total_files ?? "-"} 份</strong>
            <span>原始文件；{rawIntake?.subject_pool?.needs_ocr_vlm_count ?? "-"} 份待 OCR/VLM</span>
          </div>
          <div>
            <strong>{rawIntake?.protocol?.paragraph_count ?? "-"} 段</strong>
            <span>方案文本结构，待抽取 IN/EX 规则</span>
          </div>
          <div>
            <strong>{rawIntake?.forbidden_legacy_inputs?.length ?? "-"} 类</strong>
            <span>旧产物禁用：只作历史 QC，不作本轮输入</span>
          </div>
        </div>
        <p>
          {rawError || `源类型：${rawSourceTypeLabel || "待读取"}。当前仅展示 raw-source 发现与任务计划，逐条入排结论需外部 AI、OCR/VLM 和医学确认后生成。`}
        </p>
      </section>

      <section className="panel eligibility-controls">
        <div className="phase-tabs" aria-label="原始资料任务">
          {rawTaskPlan.length ? rawTaskPlan.map((task) => (
            <button key={task.task_type} className={task.status === "completed" ? "active" : ""}>
              <strong>{task.task_type === "protocol_rule_extraction" ? "方案规则抽取" : "逐例规则审核"}</strong>
              <span>{task.status === "blocked_external_ai_not_configured" ? "外部AI待配置" : task.status}</span>
            </button>
          )) : (
            <button>
              <strong>原始资料发现</strong>
              <span>{rawLoading ? "读取中" : "等待任务计划"}</span>
            </button>
          )}
        </div>
        <div className="search-row">
          <Search size={16} />
          <input value={search} onChange={(event) => setSearch(event.target.value)} placeholder="搜索 raw source 摘要或任务状态" />
        </div>
      </section>

      {error && <section className="panel gate-error">{error}</section>}

      <div className="eligibility-workbench">
        <section className="panel eligibility-subjects-panel">
          <SectionTitle
            title="候选受试者池（原始资料发现）"
            action={<Tag tone={rawLoading ? "warning" : "info"}>{rawLoading ? "读取中" : `${rawIntake?.subject_pool?.unique_subject_count ?? 0} 名`}</Tag>}
          />
          <div className="raw-subject-summary">
            <div><strong>{rawIntake?.subject_pool?.unique_subject_count ?? "-"}</strong><span>唯一受试者</span></div>
            <div><strong>{rawIntake?.subject_pool?.total_files ?? "-"}</strong><span>原始文件</span></div>
            <div><strong>{rawIntake?.subject_pool?.source_type_counts?.pdf ?? 0}</strong><span>PDF</span></div>
            <div><strong>{rawIntake?.subject_pool?.source_type_counts?.image ?? 0}</strong><span>图像</span></div>
            <div><strong>{(rawIntake?.subject_pool?.subject_id_prefixes || []).join(" / ") || "-"}</strong><span>受试者编号前缀</span></div>
          </div>
          <div className="eligibility-table-wrap">
            <table className="eligibility-subject-table">
              <thead>
                <tr>
                  <th>受试者</th>
                  <th>中心</th>
                  <th>ICF日期</th>
                  <th>资料数</th>
                  <th>总体结论</th>
                  {phases.map((phase) => <th key={phase.phase_id}>{phase.name}</th>)}
                </tr>
              </thead>
              <tbody>
                {filteredRows.map((row) => (
                  <tr key={row.subject_id} className={selected?.subject_id === row.subject_id ? "selected" : ""}>
                    <td>
                      <button
                        className="subject-link"
                        onClick={() => setQuery((current) => ({ ...current, subjectId: row.subject_id }))}
                      >
                        {row.subject_id}
                      </button>
                    </td>
                    <td><span>{row.center_name || row.center_code || "-"}</span></td>
                    <td>{row.icf_date || "-"}</td>
                    <td>{row.doc_count}</td>
                    <td><Tag tone={verdictTone(row.overall_verdict)}>{verdictLabel(row.overall_verdict)}</Tag></td>
                    {phases.map((phase) => {
                      const phaseReview = row.phase_reviews?.[phase.phase_id] || {};
                      return (
                        <td key={`${row.subject_id}-${phase.phase_id}`}>
                          <button
                            className={`phase-cell ${activePhaseId === phase.phase_id && selected?.subject_id === row.subject_id ? "active" : ""}`}
                            onClick={() => setQuery({ subjectId: row.subject_id, phaseId: phase.phase_id })}
                          >
                            <Tag tone={verdictTone(phaseReview.verdict)}>{verdictLabel(phaseReview.verdict)}</Tag>
                            <span>{phaseReview.has_report ? "报告已生成" : candidateStatusLabel(phaseReview.status)}</span>
                          </button>
                        </td>
                      );
                    })}
                  </tr>
                ))}
                {!filteredRows.length && (
                  <tr>
                    <td colSpan={5}>
                      <div className="raw-pending-state">
                        已完成原始资料池发现；逐例候选清单、IN/EX规则匹配和医学结论需在外部AI/OCR/VLM链路生成后展示。当前不使用 legacy MG-K10 结果填充本项目主体。
                      </div>
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </section>

        <section className="panel eligibility-review-panel">
          <SectionTitle title={selected ? `${selected.subject_id} ${selected.active_phase_label} 审核报告` : "逐条入排审核待生成"} />
          {selected ? (
            <>
              <div className="verdict-strip eligibility-verdict">
                <Tag tone={verdictTone(selected.overall_conclusion)}>{verdictLabel(selected.overall_conclusion)}</Tag>
                <strong>{selected.active_phase_label}</strong>
                <span>中心 {selected.site_id || "-"} · 资料 {selected.document_count} 份 · 状态 {candidateStatusLabel(selected.status)}</span>
                <span>节点总判定：{verdictLabel(selected.overall_rationale)}</span>
              </div>
              <div className="report-grid eligibility-report-grid">
                <div><strong>待补充资料</strong><span>{selected.missing_information?.length || 0} 项</span></div>
                <div><strong>需医学确认</strong><span>{selected.medical_confirmation_items?.length || 0} 项</span></div>
                <div><strong>溯源提醒</strong><span>{passVerifyRules.length} 条 pass_verify</span></div>
                <div><strong>报告来源</strong><span>{shortPath(ruleReviews[0]?.source_report_path) || "未生成"}</span></div>
              </div>
              <div className="rule-review-table-wrap">
                <table className="rule-review-table">
                  <thead>
                    <tr>
                      <th>规则ID</th>
                      <th>标准名称</th>
                      <th>类别</th>
                      <th>结论</th>
                      <th>医学理由 / 证据摘要</th>
                      <th>提醒类型</th>
                    </tr>
                  </thead>
                  <tbody>
                    {ruleReviews.map((rule) => (
                      <tr key={rule.rule_id}>
                        <td><strong>{rule.rule_id}</strong></td>
                        <td>{rule.rule_label}</td>
                        <td>{ruleTypeLabel(rule.rule_type)}</td>
                        <td><Tag tone={verdictTone(rule.verdict)}>{rule.verdict_label || verdictLabel(rule.verdict)}</Tag></td>
                        <td>{rule.rationale || "无补充说明"}</td>
                        <td>{rule.verification_type ? verdictLabel(rule.verdict) : "-"}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </>
          ) : (
            <div className="empty-state raw-pending-state">
              已识别当前项目原始方案和受试者资料池，但尚未生成基于本项目方案 IN/EX 编号的逐条审核结果。下一步需完成方案规则抽取、OCR/VLM证据抽取、外部AI审核和医学确认后，再进入正式候选结论。
            </div>
          )}
        </section>

        <aside className="eligibility-side">
          <section className="panel rule-tree">
            <SectionTitle title="当前方案规则抽取任务" />
            <div className="criteria-list">
              {rawTaskPlan.map((task, index) => (
                <div className="criteria-row" key={task.task_type}>
                  <Tag tone={task.status === "completed" ? "success" : "warning"}>{index + 1}</Tag>
                  <div>
                    <strong>{task.task_type === "protocol_rule_extraction" ? "方案 IN/EX 规则抽取" : "逐例入排规则审核"}</strong>
                    <span>{task.input_source_scopes?.join("；") || task.status}</span>
                  </div>
                </div>
              ))}
              {!rawTaskPlan.length && <p className="quiet-text">等待原始资料任务计划生成。</p>}
            </div>
          </section>
          <section className="panel evidence-tree">
            <SectionTitle title="证据与边界" />
            <div className="action-list">
              {rawForbiddenInputs.length ? rawForbiddenInputs.slice(0, 6).map((item) => (
                <div className="action-item" key={item}>
                  <AlertTriangle size={15} />
                  <div>
                    <strong>禁用旧产物输入</strong>
                    <span>{item}</span>
                  </div>
                </div>
              )) : <p className="quiet-text">当前未登记禁用旧产物。</p>}
            </div>
            <div className="evidence-list">
              {evidenceRows.map((evidence) => (
                <div className="evidence-node" key={evidence.evidence_id}>
                  <FileText size={16} />
                  <div>
                    <strong>{evidence.rule_id} · {evidence.source_title}</strong>
                    <span>{evidence.quote || evidence.ruleLabel}</span>
                  </div>
                </div>
              ))}
              {!evidenceRows.length && <p className="quiet-text">当前项目 raw 证据节点待 OCR/VLM 和规则审核生成；legacy 证据不得作为本项目输入。</p>}
            </div>
            <div className="audit-box legacy-comparison">
              <strong>历史对照（legacy comparison）</strong>
              <span>{legacyDataset?.source_project_code || "旧系统对照未读取"} · {legacyDataset?.source_system || "只作迁移参考"}</span>
              <span>不得用于当前 D001/MY009 原始资料审核输入。</span>
            </div>
          </section>
        </aside>
      </div>
    </main>
  );
}

const writingSectionBackendIds = {
  synopsis: "sec_synopsis",
  endpoints: "sec_objectives_endpoints",
  eligibility: "sec_eligibility",
  soa: "sec_soa",
};

const revisionIntentOptions = [
  { value: "regulatory_tone", label: "监管语气" },
  { value: "evidence_gap", label: "补证据" },
  { value: "consistency_check", label: "查一致性" },
  { value: "medical_writing_revision", label: "改写" },
];

function writingBackendSectionId(sectionId) {
  return writingSectionBackendIds[sectionId] || null;
}

function revisionThreadStatusLabel(status) {
  return {
    pending_medical_approval: "待医学批准",
    accepted_pending_medical_approval: "已接受，仍待医学批准",
    rejected: "已拒绝",
  }[status] || status || "待处理";
}

function revisionThreadTone(status) {
  if (status === "accepted_pending_medical_approval") return "warning";
  if (status === "rejected") return "neutral";
  return "info";
}

function latestPendingSuggestion(thread) {
  return [...(thread?.suggestions || [])].reverse().find((item) => item.user_decision === "pending") || thread?.suggestions?.[thread.suggestions.length - 1] || null;
}

function RichProtocolEditor({ section, approvedLocked, selectedSection, onSelectedTextChange, onEditorTextChange }) {
  const editor = useEditor({
    extensions: [
      StarterKit,
      Table.configure({ resizable: true }),
      TableRow,
      TableHeader,
      TableCell,
    ],
    editable: !approvedLocked,
    content: `
      <h2>${selectedSection === "synopsis" ? "1.1 方案概要" : "3.2 研究目的与终点"}</h2>
      <p>主要疗效终点为治疗期预设关键评估时间点 rTNSS 总分较基线的变化，具体分析时间窗和缺失数据处理方法将在统计学章节及 SAP 中进一步规定。</p>
      <table>
        <tbody>
          <tr><th>终点类型</th><th>终点名称</th><th>时间窗</th><th>分析集</th><th>证据状态</th></tr>
          <tr><td>主要</td><td>rTNSS 较基线变化</td><td>治疗期关键时间窗</td><td>ITT</td><td>待补竞品依据</td></tr>
          <tr><td>次要</td><td>iTNSS 较基线变化</td><td>W1-W4</td><td>ITT</td><td>已有方案模板</td></tr>
        </tbody>
      </table>
    `,
    onCreate: ({ editor }) => {
      onEditorTextChange?.(editor.getText().trim());
    },
    onUpdate: ({ editor }) => {
      onEditorTextChange?.(editor.getText().trim());
    },
    onSelectionUpdate: ({ editor }) => {
      const { from, to } = editor.state.selection;
      const selectedText = from === to ? "" : editor.state.doc.textBetween(from, to, " ").trim();
      onSelectedTextChange?.(selectedText);
    },
  });

  const toolbar = [
    { label: "H1", icon: Heading1, active: editor?.isActive("heading", { level: 2 }), run: () => editor?.chain().focus().toggleHeading({ level: 2 }).run() },
    { label: "B", icon: Bold, active: editor?.isActive("bold"), run: () => editor?.chain().focus().toggleBold().run() },
    { label: "I", icon: Italic, active: editor?.isActive("italic"), run: () => editor?.chain().focus().toggleItalic().run() },
    { label: "列表", icon: List, active: editor?.isActive("bulletList"), run: () => editor?.chain().focus().toggleBulletList().run() },
    { label: "编号", icon: ListOrdered, active: editor?.isActive("orderedList"), run: () => editor?.chain().focus().toggleOrderedList().run() },
  ];

  return (
    <div className="rich-editor-shell">
      <div className="rich-editor-meta">
        <span>组件类型：Endpoint</span>
        <span>当前章节：{section.title}</span>
        <span>证据覆盖 {section.coverage}%</span>
      </div>
      <div className="rich-toolbar">
        {toolbar.map((item) => {
          const Icon = item.icon;
          return (
            <button key={item.label} className={item.active ? "active" : ""} disabled={approvedLocked || !editor} onClick={item.run} title={item.label}>
              <Icon size={15} />
            </button>
          );
        })}
      </div>
      <EditorContent editor={editor} className="protocol-editor" />
    </div>
  );
}

function MedicalWritingManifestPanel({
  manifest,
  loading,
  message,
  onRefresh,
  selectedPackageId,
  onSelectPackage,
  tflCitations,
  tflCitationLoading,
  tflCitationMessage,
  onRefreshTflCitations,
}) {
  const packages = manifest?.packages || [];
  const selectedPackage = packages.find((item) => item.package_id === selectedPackageId) || packages[0];
  const documents = selectedPackage?.documents || [];
  const sections = selectedPackage ? selectedPackage.sections.slice(0, 12) : [];
  const tables = selectedPackage ? selectedPackage.tables.slice(0, 12) : [];
  const gates = selectedPackage?.quality_gates || [];
  const citationCandidates = tflCitations?.candidates || [];
  const citationGates = tflCitations?.quality_gates || [];
  const warnings = selectedPackage?.parser_warnings?.slice(0, 5) || [];
  const blockedCount = gates.filter((gate) => ["blocked", "blocker"].includes(gate.status)).length;
  const warningCount = gates.filter((gate) => gate.status === "warning").length;

  return (
    <section className="panel tfl-manifest-panel writing-manifest-panel">
      <SectionTitle
        title="研究方案写作资料包"
        action={<button onClick={onRefresh} disabled={loading}>{loading ? "生成中" : "刷新资料包"}</button>}
      />
      <div className="writing-boundary">
        当前仅展示真实DOCX来源、章节/表格候选、来源定位和质量门；AI修订建议均为待医学批准的正式内容候选，不替代医学审阅、医学批准或正式导出检查。
      </div>
      <div className="writing-manifest-stats">
        <div><strong>{formatMaybeNumber(manifest?.package_count)}</strong><span>真实资料包</span></div>
        <div><strong>{formatMaybeNumber(manifest?.total_documents)}</strong><span>源文档</span></div>
        <div><strong>{formatMaybeNumber(manifest?.total_sections)}</strong><span>章节候选</span></div>
        <div><strong>{formatMaybeNumber(manifest?.total_tables)}</strong><span>表格候选</span></div>
        <div><strong>{formatMaybeNumber(manifest?.total_source_spans)}</strong><span>source spans</span></div>
        <div className={blockedCount ? "warning" : ""}><strong>{blockedCount}</strong><span>阻断质量门</span></div>
      </div>
      {message && <div className="source-registry-message">{message}</div>}
      <div className="tfl-package-tabs">
        {packages.map((item) => (
          <button
            key={item.package_id}
            className={item.package_id === selectedPackage?.package_id ? "active" : ""}
            onClick={() => onSelectPackage(item.package_id)}
          >
            {item.package_label}
          </button>
        ))}
      </div>
      {selectedPackage ? (
        <>
          <div className="tfl-package-summary writing-package-summary">
            <div><span>项目</span><strong>{selectedPackage.project_code}</strong></div>
            <div><span>适应症</span><strong>{selectedPackage.indication}</strong></div>
            <div><span>资料底座</span><strong>{selectedPackage.source_root_label}</strong></div>
            <div><span>证据覆盖</span><strong>{selectedPackage.evidence_coverage_percent}%：覆盖率不代表医学批准</strong></div>
            <div><span>导出准备</span><strong>{selectedPackage.can_generate_review_docx ? "可生成审阅版 DOCX" : "不可生成审阅版 DOCX"} / {selectedPackage.formal_export_status}</strong></div>
          </div>
          <div className="tfl-quality-gates writing-quality-tags">
            <Tag tone="warning">待医学批准内容候选</Tag>
            <Tag tone={documents.length ? "success" : "danger"}>{documents.length ? "正文已解析" : "仅文件级登记"}</Tag>
            <Tag tone={blockedCount ? "danger" : "success"}>阻断 {blockedCount}</Tag>
            <Tag tone={warningCount ? "warning" : "success"}>待确认 {warningCount}</Tag>
            <Tag tone="neutral">独立AI边界</Tag>
          </div>
          {warnings.length ? (
            <div className="tfl-warning-list">
              {warnings.map((warning) => <span key={warning}>{warning}</span>)}
            </div>
          ) : null}
          <div className="tfl-note-list">
            <span>{selectedPackage.ai_revision_boundary}</span>
            {(manifest.parser_notes || []).slice(0, 3).map((note) => <span key={note}>{note}</span>)}
          </div>

          <div className="writing-citation-panel">
            <SectionTitle
              title="TFL写作引用候选"
              action={<button onClick={onRefreshTflCitations} disabled={tflCitationLoading}>{tflCitationLoading ? "读取中" : "刷新引用候选"}</button>}
            />
            <div className="writing-citation-boundary">
              来自数据分析与TFL的审阅处置记录。{tflCitations?.formal_output_boundary || "当前仅汇总TFL写作引用候选，不自动生成或改写正式医学写作正文。"}
            </div>
            {tflCitationMessage && <div className="source-registry-message">{tflCitationMessage}</div>}
            <div className="writing-citation-stats">
              <div><strong>{tflCitations?.total_candidates || 0}</strong><span>引用候选</span></div>
              <div><strong>{citationGates.filter((gate) => gate.status === "passed").length}</strong><span>通过质量门</span></div>
              <div><strong>{citationGates.filter((gate) => gate.status !== "passed").length}</strong><span>待确认质量门</span></div>
            </div>
            <div className="writing-citation-gates">
              {citationGates.map((gate) => (
                <div key={gate.gate_id}>
                  <Tag tone={safetyGateTone(gate.status)}>{gateStatusLabel(gate.status)}</Tag>
                  <strong>{gate.gate_label}</strong>
                  <span>{gate.detail}</span>
                </div>
              ))}
            </div>
            <div className="writing-citation-list">
              {citationCandidates.length ? citationCandidates.slice(0, 8).map((candidate) => (
                <article key={candidate.candidate_id}>
                  <div className="writing-citation-head">
                    <div>
                      <strong>{candidate.output_display_id}</strong>
                      <span>{tflOutputTypeLabel(candidate.output_type)} / {candidate.domain_hint || "领域待确认"} · {candidate.package_label}</span>
                    </div>
                    <Tag tone="warning">待医学确认</Tag>
                  </div>
                  <div className="writing-citation-meta">
                    <div><span>配对数据集</span><strong>{candidate.paired_dataset_name || "未配对"} {candidate.paired_dataset_row_count !== null && candidate.paired_dataset_row_count !== undefined ? `(${formatMaybeNumber(candidate.paired_dataset_row_count)}行)` : ""}</strong></div>
                    <div><span>建议章节</span><strong>{candidate.recommended_writing_sections.slice(0, 3).join(" / ")}</strong></div>
                    <div><span>审阅人</span><strong>{candidate.reviewer}</strong></div>
                  </div>
                  <p>{candidate.review_comment}</p>
                  <span className="writing-citation-boundary-line">{candidate.citation_boundary}</span>
                </article>
              )) : <div className="empty-state">暂无来自数据分析与TFL的写作引用候选。请先在TFL审阅工作台标记写作引用候选。</div>}
            </div>
          </div>

          <div className="tfl-manifest-grid writing-doc-grid">
            <div className="tfl-table-block">
              <h3>源文档</h3>
              <div className="tfl-table-scroll writing-doc-table">
                <table>
                  <thead>
                    <tr>
                      <th>文档</th>
                      <th>方案号/版本</th>
                      <th>解析</th>
                      <th>段落/表格/span</th>
                      <th>Word特征</th>
                    </tr>
                  </thead>
                  <tbody>
                    {documents.map((document) => (
                      <tr key={document.document_id}>
                        <td><strong>{document.public_title}</strong><span>{document.relative_path}</span></td>
                        <td>{document.protocol_identifier}<span>{document.protocol_version} / {document.protocol_date}</span></td>
                        <td><Tag tone={document.parser_status === "正文已解析" ? "success" : "warning"}>{document.parser_status}</Tag></td>
                        <td>{document.paragraph_count} / {document.table_count} / {document.span_count}</td>
                        <td>{document.image_count} 图像；{document.has_revision_marks ? "有修订痕迹" : "无修订痕迹"}；{document.has_fields ? "有字段" : "无字段"}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
            <div className="tfl-table-block">
              <h3>写作质量门</h3>
              <div className="tfl-table-scroll writing-gate-table">
                <table>
                  <thead>
                    <tr>
                      <th>质量门</th>
                      <th>状态</th>
                      <th>负责角色</th>
                      <th>说明</th>
                      <th>来源</th>
                    </tr>
                  </thead>
                  <tbody>
                    {gates.map((gate) => (
                      <tr key={gate.gate_id}>
                        <td><strong>{gate.gate_label}</strong></td>
                        <td><Tag tone={safetyGateTone(gate.status)}>{gateStatusLabel(gate.status)}</Tag></td>
                        <td>{gate.owner}</td>
                        <td>{gate.detail}</td>
                        <td>{gate.source_refs.slice(0, 3).join("；") || "待补来源定位"}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </div>

          <div className="tfl-table-block writing-wide-block">
            <h3>方案章节候选</h3>
            <div className="tfl-table-scroll writing-section-table">
              <table>
                <thead>
                  <tr>
                    <th>章节</th>
                    <th>ICH M11锚点</th>
                    <th>状态</th>
                    <th>来源定位</th>
                    <th>段落/表格</th>
                    <th>证据覆盖</th>
                    <th>映射置信度</th>
                    <th>AI任务</th>
                  </tr>
                </thead>
                <tbody>
                  {sections.map((section) => (
                    <tr key={section.section_id}>
                      <td><strong>{section.section_number ? `${section.section_number} ${section.heading}` : section.heading}</strong><span>{section.anchor_path}</span></td>
                      <td>{section.ich_m11_area || "待人工映射"}</td>
                      <td>{section.writing_status}<span>{section.medical_approval_status}</span></td>
                      <td>{section.source_locator}</td>
                      <td>{section.paragraph_count} / {section.table_count}</td>
                      <td>{section.evidence_coverage_percent}%<span>{section.evidence_status}</span></td>
                      <td>{Math.round(section.extraction_confidence * 100)}%<span>{section.requires_human_mapping ? "需人工确认" : "已确认"}</span></td>
                      <td>{section.ai_task_ready ? "可准备AI任务" : "待确认后准备"}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          <div className="tfl-table-block writing-wide-block">
            <h3>表格与来源定位</h3>
            <div className="tfl-table-scroll writing-table-inventory">
              <table>
                <thead>
                  <tr>
                    <th>表格</th>
                    <th>角色候选</th>
                    <th>行/列/非空单元</th>
                    <th>表头线索</th>
                    <th>来源定位</th>
                    <th>结构风险</th>
                    <th>解析状态</th>
                  </tr>
                </thead>
                <tbody>
                  {tables.map((table) => (
                    <tr key={table.table_id}>
                      <td><strong>Table {table.table_index}</strong><span>{table.title_hint}</span></td>
                      <td>{table.role_hint}</td>
                      <td>{table.row_count} / {table.column_count} / {table.nonempty_cell_count}</td>
                      <td>{table.headers.slice(0, 4).join("；") || "待抽取"}</td>
                      <td>{table.source_locator}</td>
                      <td>{table.quality_notes.slice(0, 2).join("；") || "无开放提示"}</td>
                      <td>{parserStatusDisplay(table.parser_status)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </>
      ) : (
        <div className="empty-state">尚未生成研究方案写作资料包。</div>
      )}
    </section>
  );
}

function WritingPage() {
  const [selectedSection, setSelectedSection] = useState("endpoints");
  const [writingManifest, setWritingManifest] = useState(null);
  const [manifestLoading, setManifestLoading] = useState(false);
  const [manifestMessage, setManifestMessage] = useState("");
  const [selectedPackageId, setSelectedPackageId] = useState("");
  const [tflCitations, setTflCitations] = useState(null);
  const [tflCitationLoading, setTflCitationLoading] = useState(false);
  const [tflCitationMessage, setTflCitationMessage] = useState("");
  const [revisionThreads, setRevisionThreads] = useState([]);
  const [revisionLoading, setRevisionLoading] = useState(false);
  const [revisionMessage, setRevisionMessage] = useState("");
  const [revisionInstruction, setRevisionInstruction] = useState("请将选中文本改写为更符合研究方案正文的医学写作表述，并指出仍需补充的证据。");
  const [revisionIntent, setRevisionIntent] = useState("regulatory_tone");
  const [selectedEditorText, setSelectedEditorText] = useState("");
  const [editorPlainText, setEditorPlainText] = useState("");
  const [activeRevisionThreadId, setActiveRevisionThreadId] = useState("");
  const [revisionActionComment, setRevisionActionComment] = useState("");
  const [revisionRewriteInstruction, setRevisionRewriteInstruction] = useState("请保留原终点名称，并补充与SAP时间窗定义衔接的保守表述。");
  const section = writingSections.find((item) => item.id === selectedSection) || writingSections[0];
  const approvedLocked = section.status === "已批准";
  const backendSectionId = writingBackendSectionId(selectedSection);
  const sectionHasBackendBinding = Boolean(backendSectionId);
  const aiRevisionDisabled = approvedLocked || !sectionHasBackendBinding;
  const refreshWritingManifest = () => {
    setManifestLoading(true);
    setManifestMessage("");
    fetch(`/api/projects/${PROJECT_ID}/medical-writing/manifest`)
      .then((response) => (response.ok ? response.json() : Promise.reject(response)))
      .then((payload) => {
        setWritingManifest(payload);
        const packageIds = (payload.packages || []).map((item) => item.package_id);
        if (!packageIds.includes(selectedPackageId)) setSelectedPackageId(packageIds[0] || "");
      })
      .catch((error) => setManifestMessage(`研究方案写作资料包生成失败：${error.status || error.message || "network"}`))
      .finally(() => setManifestLoading(false));
  };
  useEffect(() => {
    refreshWritingManifest();
  }, []);
  const refreshTflCitations = () => {
    setTflCitationLoading(true);
    setTflCitationMessage("");
    fetch(`/api/projects/${PROJECT_ID}/medical-writing/tfl-citation-candidates`)
      .then((response) => (response.ok ? response.json() : Promise.reject(response)))
      .then((payload) => setTflCitations(payload))
      .catch((error) => setTflCitationMessage(`TFL写作引用候选读取失败：${error.status || error.message || "network"}`))
      .finally(() => setTflCitationLoading(false));
  };
  useEffect(() => {
    refreshTflCitations();
  }, []);
  const refreshRevisionThreads = () => {
    setRevisionLoading(true);
    setRevisionMessage("");
    fetch(`/api/projects/${PROJECT_ID}/revision-threads`)
      .then(readJsonOrThrow)
      .then((payload) => {
        const threads = Array.isArray(payload) ? payload : [];
        setRevisionThreads(threads);
        if (!threads.some((thread) => thread.thread_id === activeRevisionThreadId)) {
          setActiveRevisionThreadId(threads[threads.length - 1]?.thread_id || "");
        }
      })
      .catch((error) => setRevisionMessage(`AI修订线程读取失败：${apiErrorText(error)}`))
      .finally(() => setRevisionLoading(false));
  };
  useEffect(() => {
    refreshRevisionThreads();
  }, []);
  useEffect(() => {
    setSelectedEditorText("");
  }, [selectedSection]);
  const submitRevisionRequest = () => {
    const selected_text = (selectedEditorText || editorPlainText || section.title).trim();
    if (!sectionHasBackendBinding) {
      setRevisionMessage("当前章节暂无后端章节绑定，不能提交AI修订，避免错误写入其他章节。");
      return;
    }
    if (!revisionInstruction.trim() || approvedLocked || !selected_text) return;
    setRevisionLoading(true);
    setRevisionMessage("");
    fetch(`/api/projects/${PROJECT_ID}/revision-threads`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        section_id: backendSectionId,
        anchor_type: selectedEditorText ? "selection" : "section",
        anchor_path: `sections.${backendSectionId}.editor.${selectedEditorText ? "selection" : "body"}`,
        selected_text,
        user_instruction: revisionInstruction.trim(),
        intent: revisionIntent,
        requested_by: "medical_manager",
      }),
    })
      .then(readJsonOrThrow)
      .then((payload) => {
        setRevisionThreads((previous) => [...previous.filter((thread) => thread.thread_id !== payload.thread.thread_id), payload.thread]);
        setActiveRevisionThreadId(payload.thread.thread_id);
        setRevisionActionComment("");
        setRevisionMessage("AI修订建议已生成，当前为待医学批准内容候选，不自动写入正式正文。");
      })
      .catch((error) => setRevisionMessage(`AI修订提交失败：${apiErrorText(error)}`))
      .finally(() => setRevisionLoading(false));
  };
  const submitRevisionAction = (thread, action) => {
    const suggestion = latestPendingSuggestion(thread);
    if (!thread || !suggestion || revisionLoading) return;
    setRevisionLoading(true);
    setRevisionMessage("");
    fetch(`/api/projects/${PROJECT_ID}/revision-threads/${thread.thread_id}/actions`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        action,
        suggestion_id: suggestion.suggestion_id,
        actor: "medical_manager",
        comment: revisionActionComment,
        rewrite_instruction: action === "request_rewrite" ? revisionRewriteInstruction : "",
      }),
    })
      .then(readJsonOrThrow)
      .then((payload) => {
        setRevisionThreads((previous) => previous.map((item) => (item.thread_id === payload.thread.thread_id ? payload.thread : item)));
        setActiveRevisionThreadId(payload.thread.thread_id);
        setRevisionMessage(action === "accept"
          ? "已接受，仍待医学批准；该建议不自动写入正式正文。"
          : action === "reject"
            ? "已拒绝该建议并写入审计。"
            : "已要求重写并生成新的待医学批准建议。");
      })
      .catch((error) => setRevisionMessage(`修订处置失败：${apiErrorText(error)}`))
      .finally(() => setRevisionLoading(false));
  };
  const activePackage = (writingManifest?.packages || []).find((item) => item.package_id === selectedPackageId) || writingManifest?.packages?.[0];
  const writingBlocked = !activePackage || activePackage.blocking_gate_count > 0;
  const sectionThreads = sectionHasBackendBinding ? revisionThreads.filter((thread) => thread.section_id === backendSectionId) : [];
  const activeThread = sectionHasBackendBinding
    ? sectionThreads.find((thread) => thread.thread_id === activeRevisionThreadId)
      || [...sectionThreads].reverse().find((thread) => thread.status === "pending_medical_approval")
      || sectionThreads[sectionThreads.length - 1]
    : null;
  const activeSuggestion = latestPendingSuggestion(activeThread);
  const revisionBoundary = "AI修订建议仅为待医学批准内容候选；接受为候选后仍不自动写入正式正文。";
  return (
    <main className="page writing-page">
      <SectionTitle
        eyebrow="医学写作"
        title="研究方案文档编辑与AI修订"
        action={<button className="primary-button" disabled={writingBlocked}>{writingBlocked ? "质量门阻断" : "提交审批"}</button>}
      />
      <div className="writing-layout writing-editor-first-layout">
        <section className="panel editor-panel writing-editor-core">
          <div className="editor-toolbar">
            {[
              ["改写", "请将选中文本改写为更符合研究方案正文的医学写作表述，并保留医学保守性。", "medical_writing_revision"],
              ["补证据", "请指出该表述仍需补充的方案、SAP、指导原则或竞品证据。", "evidence_gap"],
              ["查一致性", "请检查该表述与终点、分析集、SAP时间窗和入排标准是否存在不一致。", "consistency_check"],
              ["监管语气", "请将该表述改为更符合临床研究方案正文和监管沟通语气的写法。", "regulatory_tone"],
              ["压缩", "请在不改变医学含义的前提下压缩该表述。", "medical_writing_revision"],
              ["扩写", "请扩展该表述并标出仍需人工确认的依据。", "medical_writing_revision"],
              ["转批注", "请将该问题整理为给医学经理复核的批注式问题。", "medical_writing_revision"],
            ].map(([item, instruction, intent]) => (
              <button
                key={item}
                disabled={aiRevisionDisabled}
                onClick={() => {
                  setRevisionInstruction(instruction);
                  setRevisionIntent(intent);
                }}
              >
                <PencilLine size={14} /> {item}
              </button>
            ))}
          </div>
          {approvedLocked && (
            <div className="approval-lock">
              <CheckCircle2 size={16} />
              医学已批准章节已锁定；如需 AI 参与修改，需先退回修订并重新进入医学审阅。
            </div>
          )}
          {!sectionHasBackendBinding && (
            <div className="approval-lock warning">
              <AlertTriangle size={16} />
              当前章节暂无后端章节绑定，AI修订已关闭；请先完成真实方案章节映射，避免写入其他章节线程。
            </div>
          )}
          <RichProtocolEditor
            key={selectedSection}
            section={section}
            approvedLocked={approvedLocked}
            selectedSection={selectedSection}
            onSelectedTextChange={setSelectedEditorText}
            onEditorTextChange={setEditorPlainText}
          />
        </section>
        <aside className="panel ai-rail writing-ai-core">
          <div className="rail-tabs">
            {["AI", "证据", "风险", "审阅", "版本"].map((tab) => <button className={tab === "AI" ? "active" : ""} key={tab}>{tab}</button>)}
          </div>
          <div className="revision-form">
            <Tag tone="warning">待医学批准</Tag>
            <h3>AI修订指令</h3>
            <p>{revisionBoundary}</p>
            <label>
              修订意图
              <select value={revisionIntent} onChange={(event) => setRevisionIntent(event.target.value)} disabled={aiRevisionDisabled || revisionLoading}>
                {revisionIntentOptions.map((item) => <option value={item.value} key={item.value}>{item.label}</option>)}
              </select>
            </label>
            <label>
              用户指令
              <textarea value={revisionInstruction} onChange={(event) => setRevisionInstruction(event.target.value)} disabled={aiRevisionDisabled || revisionLoading} />
            </label>
            <div className="selected-text">
              <strong>本次提交文本</strong>
              <span>{sectionHasBackendBinding ? (selectedEditorText || editorPlainText || "请选择或编辑章节文本后提交。") : "当前章节暂无后端章节绑定，不能提交AI修订。"}</span>
            </div>
            <button className="primary-button" onClick={submitRevisionRequest} disabled={aiRevisionDisabled || revisionLoading || !revisionInstruction.trim()}>
              {revisionLoading ? "处理中" : "提交AI修订"}
            </button>
            {revisionMessage && <p className="revision-message">{revisionMessage}</p>}
          </div>
          <div className="revision-thread-list">
            <div className="revision-thread-head">
              <h3>修订线程</h3>
              <button onClick={refreshRevisionThreads} disabled={revisionLoading}>{revisionLoading ? "读取中" : "刷新"}</button>
            </div>
            {sectionThreads.length ? sectionThreads.map((thread) => (
              <button
                key={thread.thread_id}
                className={thread.thread_id === activeThread?.thread_id ? "active" : ""}
                onClick={() => setActiveRevisionThreadId(thread.thread_id)}
              >
                <span>{thread.thread_id.replace("thread_", "线程 ")}</span>
                <Tag tone={revisionThreadTone(thread.status)}>{revisionThreadStatusLabel(thread.status)}</Tag>
              </button>
            )) : <p className="quiet-text">当前章节暂无修订线程。</p>}
          </div>
          <div className="revision-thread">
            {activeThread ? (
              <>
                <Tag tone={revisionThreadTone(activeThread.status)}>{revisionThreadStatusLabel(activeThread.status)}</Tag>
                <h3>用户指令</h3>
                <p>{activeThread.user_instruction}</p>
                <h3>diff</h3>
                <div className="diff-box">
                  <del>{activeThread.selected_text}</del>
                  <ins>{activeSuggestion?.proposal_text || "暂无建议正文"}</ins>
                </div>
                <h3>证据与不确定性</h3>
                <p>{activeSuggestion?.rationale || "待生成修订理由。"}</p>
                <p>{activeSuggestion?.uncertainty || "独立AI provider未配置，当前不生成生产写作结论。"}</p>
                <p className="revision-boundary-line">{revisionBoundary}</p>
                <label>
                  处置意见
                  <textarea value={revisionActionComment} onChange={(event) => setRevisionActionComment(event.target.value)} disabled={revisionLoading || !activeSuggestion || activeSuggestion.user_decision !== "pending"} />
                </label>
                <label>
                  重写指令
                  <textarea value={revisionRewriteInstruction} onChange={(event) => setRevisionRewriteInstruction(event.target.value)} disabled={revisionLoading || !activeSuggestion || activeSuggestion.user_decision !== "pending"} />
                </label>
                <div className="button-row">
                  <button className="primary-button" disabled={revisionLoading || !activeSuggestion || activeSuggestion.user_decision !== "pending"} onClick={() => submitRevisionAction(activeThread, "accept")}>接受为候选</button>
                  <button disabled={revisionLoading || !activeSuggestion || activeSuggestion.user_decision !== "pending"} onClick={() => submitRevisionAction(activeThread, "reject")}>拒绝建议</button>
                  <button disabled={revisionLoading || !activeSuggestion || activeSuggestion.user_decision !== "pending" || !revisionRewriteInstruction.trim()} onClick={() => submitRevisionAction(activeThread, "request_rewrite")}>要求重写</button>
                </div>
              </>
            ) : (
              <div className="empty-state">暂无AI修订线程。请在上方提交修订指令。</div>
            )}
          </div>
          <div className="export-gate">
            <h3>导出质量门</h3>
            {[`未批准 AI 内容 ${revisionThreads.filter((thread) => thread.status !== "rejected").length} 项`, "开放高风险 3 项", `当前章节修订线程 ${sectionThreads.length} 条`, "证据索引覆盖 68%"].map((item, index) => (
              <p key={item} className={index < 3 ? "blocking" : "info"}>{item}</p>
            ))}
          </div>
        </aside>
        <section className="panel section-tree writing-section-strip writing-document-map">
          <div className="writing-section-strip-head">
            <span>文档结构</span>
            <strong>{section.title}</strong>
          </div>
          <div className="writing-map-summary">
            <div><strong>{writingSections.length}</strong><span>章节</span></div>
            <div><strong>{section.coverage}%</strong><span>当前证据覆盖</span></div>
            <div><strong>{sectionThreads.length}</strong><span>本章AI线程</span></div>
          </div>
          <div className="writing-section-buttons">
            {writingSections.map((section) => (
              <button key={section.id} className={selectedSection === section.id ? "active" : ""} onClick={() => setSelectedSection(section.id)}>
                <span>{section.title}</span>
                <Tag tone={section.status === "已批准" ? "success" : section.status === "医学审阅中" ? "warning" : "info"}>{section.status}</Tag>
                <Progress value={section.coverage / 100} />
              </button>
            ))}
          </div>
        </section>
      </div>
      <div className="writing-support-zone">
        <MedicalWritingManifestPanel
          manifest={writingManifest}
          loading={manifestLoading}
          message={manifestMessage}
          onRefresh={refreshWritingManifest}
          selectedPackageId={selectedPackageId}
          onSelectPackage={setSelectedPackageId}
          tflCitations={tflCitations}
          tflCitationLoading={tflCitationLoading}
          tflCitationMessage={tflCitationMessage}
          onRefreshTflCitations={refreshTflCitations}
        />
      </div>
    </main>
  );
}

function approvalTypeLabel(targetType, fallback = "") {
  if (targetType?.startsWith("medical_writing")) return "医学写作";
  if (targetType?.startsWith("medical_monitoring")) return "医学监查";
  if (targetType?.startsWith("eligibility_review")) return "入排审核";
  return fallback || "审批事项";
}

function approvalTitle(item) {
  const knownTitles = {
    approval_protocol_sec_objectives: "研究目的与终点章节",
    approval_medical_monitoring_batch003: "Batch 003 风险冻结包",
  };
  if (item.target_type === "medical_monitoring_risk_disposition") {
    const comments = item.review_comments || "";
    const risk = comments.match(/风险：([^；。]+)/)?.[1]?.trim();
    const subject = comments.match(/受试者：([^；。]+)/)?.[1]?.trim();
    const riskText = risk
      ? subject && !risk.includes(subject) ? `${subject} ${risk}` : risk
      : subject;
    return riskText ? `RUX内部Query草稿审批：${riskText}` : "RUX内部Query草稿审批：医学监查风险处置建议";
  }
  if (item.target_type === "medical_writing_revision_thread") return `医学写作修订建议：${item.target_id}`;
  return knownTitles[item.approval_id] || item.title || item.target_id || "待医学批准内容";
}

function approvalStateLabel(state) {
  return {
    ai_draft: "待医学批准",
    in_medical_review: "医学审阅中",
    returned_for_revision: "退回修订",
    medically_approved: "已批准",
    locked_for_submission: "已锁定",
    superseded: "已作废",
    archived: "已归档",
  }[state] || state;
}

function normalizeApprovalItem(item) {
  if (item.approval_id) {
    const isRuxDisposition = item.target_type === "medical_monitoring_risk_disposition";
    return {
      id: item.approval_id,
      title: approvalTitle(item),
      type: approvalTypeLabel(item.target_type),
      state: approvalStateLabel(item.state),
      rawState: item.state,
      ai: isRuxDisposition || item.requested_by === "system" ? "规则运行" : "AI 修订",
      risk: isRuxDisposition ? "内部审批候选" : item.state === "ai_draft" ? "待查看质量门" : "需质量门确认",
      owner: item.reviewed_by || item.approved_by || "医学经理",
      blockers: [],
      comments: item.review_comments || "",
      internalApprovalBoundary: isRuxDisposition
        ? "仅批准内部Query草稿/处置建议，不代表对外Query已执行、风险关闭或归档。"
        : "",
      isRuxDisposition,
    };
  }
  return {
    ...item,
    rawState: item.state,
  };
}

const plannedModuleContent = {
  evidenceDesign: {
    module: "evidence_design",
    eyebrow: "证据与设计",
    title: "证据调研与方案设计",
    status: "原始资料登记与证据索引 P0",
    summary: "面向适应症背景、监管指导原则、竞品目录、竞品方案和临床结果，形成可更新的证据平台，并将待医学确认的 PICOS 设计建议流转到医学写作。",
    inputs: ["CDE/FDA/EMA 指导原则", "ClinicalTrials.gov / CDE 登记", "PubMed / 期刊全文", "竞品 protocol / SAP / medical review", "本地 CRSwNP 竞品调研原文"],
    aiTasks: ["disease_background_research", "competitive_intelligence", "protocol_design_synthesis", "picos_design_coach"],
    next: ["建立证据资料台账", "接入公开检索与本地竞品原文", "形成 PICOS 问答式设计工作流", "与医学写作章节树联动"],
  },
  tfl: {
    module: "data_analysis_tfl",
    eyebrow: "数据分析",
    title: "数据分析与TFL",
    status: "资料登记与数据清单 P0",
    summary: "面向 SDTM/ADaM、define.xml、SAP 和 TFL shells，提供医学经理可读的数据查看、表图清单生成、监管交付和写作引用能力。",
    inputs: ["SDTM XPT/SAS7BDAT", "ADaM XPT/SAS7BDAT", "define.xml", "SAP", "TFL shells / RTF / CSV"],
    aiTasks: ["tfl_generation_assist", "analysis_result_explanation"],
    next: ["盘点 Ruxolitinib-AD 与 MY008 的数据集样本", "建立数据集清单（dataset manifest）", "生成TFL查看页最小版", "将结果摘要供医学写作引用"],
  },
  safety: {
    module: "safety_pv",
    eyebrow: "安全性协同",
    title: "安全信号与PV协同",
    status: "协同复核 P0",
    summary: "本页输出为安全性医学/PV协同候选，不替代PV系统或正式药物警戒流程；以下内容均为待医学/PV确认。",
    inputs: ["安全性listing", "PV提供的个案叙述资料", "DSUR/IB安全更新素材", "安全计划参考资料", "医学监查风险账本"],
    aiTasks: ["safety_case_medical_review", "signal_narrative_synthesis"],
    next: ["确定与医学监查风险账本的边界", "接入安全性资料台账", "建立 SAE/AESI 医学审阅质量门", "联动医学写作 DSUR/IB 模块"],
  },
};

const sourceRegistryCandidates = {
  evidenceDesign: [
    {
      id: "ev-crs-trial-design",
      title: "CRSwNP 竞品试验设计索引",
      kind: "local-file",
      module: "evidence_design",
      sourceType: "CSV",
      purpose: "竞品方案设计、终点、样本量和入排标准结构化索引。",
    },
    {
      id: "ev-crs-efficacy",
      title: "CRSwNP 疗效结果索引",
      kind: "local-file",
      module: "evidence_design",
      sourceType: "CSV",
      purpose: "PICOS 决策和医学写作主要/次要终点证据。",
    },
    {
      id: "ev-crs-safety",
      title: "CRSwNP 安全性结果索引",
      kind: "local-file",
      module: "evidence_design",
      sourceType: "CSV",
      purpose: "竞品安全性结局、AESI 和安全章节证据。",
    },
    {
      id: "ev-crs-document-index",
      title: "CRSwNP 原文索引",
      kind: "local-file",
      module: "evidence_design",
      sourceType: "CSV",
      purpose: "追踪 protocol、SAP、publication 和监管原文路径。",
    },
  ],
  tfl: [
    {
      id: "tfl-rux-listing",
      title: "RUX-03-002 项目级 listing",
      kind: "local-file",
      module: "data_analysis_tfl",
      sourceType: "XLSX",
      purpose: "跨项目字段识别、数据集查看和医学解释样本。",
    },
    {
      id: "tfl-rux-sdtm-package",
      title: "RUX-03-002 SDTM 数据包",
      kind: "local-directory",
      module: "data_analysis_tfl",
      sourceKind: "tfl_dataset_package_inventory",
      sourceType: "Directory",
      purpose: "XPT、define、aCRF 和 reviewer guide 的 dataset manifest 起点。",
    },
    {
      id: "tfl-rux-final-tfl",
      title: "RUX-03-002 SAR 与 TFL 包",
      kind: "local-directory",
      module: "data_analysis_tfl",
      sourceKind: "tfl_output_package_inventory",
      sourceType: "Directory",
      purpose: "最终 TFL、adhoc TLF 和写作引用链路。",
    },
  ],
  safety: [
    {
      id: "pv-my009-mm-listing",
      title: "MY009 UC 医学复核 listing",
      kind: "local-file",
      module: "safety_pv",
      sourceType: "XLSX",
      purpose: "AE、实验室、合并用药和医学复核安全样本。",
    },
    {
      id: "pv-my009-safety-package",
      title: "MY009 UC S1 安全评估包",
      kind: "local-directory",
      module: "safety_pv",
      sourceKind: "safety_signal_package_inventory",
      sourceType: "Directory",
      purpose: "安全评估报告、AE TFL、比较表和演示材料登记。",
    },
    {
      id: "pv-my009-dsur",
      title: "MY009 DSUR 医学资料收集表",
      kind: "local-file",
      module: "safety_pv",
      sourceType: "DOCX",
      purpose: "DSUR/IB 安全更新和医学-PV 协同字段样本。",
    },
    {
      id: "pv-rux-pv-plan",
      title: "RUX-03-002 PV计划包",
      kind: "local-directory",
      module: "safety_pv",
      sourceKind: "pv_safety_package_inventory",
      sourceType: "Directory",
      purpose: "安全管理计划、PV 协同边界和质量门依据。",
    },
    {
      id: "pv-rux-274",
      title: "RUX-03-002 2.7.4安全总结",
      kind: "local-directory",
      module: "safety_pv",
      sourceKind: "clinical_safety_summary_inventory",
      sourceType: "Directory",
      purpose: "安全性总结、实验室和 AE 风险解释的监管交付依据。",
    },
  ],
};

function TflManifestPanel({
  manifest,
  loading,
  message,
  onRefresh,
  selectedPackageId,
  onSelectPackage,
  reviewWorkbench,
  reviewLoading,
  reviewMessage,
  selectedOutputId,
  onSelectOutput,
  onRefreshReview,
  onApplyReviewAction,
  applyingReviewAction,
}) {
  const packages = manifest?.packages || [];
  const selectedPackage = packages.find((item) => item.package_id === selectedPackageId) || packages[0];
  const [reviewComment, setReviewComment] = useState("");
  const qualityGaps = packages.reduce((count, item) => count + (item.define_itemgroup_count ? 0 : 1), 0);
  const datasetPreview = selectedPackage
    ? [...selectedPackage.datasets]
        .sort((left, right) => {
          const parsedDelta = Number(right.parser_status === "parsed") - Number(left.parser_status === "parsed");
          if (parsedDelta) return parsedDelta;
          return `${left.standard}${left.dataset_name}`.localeCompare(`${right.standard}${right.dataset_name}`);
        })
        .slice(0, 12)
    : [];
  const outputPreview = selectedPackage ? selectedPackage.outputs.slice(0, 12) : [];
  const warnings = selectedPackage?.parser_warnings?.slice(0, 5) || [];
  const selectedTflCounts = selectedPackage?.tfl_count_by_type || {};
  const tflCountText = `表${selectedTflCounts.table || 0} / 图${selectedTflCounts.figure || 0} / Listing${selectedTflCounts.listing || 0}`;
  const reviewOutput = reviewWorkbench?.selected_output;
  const reviewDataset = reviewWorkbench?.paired_dataset;
  const reviewCandidates = reviewWorkbench?.candidate_outputs || [];
  const reviewGates = reviewWorkbench?.quality_gates || [];
  const reviewRecords = reviewWorkbench?.review_records || [];
  const datasetContext = reviewWorkbench?.dataset_context || [];
  const reviewStatus = reviewWorkbench?.current_status || "待医学审阅";
  const writingCandidateAllowed = Boolean(reviewDataset) && ["医学已审阅", "写作引用候选"].includes(reviewStatus);
  const actionOrder = [
    "mark_reviewed",
    "request_statistical_review",
    "create_writing_candidate",
    "return_for_dataset_check",
    "reset_review",
  ];

  useEffect(() => {
    setReviewComment("");
  }, [reviewWorkbench?.selected_output_id]);

  const submitReviewAction = (action) => {
    onApplyReviewAction(action, reviewComment).then((ok) => {
      if (ok) setReviewComment("");
    });
  };

  return (
    <section className="panel tfl-manifest-panel">
      <SectionTitle
        title="数据集清单与TFL交付清单"
        action={<button onClick={onRefresh} disabled={loading}>{loading ? "生成中" : "刷新清单"}</button>}
      />
      <div className="tfl-manifest-stats">
        <div><strong>{manifest?.package_count || 0}</strong><span>真实交付包</span></div>
        <div><strong>{formatMaybeNumber(manifest?.total_datasets)}</strong><span>数据文件</span></div>
        <div><strong>{formatMaybeNumber(manifest?.total_outputs)}</strong><span>TFL RTF输出</span></div>
        <div className={qualityGaps ? "warning" : ""}><strong>{qualityGaps}</strong><span>define缺口包</span></div>
      </div>
      {message && <div className="source-registry-message">{message}</div>}
      <div className="tfl-package-tabs">
        {packages.map((item) => (
          <button
            key={item.package_id}
            className={item.package_id === selectedPackage?.package_id ? "active" : ""}
            onClick={() => onSelectPackage(item.package_id)}
          >
            {item.package_label}
          </button>
        ))}
      </div>
      {selectedPackage ? (
        <>
          <div className="tfl-package-summary">
            <div><span>数据目录</span><strong>{selectedPackage.dataset_root_label}</strong></div>
            <div><span>TFL目录</span><strong>{selectedPackage.tfl_root_label}</strong></div>
            <div><span>define.xml</span><strong>{selectedPackage.define_xml_count} 个文件 / {selectedPackage.define_itemgroup_count} 个数据集定义</strong></div>
            <div><span>TFL输出</span><strong>{tflCountText}</strong></div>
            <div><span>目录角色</span><strong>{Object.entries(selectedPackage.dataset_count_by_role).map(([key, value]) => `${key}:${value}`).join("；") || "未识别"}</strong></div>
          </div>
          <div className="tfl-quality-gates">
            <Tag tone={selectedPackage.define_itemgroup_count ? "success" : "warning"}>
              {selectedPackage.define_itemgroup_count ? "define已关联" : "define缺失/未提供"}
            </Tag>
            <Tag tone={Object.values(selectedPackage.tfl_count_by_type).length ? "success" : "warning"}>TFL输出已登记</Tag>
            <Tag tone="warning">不生成正式TFL</Tag>
            <Tag tone="neutral">待医学确认</Tag>
          </div>
          {warnings.length ? (
            <div className="tfl-warning-list">
              {warnings.map((warning) => <span key={warning}>{warning}</span>)}
            </div>
          ) : null}
          <div className="tfl-review-workbench">
            <SectionTitle
              title="TFL审阅工作台"
              action={<button onClick={onRefreshReview} disabled={reviewLoading || !selectedPackage}>{reviewLoading ? "读取中" : "刷新审阅状态"}</button>}
            />
            <div className="tfl-review-boundary">
              {reviewWorkbench?.formal_output_boundary || "当前仅形成待医学确认的数据审阅和写作引用候选，不生成正式监管TFL。"}
            </div>
            {reviewMessage && <div className="source-registry-message">{reviewMessage}</div>}
            <div className="tfl-review-focus">
              <div><span>当前审阅状态</span><strong>{reviewStatus}</strong></div>
              <div><span>当前TFL对象</span><strong>{reviewOutput?.display_id || "未选择"}</strong></div>
              <div><span>类型/领域</span><strong>{reviewOutput ? `${tflOutputTypeLabel(reviewOutput.output_type)} / ${reviewOutput.domain_hint || "领域待识别"}` : "未选择"}</strong></div>
              <div><span>配对数据集</span><strong>{reviewDataset ? `${reviewDataset.dataset_name}（${reviewDataset.row_count ?? "未读"}行）` : "未识别，需复核"}</strong></div>
            </div>
            <div className="tfl-review-grid">
              <div className="tfl-review-selector">
                <h3>候选TFL输出</h3>
                <div className="tfl-review-candidate-list">
                  {reviewCandidates.length ? reviewCandidates.map((output) => (
                    <button
                      key={output.output_id}
                      className={output.output_id === (selectedOutputId || reviewWorkbench?.selected_output_id) ? "active" : ""}
                      onClick={() => onSelectOutput(output.output_id)}
                    >
                      <strong>{output.display_id}</strong>
                      <span>{tflOutputTypeLabel(output.output_type)} · {output.domain_hint || "领域待识别"} · {output.paired_file_id ? "已配对" : "未配对"}</span>
                    </button>
                  )) : <div className="empty-state">当前包尚未识别可审阅TFL输出。</div>}
                </div>
              </div>
              <div className="tfl-review-detail">
                <h3>质量门与处置意见</h3>
                <div className="tfl-review-gates">
                  {reviewGates.map((gate) => (
                    <div key={gate.gate_id}>
                      <Tag tone={safetyGateTone(gate.status)}>{gateStatusLabel(gate.status)}</Tag>
                      <strong>{gate.gate_label}</strong>
                      <span>{gate.detail}</span>
                    </div>
                  ))}
                </div>
                <label className="tfl-review-comment">
                  <span>本次医学/统计处理意见</span>
                  <textarea
                    value={reviewComment}
                    onChange={(event) => setReviewComment(event.target.value)}
                    placeholder="填写审阅依据、需统计复核的问题或允许进入写作引用候选的边界。"
                    rows={4}
                  />
                </label>
                <div className="tfl-review-actions">
                  {actionOrder.map((action) => {
                    const needsComment = action !== "reset_review";
                    const disabled = reviewLoading ||
                      Boolean(applyingReviewAction) ||
                      !reviewOutput ||
                      (needsComment && !reviewComment.trim()) ||
                      (action === "create_writing_candidate" && !writingCandidateAllowed);
                    return (
                      <button
                        key={action}
                        className={action === "mark_reviewed" ? "primary-button" : ""}
                        onClick={() => submitReviewAction(action)}
                        disabled={disabled}
                      >
                        {applyingReviewAction === action ? "处理中" : tflReviewActionLabel(action)}
                      </button>
                    );
                  })}
                </div>
                {!writingCandidateAllowed && (
                  <p className="tfl-review-hint">写作引用候选需要已配对数据集，并先完成医学审阅。</p>
                )}
              </div>
            </div>
            <div className="tfl-review-support-grid">
              <div className="tfl-table-block">
                <h3>配套数据集上下文</h3>
                <div className="tfl-table-scroll tfl-review-dataset-table">
                  <table>
                    <thead>
                      <tr>
                        <th>数据集</th>
                        <th>标准/角色</th>
                        <th>域</th>
                        <th>行/变量</th>
                        <th>关键变量</th>
                        <th>define</th>
                      </tr>
                    </thead>
                    <tbody>
                      {datasetContext.map((dataset) => (
                        <tr key={dataset.dataset_id}>
                          <td><strong>{dataset.dataset_name}</strong><span>{dataset.relative_path}</span></td>
                          <td>{dataset.standard} / {dataset.package_role}</td>
                          <td>{dataset.domain || dataset.class_name || "未识别"}</td>
                          <td>{formatMaybeNumber(dataset.row_count)} / {formatMaybeNumber(dataset.column_count)}</td>
                          <td>{dataset.key_variables.slice(0, 6).join(", ") || "待解析"}</td>
                          <td>{dataset.define_linked ? "已关联" : "未关联"}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
              <div className="tfl-review-audit">
                <h3>审阅轨迹</h3>
                {reviewRecords.length ? reviewRecords.map((record) => (
                  <div key={record.record_id}>
                    <Tag tone={record.new_status === "写作引用候选" || record.new_status === "医学已审阅" ? "success" : "warning"}>
                      {record.new_status}
                    </Tag>
                    <strong>{tflReviewActionLabel(record.action)}</strong>
                    <span>{record.actor} · {new Date(record.created_at).toLocaleString("zh-CN")}</span>
                    <p>{record.comment || "未填写意见"}</p>
                  </div>
                )) : <div className="empty-state">尚无审阅动作记录。</div>}
              </div>
            </div>
          </div>
          <div className="tfl-manifest-grid">
            <div className="tfl-table-block">
              <h3>数据集清单（dataset manifest）</h3>
              <div className="tfl-table-scroll">
                <table>
                  <thead>
                    <tr>
                      <th>数据集</th>
                      <th>标准</th>
                      <th>角色</th>
                      <th>域/类别</th>
                      <th>行数</th>
                      <th>变量数</th>
                      <th>关键变量</th>
                      <th>define</th>
                      <th>解析状态</th>
                    </tr>
                  </thead>
                  <tbody>
                    {datasetPreview.map((dataset) => (
                      <tr key={dataset.dataset_id}>
                        <td><strong>{dataset.dataset_name}</strong><span>{dataset.relative_path}</span></td>
                        <td>{dataset.standard}</td>
                        <td>{dataset.package_role}</td>
                        <td>{dataset.domain || dataset.class_name || "未识别"}</td>
                        <td>{formatMaybeNumber(dataset.row_count)}</td>
                        <td>{formatMaybeNumber(dataset.column_count)}</td>
                        <td>{dataset.key_variables.slice(0, 5).join(", ") || "待解析"}</td>
                        <td>{dataset.define_linked ? "已关联" : "未关联"}</td>
                        <td>{parserStatusDisplay(dataset.parser_status)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
            <div className="tfl-table-block">
              <h3>TFL清单</h3>
              <div className="tfl-table-scroll">
                <table>
                  <thead>
                    <tr>
                      <th>编号</th>
                      <th>类型</th>
                      <th>领域</th>
                      <th>标题线索</th>
                      <th>配对数据</th>
                      <th>文件</th>
                      <th>状态</th>
                    </tr>
                  </thead>
                  <tbody>
                    {outputPreview.map((output) => (
                      <tr key={output.output_id}>
                        <td><strong>{output.display_id}</strong></td>
                        <td>{tflOutputTypeLabel(output.output_type)}</td>
                        <td>{output.domain_hint || "未识别"}</td>
                        <td>{output.title_hint || "待抽取"}</td>
                        <td>{output.paired_file_id ? "已配对" : "未配对"}</td>
                        <td><span>{output.relative_path}</span></td>
                        <td>{parserStatusDisplay(output.parser_status)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
          <div className="tfl-note-list">
            {selectedPackage.traceability_notes.map((note) => <span key={note}>{note}</span>)}
          </div>
        </>
      ) : (
        <div className="empty-state">尚未生成数据集与TFL清单。</div>
      )}
    </section>
  );
}

function SafetyPvManifestPanel({
  manifest,
  loading,
  message,
  onRefresh,
  selectedPackageId,
  onSelectPackage,
  selectedSignalId,
  onSelectSignal,
  reviewWorkbench,
  reviewLoading,
  reviewMessage,
  reviewComment,
  setReviewComment,
  onReviewAction,
  applyingReviewAction,
  handoffManifest,
  onRefreshHandoff,
}) {
  const packages = manifest?.packages || [];
  const selectedPackage = packages.find((item) => item.package_id === selectedPackageId) || packages[0];
  const domains = selectedPackage ? selectedPackage.listing_domains.slice(0, 14) : [];
  const documents = selectedPackage ? selectedPackage.documents.slice(0, 10) : [];
  const candidates = (reviewWorkbench?.candidate_signals?.length ? reviewWorkbench.candidate_signals : selectedPackage?.signal_candidates || []).slice(0, 24);
  const selectedSignal = reviewWorkbench?.selected_signal || candidates.find((item) => item.signal_id === selectedSignalId) || candidates[0];
  const gates = selectedPackage ? selectedPackage.quality_gates : [];
  const reviewGates = reviewWorkbench?.quality_gates || [];
  const reviewRecords = reviewWorkbench?.review_records || [];
  const handoffCandidates = handoffManifest?.candidates || [];
  const warnings = selectedPackage?.parser_warnings?.slice(0, 4) || [];
  const actionOrder = [
    "mark_medical_reviewed",
    "request_pv_confirmation",
    "return_for_source_check",
    "accept_no_action",
    "reset_review",
  ];
  const latestReviewStatus = reviewRecords.length ? reviewRecords[reviewRecords.length - 1].new_status : "";
  const currentStatus = latestReviewStatus || reviewWorkbench?.current_status || selectedSignal?.confirmation_status || "待医学/PV确认";
  const canRequestPv = currentStatus === "医学已复核" || currentStatus === "PV确认候选";

  const submitReviewAction = (action) => {
    onReviewAction(action, action === "reset_review" ? "" : reviewComment);
  };

  return (
    <section className="panel tfl-manifest-panel safety-pv-panel">
      <SectionTitle
        title="安全信号审阅工作台"
        action={<button onClick={onRefresh} disabled={loading}>{loading ? "生成中" : "刷新安全资料清单"}</button>}
      />
      <div className="safety-pv-boundary">
        以下内容为待医学/PV确认的安全信号审阅记录和协同交接候选，不构成最终安全性结论或监管递交意见；报告性判断和递交流程由PV流程确认。
      </div>
      <div className="safety-pv-stats">
        <div><strong>{manifest?.package_count || 0}</strong><span>真实安全资料包</span></div>
        <div><strong>{formatMaybeNumber(manifest?.total_listing_domains)}</strong><span>listing域</span></div>
        <div><strong>{formatMaybeNumber(manifest?.total_documents)}</strong><span>安全资料文件</span></div>
        <div><strong>{formatMaybeNumber(manifest?.total_signal_candidates)}</strong><span>待确认候选</span></div>
        <div><strong>{formatMaybeNumber(manifest?.quality_gate_count)}</strong><span>质量门</span></div>
      </div>
      {message && <div className="source-registry-message">{message}</div>}
      <div className="tfl-package-tabs">
        {packages.map((item) => (
          <button
            key={item.package_id}
            className={item.package_id === selectedPackage?.package_id ? "active" : ""}
            onClick={() => onSelectPackage(item.package_id)}
          >
            {item.package_label}
          </button>
        ))}
      </div>
      {selectedPackage ? (
        <>
          <div className="tfl-package-summary safety-package-summary">
            <div><span>项目</span><strong>{selectedPackage.project_code}</strong></div>
            <div><span>资料包</span><strong>{selectedPackage.source_root_label}</strong></div>
            <div><span>资料角色</span><strong>{selectedPackage.package_role}</strong></div>
            <div><span>listing / 文件</span><strong>{selectedPackage.listing_domains.length} 个域 / {selectedPackage.documents.length} 个文件</strong></div>
            <div><span>候选 / 质量门</span><strong>{selectedPackage.signal_candidates.length} 个候选 / {selectedPackage.quality_gates.length} 个质量门</strong></div>
          </div>
          <div className="tfl-quality-gates">
            <Tag tone="warning">待医学/PV确认</Tag>
            <Tag tone="neutral">不替代PV系统</Tag>
            <Tag tone={selectedPackage.listing_domains.length ? "success" : "warning"}>安全域已登记</Tag>
            <Tag tone={selectedPackage.documents.length ? "success" : "warning"}>源资料已登记</Tag>
          </div>
          {warnings.length ? (
            <div className="tfl-warning-list">
              {warnings.map((warning) => <span key={warning}>{warning}</span>)}
            </div>
          ) : null}
          <div className="safety-review-workbench">
            <div className="safety-review-head">
              <div>
                <h3>安全信号审阅工作台</h3>
                <p>{reviewWorkbench?.formal_output_boundary || "当前仅形成待医学/PV确认的审阅记录和交接候选。"}</p>
              </div>
              <div className="safety-review-head-actions">
                <Tag tone={currentStatus === "PV确认候选" ? "success" : currentStatus === "退回补充资料" ? "warning" : "info"}>{currentStatus}</Tag>
                <Tag tone="neutral">不替代PV系统</Tag>
                <button onClick={onRefreshHandoff}>刷新交接候选</button>
              </div>
            </div>
            {reviewMessage && <div className="source-registry-message">{reviewMessage}</div>}
            <div className="safety-review-grid">
              <aside className="safety-review-selector">
                <h3>候选安全信号</h3>
                <div className="safety-review-candidate-list">
                  {candidates.map((candidate) => (
                    <button
                      key={candidate.signal_id}
                      className={candidate.signal_id === reviewWorkbench?.selected_signal_id ? "active" : ""}
                      onClick={() => onSelectSignal(candidate.signal_id)}
                    >
                      <span>{candidate.signal_label}</span>
                      <strong>{candidate.title}</strong>
                      <em>{candidate.source_domains.slice(0, 4).join(" / ") || "来源待补充"}</em>
                      <Tag tone={statusClass(candidate.severity)}>{severityLabel(candidate.severity)}</Tag>
                    </button>
                  ))}
                </div>
              </aside>
              <section className="safety-review-detail">
                <div className="safety-signal-summary">
                  <Tag tone={statusClass(selectedSignal?.severity)}>{severityLabel(selectedSignal?.severity)}</Tag>
                  <h3>{selectedSignal?.title || "请选择安全信号候选"}</h3>
                  <p>{selectedSignal?.observation || "等待读取候选详情。"}</p>
                  <div>
                    {(selectedSignal?.evidence_locators || []).slice(0, 5).map((locator) => <span key={locator}>{locator}</span>)}
                  </div>
                </div>
                <div className="safety-review-gates">
                  {reviewGates.map((gate) => (
                    <div key={gate.gate_id}>
                      <Tag tone={safetyGateTone(gate.status)}>{gateStatusLabel(gate.status)}</Tag>
                      <strong>{gate.gate_label}</strong>
                      <span>{gate.detail}</span>
                    </div>
                  ))}
                </div>
                <label className="safety-review-comment">
                  <span>医学意见与协同说明</span>
                  <textarea
                    value={reviewComment}
                    onChange={(event) => setReviewComment(event.target.value)}
                    placeholder="填写本次医学复核理由、来源定位、需PV确认的问题或退回补充资料要求。"
                    rows={4}
                  />
                </label>
                <div className="safety-review-actions">
                  {actionOrder.map((action) => {
                    const needsComment = action !== "reset_review";
                    const disabled = reviewLoading ||
                      Boolean(applyingReviewAction) ||
                      !selectedSignal ||
                      (needsComment && !reviewComment.trim());
                    return (
                      <button
                        key={action}
                        className={action === "mark_medical_reviewed" ? "primary-button" : ""}
                        disabled={disabled}
                        onClick={() => submitReviewAction(action)}
                      >
                        {applyingReviewAction === action ? "处理中" : safetyReviewActionLabel(action)}
                      </button>
                    );
                  })}
                </div>
                {!canRequestPv && <p className="safety-review-hint">标记PV协同确认前，需要先保存医学意见并形成“医学已复核”状态。</p>}
              </section>
              <aside className="safety-review-side">
                <section className="safety-review-audit">
                  <h3>审计记录</h3>
                  {reviewRecords.length ? reviewRecords.map((record) => (
                    <div className="safety-review-record" key={record.record_id}>
                      <Tag tone={record.new_status === "PV确认候选" || record.new_status === "医学已复核" ? "success" : "warning"}>{record.new_status}</Tag>
                      <strong>{safetyReviewActionLabel(record.action)}</strong>
                      <span>{record.actor} · {new Date(record.created_at).toLocaleString("zh-CN")}</span>
                      <p>{record.comment || "未填写意见"}</p>
                    </div>
                  )) : <div className="empty-state">尚无审阅动作记录。</div>}
                </section>
                <section className="safety-handoff-panel">
                  <h3>PV协同交接候选</h3>
                  {handoffCandidates.length ? handoffCandidates.slice(0, 6).map((candidate) => (
                    <div className="safety-handoff-card" key={candidate.candidate_id}>
                      <Tag tone={statusClass(candidate.severity)}>{severityLabel(candidate.severity)}</Tag>
                      <strong>{candidate.title}</strong>
                      <span>{candidate.recommended_handoff_sections.join(" / ")}</span>
                      <p>{candidate.review_comment}</p>
                    </div>
                  )) : <div className="empty-state">暂无PV协同交接候选。</div>}
                </section>
              </aside>
            </div>
          </div>
          <div className="tfl-manifest-grid">
            <div className="tfl-table-block">
              <h3>安全listing域清单</h3>
              <div className="tfl-table-scroll safety-domain-table">
                <table>
                  <thead>
                    <tr>
                      <th>域</th>
                      <th>医学标签</th>
                      <th>安全性用途</th>
                      <th>记录数</th>
                      <th>受试者</th>
                      <th>中心</th>
                      <th>关键字段</th>
                      <th>状态</th>
                    </tr>
                  </thead>
                  <tbody>
                    {domains.map((domain) => (
                      <tr key={domain.domain_id}>
                        <td><strong>{domain.sheet_name}</strong><span>{domain.domain}</span></td>
                        <td>{domain.domain_label}</td>
                        <td>{domain.safety_relevance}</td>
                        <td>{formatMaybeNumber(domain.row_count)}</td>
                        <td>{formatMaybeNumber(domain.subject_count)}</td>
                        <td>{formatMaybeNumber(domain.site_count)}</td>
                        <td>{domain.key_fields.slice(0, 6).join(", ") || "待识别"}</td>
                        <td>{parserStatusDisplay(domain.parser_status)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
            <div className="tfl-table-block">
              <h3>安全资料文件</h3>
              <div className="tfl-table-scroll safety-doc-table">
                <table>
                  <thead>
                    <tr>
                      <th>资料</th>
                      <th>类型</th>
                      <th>用途</th>
                      <th>主题</th>
                      <th>状态</th>
                    </tr>
                  </thead>
                  <tbody>
                    {documents.map((document) => (
                      <tr key={document.document_id}>
                        <td><strong>{document.public_title}</strong><span>{document.relative_path}</span></td>
                        <td>{document.file_format}</td>
                        <td>{document.role_hint}</td>
                        <td>{document.key_topics.slice(0, 3).join(" / ")}</td>
                        <td>{parserStatusDisplay(document.parser_status)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
          <div className="tfl-table-block safety-wide-block">
            <h3>安全信号候选复核表</h3>
            <div className="tfl-table-scroll safety-candidate-table">
              <table>
                <thead>
                  <tr>
                    <th>候选类型</th>
                    <th>标题</th>
                    <th>优先级</th>
                    <th>来源域</th>
                    <th>观察</th>
                    <th>医学/PV边界</th>
                    <th>下一步</th>
                    <th>状态</th>
                  </tr>
                </thead>
                <tbody>
                  {candidates.map((candidate) => (
                    <tr key={candidate.signal_id}>
                      <td><strong>{candidate.signal_label}</strong><span>{candidate.signal_type}</span></td>
                      <td>{candidate.title}</td>
                      <td><Tag tone={statusClass(candidate.severity)}>{severityLabel(candidate.severity)}</Tag></td>
                      <td>{candidate.source_domains.slice(0, 5).join(" / ")}</td>
                      <td>{candidate.observation}</td>
                      <td>{candidate.medical_pv_boundary}</td>
                      <td>{candidate.recommended_next_step}</td>
                      <td>{candidate.confirmation_status}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
          <div className="tfl-table-block safety-wide-block">
            <h3>PV协同质量门</h3>
            <div className="tfl-table-scroll safety-gate-table">
              <table>
                <thead>
                  <tr>
                    <th>质量门</th>
                    <th>状态</th>
                    <th>负责角色</th>
                    <th>说明</th>
                    <th>来源</th>
                  </tr>
                </thead>
                <tbody>
                  {gates.map((gate) => (
                    <tr key={gate.gate_id}>
                      <td><strong>{gate.gate_label}</strong></td>
                      <td><Tag tone={safetyGateTone(gate.status)}>{gate.status === "ok" ? "通过" : gate.status === "warning" ? "需确认" : "阻断"}</Tag></td>
                      <td>{gate.owner}</td>
                      <td>{gate.detail}</td>
                      <td>{gate.source_refs.slice(0, 4).join("；") || "待补充"}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
          <div className="tfl-note-list">
            {(manifest.parser_notes || []).map((note) => <span key={note}>{note}</span>)}
          </div>
        </>
      ) : (
        <div className="empty-state">尚未生成安全资料清单。</div>
      )}
    </section>
  );
}

function PicosDecisionWorkspace({
  workflow,
  loading,
  message,
  selectedQuestionId,
  onSelectQuestion,
  rationales,
  setRationales,
  onAction,
  busyAction,
  onRefresh,
}) {
  const steps = workflow?.steps || [];
  const selectedStep = steps.find((step) => step.question_id === selectedQuestionId) || steps[0];
  const selectedOption = selectedStep?.options?.find((option) => option.option_id === selectedStep.selected_option_id);
  const rationaleValue = rationales[selectedStep?.question_id] ?? selectedStep?.user_rationale ?? "";
  const busyFor = (action) => selectedStep && busyAction === `${selectedStep.question_id}:${action}`;
  const canSaveRationale = Boolean(selectedStep?.selected_option_id && rationaleValue.trim());
  const canMarkCandidate = Boolean(selectedStep?.selected_option_id && (selectedStep?.user_rationale || rationaleValue.trim()));

  if (loading && !workflow) {
    return <div className="panel-subsection picos-loading">PICOS 决策工作台读取中...</div>;
  }
  if (!selectedStep) {
    return <div className="empty-state">尚未生成 PICOS 决策工作台。</div>;
  }

  return (
    <div className="picos-workflow-panel">
      <div className="picos-workflow-head">
        <div>
          <h3>{workflow?.workflow_label || "PICOS 决策工作台"}</h3>
          <p>{workflow?.formal_output_boundary || "PICOS输出仅作为待医学批准候选。"}</p>
        </div>
        <div className="picos-head-tags">
          <Tag tone="warning">待医学确认</Tag>
          <Tag tone={workflow?.ai_gateway_status === "configured" ? "success" : "warning"}>{workflow?.ai_gateway_status === "configured" ? "独立AI已配置" : "独立AI未配置"}</Tag>
          <Tag tone="neutral">codex_runtime_dependency=false</Tag>
          <button onClick={onRefresh} disabled={loading}>{loading ? "刷新中" : "刷新决策"}</button>
        </div>
      </div>
      {message && <div className="source-registry-message">{message}</div>}
      <div className="picos-workflow-stats">
        <div><strong>{workflow?.decision_count ?? 0}</strong><span>已选择</span></div>
        <div><strong>{workflow?.writing_candidate_count ?? 0}</strong><span>写作候选</span></div>
        <div><strong>{workflow?.blocking_gate_count ?? 0}</strong><span>阻断质量门</span></div>
        <div><strong>{steps.length}</strong><span>PICOS域</span></div>
      </div>
      <div className="picos-workflow-grid">
        <aside className="picos-question-list">
          {steps.map((step) => (
            <button
              key={step.question_id}
              className={step.question_id === selectedStep.question_id ? "active" : ""}
              onClick={() => onSelectQuestion(step.question_id)}
            >
              <span>{step.picos_domain}</span>
              <strong>{step.writing_target_section}</strong>
              <Tag tone={picosStatusTone(step.decision_status)}>{step.decision_status}</Tag>
            </button>
          ))}
        </aside>
        <section className="picos-decision-card">
          <div className="picos-card-top">
            <Tag tone={picosStatusTone(selectedStep.decision_status)}>{selectedStep.decision_status}</Tag>
            <Tag tone={safetyGateTone(selectedStep.quality_gate_status)}>{gateStatusLabel(selectedStep.quality_gate_status)}</Tag>
          </div>
          <h3>{selectedStep.question}</h3>
          <p>{selectedStep.current_evidence_summary}</p>
          <div className="picos-source-list">
            {selectedStep.source_refs.slice(0, 5).map((ref) => <span key={ref}>{ref}</span>)}
          </div>
          <div className="picos-option-list">
            {selectedStep.options.map((option) => (
              <button
                key={option.option_id}
                className={option.option_id === selectedStep.selected_option_id ? "selected" : ""}
                onClick={() => onAction(selectedStep.question_id, "select_option", { option_id: option.option_id, user_rationale: rationaleValue })}
                disabled={Boolean(busyAction)}
              >
                <strong>{option.label}</strong>
                <span>{option.design_summary}</span>
                <em>{option.medical_rationale_prompt}</em>
              </button>
            ))}
          </div>
          <label className="picos-rationale-box">
            <span>医学理由与项目口径</span>
            <textarea
              value={rationaleValue}
              onChange={(event) => setRationales((current) => ({ ...current, [selectedStep.question_id]: event.target.value }))}
              placeholder="填写选择理由、适用人群/终点/设计边界、需跨部门确认的事项"
            />
          </label>
          <div className="button-row">
            <button
              disabled={!canSaveRationale || Boolean(busyAction)}
              onClick={() => onAction(selectedStep.question_id, "save_rationale", { user_rationale: rationaleValue })}
            >
              {busyFor("save_rationale") ? "保存中" : "保存医学理由"}
            </button>
            <button
              className="primary-button"
              disabled={!canMarkCandidate || Boolean(busyAction)}
              onClick={() => onAction(selectedStep.question_id, "mark_writing_candidate", { user_rationale: rationaleValue, comment: "进入医学写作候选。" })}
            >
              {busyFor("mark_writing_candidate") ? "标记中" : "标记写作候选"}
            </button>
            <button
              disabled={Boolean(busyAction)}
              onClick={() => onAction(selectedStep.question_id, "return_for_evidence", { comment: "退回补充来源或跨部门确认。" })}
            >
              退回补证
            </button>
            <button
              disabled={Boolean(busyAction)}
              onClick={() => onAction(selectedStep.question_id, "reset_decision", { comment: "重置当前PICOS决策。" })}
            >
              重置
            </button>
          </div>
        </section>
        <aside className="picos-handoff-panel">
          <h3>写作流转预览</h3>
          <div className="handoff-box">
            <span>目标章节</span>
            <strong>{selectedStep.writing_target_section}</strong>
          </div>
          <div className="handoff-box">
            <span>当前候选</span>
            <strong>{selectedOption?.label || "尚未选择候选"}</strong>
            <p>{selectedOption?.design_summary || "请选择候选并填写医学理由后，再标记为写作候选。"}</p>
          </div>
          <div className="handoff-box">
            <span>流转状态</span>
            <Tag tone={selectedStep.writing_handoff_status === "可作为医学写作候选输入" ? "success" : "warning"}>{selectedStep.writing_handoff_status}</Tag>
          </div>
          <div className="handoff-box">
            <span>风险与未决项</span>
            {(selectedOption?.risk_notes?.length ? selectedOption.risk_notes : ["需医学批准后才可进入正式内容。"]).map((note) => <p key={note}>{note}</p>)}
          </div>
          <div className="picos-audit">
            <strong>审计轨迹</strong>
            {(selectedStep.audit_trail || []).length ? selectedStep.audit_trail.map((record) => (
              <div key={record.record_id}>
                <Tag tone="neutral">{picosActionLabel(record.action)}</Tag>
                <span>{record.to_status}</span>
                <small>{record.actor}</small>
              </div>
            )) : <p>暂无用户决策记录。</p>}
          </div>
        </aside>
      </div>
    </div>
  );
}

function EvidenceDesignManifestPanel({ manifest, loading, message, onRefresh, selectedPackageId, onSelectPackage }) {
  const packages = manifest?.packages || [];
  const selectedPackage = packages.find((item) => item.package_id === selectedPackageId) || packages[0];
  const products = selectedPackage ? selectedPackage.products.slice(0, 12) : [];
  const trials = selectedPackage ? selectedPackage.trial_designs.slice(0, 12) : [];
  const results = selectedPackage ? [...selectedPackage.efficacy_results, ...selectedPackage.safety_results].slice(0, 14) : [];
  const documents = selectedPackage ? selectedPackage.documents.slice(0, 10) : [];
  const gates = selectedPackage ? selectedPackage.quality_gates : [];
  const warnings = selectedPackage?.parser_warnings?.slice(0, 4) || [];
  const [picosWorkflow, setPicosWorkflow] = useState(null);
  const [picosLoading, setPicosLoading] = useState(false);
  const [picosMessage, setPicosMessage] = useState("");
  const [selectedPicosQuestionId, setSelectedPicosQuestionId] = useState("");
  const [picosRationales, setPicosRationales] = useState({});
  const [picosBusyAction, setPicosBusyAction] = useState("");

  const loadPicosWorkflow = () => {
    if (!selectedPackage?.package_id) return;
    setPicosLoading(true);
    setPicosMessage("");
    fetch(`/api/projects/${PROJECT_ID}/evidence-design/picos-workflow?package_id=${encodeURIComponent(selectedPackage.package_id)}`)
      .then((response) => response.ok ? response.json() : Promise.reject(response))
      .then((payload) => {
        setPicosWorkflow(payload);
        const steps = payload.steps || [];
        if (!steps.some((step) => step.question_id === selectedPicosQuestionId)) {
          setSelectedPicosQuestionId(steps[0]?.question_id || "");
        }
      })
      .catch((error) => setPicosMessage(`PICOS决策工作台读取失败：${error.status || error.message || "network"}`))
      .finally(() => setPicosLoading(false));
  };

  useEffect(() => {
    loadPicosWorkflow();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [selectedPackage?.package_id]);

  const submitPicosAction = async (questionId, action, extra = {}) => {
    if (!selectedPackage?.package_id) return;
    const actionKey = `${questionId}:${action}`;
    setPicosBusyAction(actionKey);
    setPicosMessage("");
    try {
      const response = await fetch(
        `/api/projects/${PROJECT_ID}/evidence-design/picos-workflow/${encodeURIComponent(selectedPackage.package_id)}/questions/${encodeURIComponent(questionId)}/actions`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ action, actor: "medical_manager", ...extra }),
        },
      );
      const payload = await response.json();
      if (!response.ok) throw new Error(payload.detail || `API ${response.status}`);
      setPicosWorkflow(payload);
      setPicosMessage(action === "mark_writing_candidate" ? "已标记为医学写作候选，仍需医学批准后才能进入正式内容。" : "PICOS决策已保存。");
    } catch (error) {
      setPicosMessage(`PICOS动作失败：${error.message}`);
    } finally {
      setPicosBusyAction("");
    }
  };

  return (
    <section className="panel tfl-manifest-panel evidence-design-panel">
      <SectionTitle
        title="竞品证据清单与PICOS设计队列"
        action={<button onClick={onRefresh} disabled={loading}>{loading ? "生成中" : "刷新证据清单"}</button>}
      />
      <div className="evidence-boundary">
        本工作面只展示来源可追溯的竞品证据、证据缺口和PICOS待决策问题；所有设计输出均为待医学确认/待医学批准内容，不代表已完成医学批准。
      </div>
      <div className="evidence-stats">
        <div><strong>{formatMaybeNumber(manifest?.total_products)}</strong><span>竞品/机制</span></div>
        <div><strong>{formatMaybeNumber(manifest?.total_trials)}</strong><span>试验设计</span></div>
        <div><strong>{formatMaybeNumber(manifest?.total_documents)}</strong><span>原始资料</span></div>
        <div><strong>{formatMaybeNumber(manifest?.total_result_rows)}</strong><span>结果行</span></div>
        <div><strong>{formatMaybeNumber(manifest?.picos_question_count)}</strong><span>PICOS问题</span></div>
        <div><strong>{formatMaybeNumber(manifest?.quality_gate_count)}</strong><span>质量门</span></div>
      </div>
      {message && <div className="source-registry-message">{message}</div>}
      <div className="tfl-package-tabs">
        {packages.map((item) => (
          <button
            key={item.package_id}
            className={item.package_id === selectedPackage?.package_id ? "active" : ""}
            onClick={() => onSelectPackage(item.package_id)}
          >
            {item.package_label}
          </button>
        ))}
      </div>
      {selectedPackage ? (
        <>
          <div className="tfl-package-summary evidence-package-summary">
            <div><span>适应症</span><strong>{selectedPackage.indication}</strong></div>
            <div><span>资料底座</span><strong>{selectedPackage.source_root_label}</strong></div>
            <div><span>资料角色</span><strong>{selectedPackage.package_role}</strong></div>
            <div><span>试验分布</span><strong>{Object.entries(selectedPackage.trial_count_by_phase).map(([key, value]) => `${key}:${value}`).join("；") || "未读取"}</strong></div>
            <div><span>结果覆盖</span><strong>{Object.entries(selectedPackage.endpoint_count_by_name).slice(0, 4).map(([key, value]) => `${key}:${value}`).join("；") || "未读取"}</strong></div>
          </div>
          <div className="tfl-quality-gates">
            <Tag tone="warning">待医学确认</Tag>
            <Tag tone="neutral">不使用既有深度报告作为输入</Tag>
            <Tag tone={selectedPackage.trial_designs.length ? "success" : "warning"}>竞品设计已登记</Tag>
            <Tag tone={selectedPackage.documents.length ? "success" : "warning"}>原始资料已登记</Tag>
            <Tag tone="warning">PICOS未批准</Tag>
          </div>
          {warnings.length ? (
            <div className="tfl-warning-list">
              {warnings.map((warning) => <span key={warning}>{warning}</span>)}
            </div>
          ) : null}

          <PicosDecisionWorkspace
            workflow={picosWorkflow}
            loading={picosLoading}
            message={picosMessage}
            selectedQuestionId={selectedPicosQuestionId}
            onSelectQuestion={setSelectedPicosQuestionId}
            rationales={picosRationales}
            setRationales={setPicosRationales}
            onAction={submitPicosAction}
            busyAction={picosBusyAction}
            onRefresh={loadPicosWorkflow}
          />

          <div className="evidence-picos-workbench">
            <div className="tfl-table-block">
              <h3>证据质量门</h3>
              <div className="tfl-table-scroll evidence-gate-table">
                <table>
                  <thead>
                    <tr>
                      <th>质量门</th>
                      <th>状态</th>
                      <th>负责角色</th>
                      <th>说明</th>
                      <th>来源</th>
                    </tr>
                  </thead>
                  <tbody>
                    {gates.map((gate) => (
                      <tr key={gate.gate_id}>
                        <td><strong>{gate.gate_label}</strong></td>
                        <td><Tag tone={safetyGateTone(gate.status)}>{gateStatusLabel(gate.status)}</Tag></td>
                        <td>{gate.owner}</td>
                        <td>{gate.detail}</td>
                        <td>{gate.source_refs.slice(0, 4).join("；")}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </div>

          <div className="tfl-table-block evidence-wide-block">
            <h3>竞品试验设计矩阵</h3>
            <div className="tfl-table-scroll evidence-trial-table">
              <table>
                <thead>
                  <tr>
                    <th>药物/研究</th>
                    <th>机制/申办方</th>
                    <th>分期/状态</th>
                    <th>地区/登记号</th>
                    <th>设计与样本量</th>
                    <th>干预/对照</th>
                    <th>主要终点</th>
                    <th>关键次要终点</th>
                    <th>Protocol/SAP/发表</th>
                    <th>证据状态</th>
                  </tr>
                </thead>
                <tbody>
                  {trials.map((trial) => (
                    <tr key={trial.trial_id}>
                      <td><strong>{trial.drug_name}</strong><span>{trial.trial_acronym || trial.trial_id}</span></td>
                      <td>{trial.target}<span>{trial.sponsor}</span></td>
                      <td>{trial.phase}<span>{trial.trial_status}</span></td>
                      <td>{trial.region}<span>{trial.registry_id}</span></td>
                      <td>{trial.design_type}<span>样本量：{trial.sample_size || "未披露"}</span></td>
                      <td>{trial.treatment_group}<span>对照：{trial.comparator || "待核对"}</span></td>
                      <td>{trial.primary_endpoint}<span>{trial.primary_timepoint}</span></td>
                      <td>{trial.key_secondary_endpoint || "待抽取"}</td>
                      <td>{trial.protocol_available} / {trial.sap_available} / {trial.publication_available}</td>
                      <td>{trial.verification_status}<span>{trial.evidence_level}</span></td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          <div className="tfl-manifest-grid">
            <div className="tfl-table-block">
              <h3>竞品概览</h3>
              <div className="tfl-table-scroll evidence-product-table">
                <table>
                  <thead>
                    <tr>
                      <th>竞品</th>
                      <th>机制</th>
                      <th>申办方</th>
                      <th>研究数</th>
                      <th>区域</th>
                      <th>状态线索</th>
                    </tr>
                  </thead>
                  <tbody>
                    {products.map((product) => (
                      <tr key={product.product_id}>
                        <td><strong>{product.drug_name}</strong></td>
                        <td>{product.target}</td>
                        <td>{product.sponsor}</td>
                        <td>{product.trial_count}</td>
                        <td>{Object.entries(product.region_summary).map(([key, value]) => `${key}:${value}`).join("；")}</td>
                        <td>{product.approval_status_hint}<span>{product.highest_evidence_level}</span></td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
            <div className="tfl-table-block">
              <h3>原始资料索引</h3>
              <div className="tfl-table-scroll evidence-doc-table">
                <table>
                  <thead>
                    <tr>
                      <th>资料</th>
                      <th>类型</th>
                      <th>药物/研究</th>
                      <th>用途</th>
                      <th>证据等级</th>
                    </tr>
                  </thead>
                  <tbody>
                    {documents.map((document) => (
                      <tr key={document.document_id}>
                        <td><strong>{document.public_title}</strong><span>{document.relative_path}</span></td>
                        <td>{document.document_type}</td>
                        <td>{document.drug_name}<span>{document.trial_identifier}</span></td>
                        <td>{document.role_hint}</td>
                        <td>{document.evidence_level}<span>{document.verification_status}</span></td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </div>

          <div className="tfl-table-block evidence-wide-block">
            <h3>疗效/安全性结果摘要</h3>
            <div className="tfl-table-scroll evidence-result-table">
              <table>
                <thead>
                  <tr>
                    <th>类型</th>
                    <th>药物/研究</th>
                    <th>终点</th>
                    <th>时间点</th>
                    <th>干预/对照</th>
                    <th>结果摘录</th>
                    <th>来源</th>
                    <th>边界</th>
                  </tr>
                </thead>
                <tbody>
                  {results.map((result) => (
                    <tr key={`${result.result_kind}:${result.result_id}`}>
                      <td>{result.result_kind === "safety" ? "安全性" : "疗效"}</td>
                      <td><strong>{result.drug_name}</strong><span>{result.trial_identifier || result.trial_id}</span></td>
                      <td>{result.endpoint_name}<span>{result.endpoint_type}</span></td>
                      <td>{result.timepoint || "未记录"}</td>
                      <td>{result.treatment_group}<span>对照：{result.comparator || "待核对"}</span></td>
                      <td>{result.effect_summary || "待抽取"}</td>
                      <td>{result.source_type}<span>{result.source_locator}</span></td>
                      <td>{result.medical_boundary}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          <div className="tfl-note-list">
            {(manifest.parser_notes || []).map((note) => <span key={note}>{note}</span>)}
          </div>
        </>
      ) : (
        <div className="empty-state">尚未生成竞品证据清单。</div>
      )}
    </section>
  );
}

function PlannedModulePage({ moduleKey }) {
  const config = plannedModuleContent[moduleKey];
  const candidates = sourceRegistryCandidates[moduleKey] || [];
  const [registry, setRegistry] = useState({ entries: [], spans: [] });
  const [loadingSources, setLoadingSources] = useState(false);
  const [registeringId, setRegisteringId] = useState("");
  const [message, setMessage] = useState("");
  const [aiTaskType, setAiTaskType] = useState(config.aiTasks[0] || "");
  const [runningAi, setRunningAi] = useState(false);
  const [evidenceManifest, setEvidenceManifest] = useState(null);
  const [evidenceManifestLoading, setEvidenceManifestLoading] = useState(false);
  const [evidenceManifestMessage, setEvidenceManifestMessage] = useState("");
  const [selectedEvidencePackageId, setSelectedEvidencePackageId] = useState("");
  const [tflManifest, setTflManifest] = useState(null);
  const [tflManifestLoading, setTflManifestLoading] = useState(false);
  const [tflManifestMessage, setTflManifestMessage] = useState("");
  const [selectedTflPackageId, setSelectedTflPackageId] = useState("");
  const [selectedTflOutputId, setSelectedTflOutputId] = useState("");
  const [tflReviewWorkbench, setTflReviewWorkbench] = useState(null);
  const [tflReviewLoading, setTflReviewLoading] = useState(false);
  const [tflReviewMessage, setTflReviewMessage] = useState("");
  const [tflActionLoading, setTflActionLoading] = useState("");
  const tflManifestInFlight = useRef(false);
  const tflReviewRequestId = useRef(0);
  const [safetyManifest, setSafetyManifest] = useState(null);
  const [safetyManifestLoading, setSafetyManifestLoading] = useState(false);
  const [safetyManifestMessage, setSafetyManifestMessage] = useState("");
  const [selectedSafetyPackageId, setSelectedSafetyPackageId] = useState("");
  const [selectedSafetySignalId, setSelectedSafetySignalId] = useState("");
  const [safetyReviewWorkbench, setSafetyReviewWorkbench] = useState(null);
  const [safetyReviewLoading, setSafetyReviewLoading] = useState(false);
  const [safetyReviewMessage, setSafetyReviewMessage] = useState("");
  const [safetyActionLoading, setSafetyActionLoading] = useState("");
  const [safetyReviewComment, setSafetyReviewComment] = useState("");
  const [safetyHandoffManifest, setSafetyHandoffManifest] = useState(null);
  const safetyReviewRequestId = useRef(0);

  const moduleEntries = registry.entries.filter((entry) => entry.module === config.module);
  const moduleSpans = registry.spans.filter((span) => span.module === config.module);
  const selectedSourceIds = moduleSpans.slice(0, 12).map((span) => span.source_id);

  const refreshSources = () => {
    setLoadingSources(true);
    fetch(`/api/projects/${PROJECT_ID}/sources`)
      .then((response) => (response.ok ? response.json() : Promise.reject(response)))
      .then((data) => setRegistry({ entries: data.entries || [], spans: data.spans || [] }))
      .catch((error) => setMessage(`原始资料登记读取失败：${error.status || error.message || "network"}`))
      .finally(() => setLoadingSources(false));
  };

  useEffect(() => {
    refreshSources();
  }, [moduleKey]);

  const refreshEvidenceManifest = () => {
    if (moduleKey !== "evidenceDesign") return;
    setEvidenceManifestLoading(true);
    setEvidenceManifestMessage("");
    fetch(`/api/projects/${PROJECT_ID}/evidence-design/manifest`)
      .then((response) => (response.ok ? response.json() : Promise.reject(response)))
      .then((data) => {
        setEvidenceManifest(data);
        const packageIds = (data.packages || []).map((item) => item.package_id);
        if (!packageIds.includes(selectedEvidencePackageId)) {
          setSelectedEvidencePackageId(packageIds[0] || "");
        }
      })
      .catch((error) => setEvidenceManifestMessage(`竞品证据清单生成失败：${error.status || error.message || "network"}`))
      .finally(() => setEvidenceManifestLoading(false));
  };

  useEffect(() => {
    if (moduleKey === "evidenceDesign") {
      refreshEvidenceManifest();
    } else {
      setEvidenceManifest(null);
      setEvidenceManifestMessage("");
      setSelectedEvidencePackageId("");
    }
  }, [moduleKey]);

  const refreshTflManifest = (forceRefresh = true) => {
    if (moduleKey !== "tfl") return Promise.resolve(false);
    if (!forceRefresh && tflManifestInFlight.current) return Promise.resolve(false);
    tflManifestInFlight.current = true;
    setTflManifestLoading(true);
    setTflManifestMessage("");
    const params = new URLSearchParams();
    params.set("force_refresh", forceRefresh ? "true" : "false");
    return fetch(`/api/projects/${PROJECT_ID}/tfl/manifest?${params.toString()}`)
      .then((response) => (response.ok ? response.json() : Promise.reject(response)))
      .then((data) => {
        setTflManifest(data);
        const packageIds = (data.packages || []).map((item) => item.package_id);
        if (!packageIds.includes(selectedTflPackageId)) {
          setSelectedTflPackageId(packageIds[0] || "");
        }
        return true;
      })
      .catch((error) => {
        setTflManifestMessage(`数据集与TFL清单生成失败：${error.status || error.message || "network"}`);
        return false;
      })
      .finally(() => {
        tflManifestInFlight.current = false;
        setTflManifestLoading(false);
      });
  };

  const refreshTflReviewWorkbench = (packageId = selectedTflPackageId, outputId = selectedTflOutputId) => {
    if (moduleKey !== "tfl") return Promise.resolve(false);
    const requestId = tflReviewRequestId.current + 1;
    tflReviewRequestId.current = requestId;
    setTflReviewLoading(true);
    setTflReviewMessage("");
    const params = new URLSearchParams();
    if (packageId) params.set("package_id", packageId);
    if (outputId) params.set("output_id", outputId);
    return fetch(`/api/projects/${PROJECT_ID}/tfl/review-workbench?${params.toString()}`)
      .then((response) => (response.ok ? response.json() : Promise.reject(response)))
      .then((data) => {
        if (requestId !== tflReviewRequestId.current) return false;
        setTflReviewWorkbench(data);
        if (data.package_id && data.package_id !== selectedTflPackageId) {
          setSelectedTflPackageId(data.package_id);
        }
        if (data.selected_output_id && data.selected_output_id !== selectedTflOutputId) {
          setSelectedTflOutputId(data.selected_output_id);
        }
        return true;
      })
      .catch((error) => {
        if (requestId === tflReviewRequestId.current) {
          setTflReviewMessage(`TFL审阅工作台读取失败：${error.status || error.message || "network"}`);
        }
        return false;
      })
      .finally(() => {
        if (requestId === tflReviewRequestId.current) setTflReviewLoading(false);
      });
  };

  useEffect(() => {
    if (moduleKey === "tfl") {
      refreshTflManifest(false);
    } else {
      setTflManifest(null);
      setTflManifestMessage("");
      setSelectedTflPackageId("");
      setSelectedTflOutputId("");
      setTflReviewWorkbench(null);
      setTflReviewMessage("");
    }
  }, [moduleKey]);

  useEffect(() => {
    if (moduleKey === "tfl" && selectedTflPackageId) {
      refreshTflReviewWorkbench(selectedTflPackageId, selectedTflOutputId);
    }
  }, [moduleKey, selectedTflPackageId, selectedTflOutputId]);

  const selectTflPackage = (packageId) => {
    setSelectedTflPackageId(packageId);
    setSelectedTflOutputId("");
  };

  const applyTflReviewAction = async (action, comment) => {
    const packageId = tflReviewWorkbench?.package_id || selectedTflPackageId;
    const outputId = tflReviewWorkbench?.selected_output_id || selectedTflOutputId;
    if (!packageId || !outputId) {
      setTflReviewMessage("请先选择TFL输出对象。");
      return false;
    }
    setTflActionLoading(action);
    setTflReviewMessage("");
    try {
      const response = await fetch(
        `/api/projects/${PROJECT_ID}/tfl/review-workbench/${encodeURIComponent(packageId)}/outputs/${encodeURIComponent(outputId)}/actions`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ action, actor: "medical_manager", comment }),
        },
      );
      const payload = await response.json();
      if (!response.ok) throw new Error(payload.detail || `API ${response.status}`);
      setTflReviewWorkbench(payload);
      setSelectedTflOutputId(payload.selected_output_id || outputId);
      setTflReviewMessage(`已更新审阅状态：${payload.current_status}`);
      return true;
    } catch (error) {
      setTflReviewMessage(`TFL审阅动作提交失败：${error.message}`);
      return false;
    } finally {
      setTflActionLoading("");
    }
  };

  const refreshSafetyManifest = () => {
    if (moduleKey !== "safety") return;
    setSafetyManifestLoading(true);
    setSafetyManifestMessage("");
    fetch(`/api/projects/${PROJECT_ID}/safety-pv/manifest`)
      .then((response) => (response.ok ? response.json() : Promise.reject(response)))
      .then((data) => {
        setSafetyManifest(data);
        const packageIds = (data.packages || []).map((item) => item.package_id);
        if (!packageIds.includes(selectedSafetyPackageId)) {
          setSelectedSafetyPackageId(packageIds[0] || "");
        }
      })
      .catch((error) => setSafetyManifestMessage(`安全资料清单生成失败：${error.status || error.message || "network"}`))
      .finally(() => setSafetyManifestLoading(false));
  };

  const refreshSafetyReviewWorkbench = (packageId = selectedSafetyPackageId, signalId = selectedSafetySignalId) => {
    if (moduleKey !== "safety") return Promise.resolve(false);
    const requestId = safetyReviewRequestId.current + 1;
    safetyReviewRequestId.current = requestId;
    setSafetyReviewLoading(true);
    setSafetyReviewMessage("");
    const params = new URLSearchParams();
    if (packageId) params.set("package_id", packageId);
    if (signalId) params.set("signal_id", signalId);
    return fetch(`/api/projects/${PROJECT_ID}/safety-pv/review-workbench?${params.toString()}`)
      .then((response) => (response.ok ? response.json() : Promise.reject(response)))
      .then((data) => {
        if (requestId !== safetyReviewRequestId.current) return false;
        setSafetyReviewWorkbench(data);
        if (data.package_id && data.package_id !== selectedSafetyPackageId) {
          setSelectedSafetyPackageId(data.package_id);
        }
        if (data.selected_signal_id && data.selected_signal_id !== selectedSafetySignalId) {
          setSelectedSafetySignalId(data.selected_signal_id);
        }
        return true;
      })
      .catch((error) => {
        if (requestId === safetyReviewRequestId.current) {
          setSafetyReviewMessage(`安全信号审阅工作台读取失败：${error.status || error.message || "network"}`);
        }
        return false;
      })
      .finally(() => {
        if (requestId === safetyReviewRequestId.current) setSafetyReviewLoading(false);
      });
  };

  const refreshSafetyHandoff = () => {
    if (moduleKey !== "safety") return Promise.resolve(false);
    return fetch(`/api/projects/${PROJECT_ID}/safety-pv/handoff-candidates`)
      .then((response) => (response.ok ? response.json() : Promise.reject(response)))
      .then((data) => {
        setSafetyHandoffManifest(data);
        return true;
      })
      .catch((error) => {
        setSafetyReviewMessage(`PV协同交接候选读取失败：${error.status || error.message || "network"}`);
        return false;
      });
  };

  useEffect(() => {
    if (moduleKey === "safety") {
      refreshSafetyManifest();
      refreshSafetyHandoff();
    } else {
      setSafetyManifest(null);
      setSafetyManifestMessage("");
      setSelectedSafetyPackageId("");
      setSelectedSafetySignalId("");
      setSafetyReviewWorkbench(null);
      setSafetyReviewMessage("");
      setSafetyReviewComment("");
      setSafetyHandoffManifest(null);
    }
  }, [moduleKey]);

  useEffect(() => {
    if (moduleKey === "safety" && selectedSafetyPackageId) {
      refreshSafetyReviewWorkbench(selectedSafetyPackageId, selectedSafetySignalId);
    }
  }, [moduleKey, selectedSafetyPackageId, selectedSafetySignalId]);

  const selectSafetyPackage = (packageId) => {
    setSelectedSafetyPackageId(packageId);
    setSelectedSafetySignalId("");
    setSafetyReviewComment("");
  };

  const selectSafetySignal = (signalId) => {
    setSelectedSafetySignalId(signalId);
    setSafetyReviewComment("");
  };

  const applySafetyReviewAction = async (action, comment) => {
    const packageId = safetyReviewWorkbench?.package_id || selectedSafetyPackageId;
    const signalId = safetyReviewWorkbench?.selected_signal_id || selectedSafetySignalId;
    if (!packageId || !signalId) {
      setSafetyReviewMessage("请先选择安全信号候选。");
      return false;
    }
    setSafetyActionLoading(action);
    setSafetyReviewMessage("");
    try {
      const response = await fetch(
        `/api/projects/${PROJECT_ID}/safety-pv/review-workbench/${encodeURIComponent(packageId)}/signals/${encodeURIComponent(signalId)}/actions`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ action, actor: "medical_manager", comment }),
        },
      );
      const payload = await response.json();
      if (!response.ok) throw new Error(payload.detail || `API ${response.status}`);
      setSafetyReviewWorkbench(payload);
      setSelectedSafetySignalId(payload.selected_signal_id || signalId);
      setSafetyReviewMessage(`已更新审阅状态：${payload.current_status}`);
      if (action === "request_pv_confirmation" || action === "reset_review" || action === "accept_no_action") {
        await refreshSafetyHandoff();
      }
      return true;
    } catch (error) {
      setSafetyReviewMessage(`安全信号审阅动作提交失败：${error.message}`);
      return false;
    } finally {
      setSafetyActionLoading("");
    }
  };

  const registerCandidate = async (candidate) => {
    setRegisteringId(candidate.id);
    setMessage("");
    const params = new URLSearchParams();
    params.set("candidate_id", candidate.id);
    params.set("module", candidate.module);
    try {
      const response = await fetch(`/api/projects/${PROJECT_ID}/sources/local-candidate?${params.toString()}`, { method: "POST" });
      const payload = await response.json();
      if (!response.ok) throw new Error(payload.detail || `API ${response.status}`);
      setMessage(`${candidate.title} 已登记：${payload.entry?.span_count || 0} 个证据片段。`);
      refreshSources();
    } catch (error) {
      setMessage(`${candidate.title} 登记失败：${error.message}`);
    } finally {
      setRegisteringId("");
    }
  };

  const submitAiTask = async () => {
    if (!selectedSourceIds.length) {
      setMessage("请先登记至少一个原始资料证据片段，再准备 AI 任务。");
      return;
    }
    setRunningAi(true);
    setMessage("");
    try {
      const response = await fetch(`/api/projects/${PROJECT_ID}/ai-runs/from-sources`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          module: config.module,
          task_type: aiTaskType,
          prompt_version: `${aiTaskType}_v0_1`,
          source_ids: selectedSourceIds,
          forbidden_source_ids: ["legacy_deep_dive_report", "generated_html_reference", "previous_ai_summary"],
          user_instruction: `仅基于已登记的原始证据片段，为${config.title}准备待医学确认的结构化输出。`,
        }),
      });
      const payload = await response.json();
      if (!response.ok) throw new Error(payload.detail || `API ${response.status}`);
      setMessage(payload.status === "blocked" ? "AI 任务已建立，但外部模型服务未配置；已记录 blocked run。" : `AI 任务已提交：${payload.status}`);
    } catch (error) {
      setMessage(`AI 任务准备失败：${error.message}`);
    } finally {
      setRunningAi(false);
    }
  };

  return (
    <main className="page">
      <SectionTitle eyebrow={config.eyebrow} title={config.title} />
      <section className="panel">
        <div className="approval-meta">
          <Tag tone="info">{config.status}</Tag>
          <Tag tone="warning">{moduleKey === "safety" ? "待医学/PV确认" : "待医学确认"}</Tag>
          <Tag tone="neutral">医学相关模块</Tag>
          {moduleKey === "safety" && <Tag tone="neutral">不替代PV系统</Tag>}
          {moduleKey === "evidenceDesign" && <Tag tone="neutral">设计建议候选</Tag>}
        </div>
        <p className="module-summary">{config.summary}</p>
      </section>
      {moduleKey === "evidenceDesign" && (
        <EvidenceDesignManifestPanel
          manifest={evidenceManifest}
          loading={evidenceManifestLoading}
          message={evidenceManifestMessage}
          onRefresh={refreshEvidenceManifest}
          selectedPackageId={selectedEvidencePackageId}
          onSelectPackage={setSelectedEvidencePackageId}
        />
      )}
      {moduleKey === "safety" && (
        <SafetyPvManifestPanel
          manifest={safetyManifest}
          loading={safetyManifestLoading}
          message={safetyManifestMessage}
          onRefresh={refreshSafetyManifest}
          selectedPackageId={selectedSafetyPackageId}
          onSelectPackage={selectSafetyPackage}
          selectedSignalId={selectedSafetySignalId}
          onSelectSignal={selectSafetySignal}
          reviewWorkbench={safetyReviewWorkbench}
          reviewLoading={safetyReviewLoading}
          reviewMessage={safetyReviewMessage}
          reviewComment={safetyReviewComment}
          setReviewComment={setSafetyReviewComment}
          onReviewAction={applySafetyReviewAction}
          applyingReviewAction={safetyActionLoading}
          handoffManifest={safetyHandoffManifest}
          onRefreshHandoff={refreshSafetyHandoff}
        />
      )}
      <section className="panel source-registry-panel">
        <SectionTitle
          title="原始资料登记"
          action={<button onClick={refreshSources} disabled={loadingSources}>{loadingSources ? "读取中" : "刷新"}</button>}
        />
        <div className="source-stats">
          <div><strong>{moduleEntries.length}</strong><span>已登记资料包</span></div>
          <div><strong>{moduleSpans.length}</strong><span>证据片段</span></div>
          <div><strong>{selectedSourceIds.length}</strong><span>本次 AI 任务预选</span></div>
          <div><strong>{config.aiTasks.length}</strong><span>AI 任务类型</span></div>
        </div>
        {message && <div className="source-registry-message">{message}</div>}
        <div className="source-candidate-grid">
          {candidates.map((candidate) => (
            <article className="source-candidate-card" key={candidate.id}>
              <div>
                <Tag tone={candidate.kind === "local-file" ? "info" : "neutral"}>{sourceTypeLabel(candidate.sourceType)}</Tag>
                <h3>{candidate.title}</h3>
                <p>{candidate.purpose}</p>
                <span className="source-candidate-label">{candidate.title}</span>
              </div>
              <button onClick={() => registerCandidate(candidate)} disabled={Boolean(registeringId)}>
                {registeringId === candidate.id ? "登记中" : "登记"}
              </button>
            </article>
          ))}
        </div>
        <div className="registered-source-list">
          {moduleEntries.length ? moduleEntries.map((entry) => (
            <div className="registered-source-row" key={entry.entry_id}>
              <Tag tone={entry.parser_status === "parsed" ? "success" : "warning"}>{parserStatusLabel(entry.parser_status)}</Tag>
              <strong>{entry.public_title}</strong>
              <span>{sourceKindLabel(entry.source_kind)}</span>
              <span>{entry.span_count} 片段</span>
              <span>{compactLabel(entry.entry_id, 18)}</span>
            </div>
          )) : <div className="empty-state">当前模块尚未登记原始资料。</div>}
        </div>
      </section>
      {moduleKey === "tfl" && (
        <TflManifestPanel
          manifest={tflManifest}
          loading={tflManifestLoading}
          message={tflManifestMessage}
          onRefresh={() => refreshTflManifest(true)}
          selectedPackageId={selectedTflPackageId}
          onSelectPackage={selectTflPackage}
          reviewWorkbench={tflReviewWorkbench}
          reviewLoading={tflReviewLoading}
          reviewMessage={tflReviewMessage}
          selectedOutputId={selectedTflOutputId}
          onSelectOutput={setSelectedTflOutputId}
          onRefreshReview={() => refreshTflReviewWorkbench(selectedTflPackageId, selectedTflOutputId)}
          onApplyReviewAction={applyTflReviewAction}
          applyingReviewAction={tflActionLoading}
        />
      )}
      <section className="panel ai-task-prep-panel">
        <SectionTitle title="独立 AI 任务准备" />
        <div className="ai-task-prep">
          <label>
            <span>任务类型</span>
            <select value={aiTaskType} onChange={(event) => setAiTaskType(event.target.value)}>
              {config.aiTasks.map((task) => <option key={task} value={task}>{aiTaskDisplayName(task)}</option>)}
            </select>
          </label>
          <div className="selected-source-chips">
            {selectedSourceIds.length ? selectedSourceIds.map((sourceId) => (
              <Tag key={sourceId} tone="neutral">{sourceId.slice(0, 32)}</Tag>
            )) : <span>暂无可用 source_id</span>}
          </div>
          <button className="primary-button" onClick={submitAiTask} disabled={runningAi || !aiTaskType}>
            {runningAi ? "准备中" : "准备 AI 任务"}
          </button>
        </div>
      </section>
      <div className="overview-grid">
        <section className="panel">
          <SectionTitle title="正式输入" />
          <div className="task-list">
            {config.inputs.map((item) => (
              <div className="task-row" key={item}>
                <span><Tag tone="info">来源</Tag></span>
                <strong>{item}</strong>
                <span>原始资料</span>
                <span>待索引</span>
              </div>
            ))}
          </div>
        </section>
        <section className="panel">
          <SectionTitle title="AI 任务" />
          <div className="task-list">
            {config.aiTasks.map((item) => (
              <div className="task-row" key={item}>
                <span><Tag tone="warning">任务</Tag></span>
                <strong>{aiTaskDisplayName(item)}</strong>
                <span>需独立模型服务</span>
                <span>未启用</span>
              </div>
            ))}
          </div>
        </section>
        <section className="panel">
          <SectionTitle title="下一步" />
          <div className="task-list">
            {config.next.map((item, index) => (
              <div className="task-row" key={item}>
                <span><Tag tone="neutral">{index + 1}</Tag></span>
                <strong>{item}</strong>
                <span>产品化任务</span>
                <span>P0/P1</span>
              </div>
            ))}
          </div>
        </section>
      </div>
    </main>
  );
}

function ApprovalPage({ dashboard, refreshDashboard }) {
  const approvalRows = useMemo(() => {
    const source = dashboard.pending_approvals?.length ? dashboard.pending_approvals : approvalItems;
    return source.map(normalizeApprovalItem);
  }, [dashboard.pending_approvals]);
  const [selectedId, setSelectedId] = useState(approvalRows[0]?.id || "");
  const selected = approvalRows.find((item) => item.id === selectedId) || approvalRows[0] || normalizeApprovalItem(approvalItems[0]);
  const [comment, setComment] = useState("");
  const [approvalMessage, setApprovalMessage] = useState("");
  const [serverBlockers, setServerBlockers] = useState([]);
  const [actionLoading, setActionLoading] = useState(false);
  const displayedBlockers = serverBlockers.length ? serverBlockers.map((item) => item.message || item.blocker_type) : selected.blockers;
  const hasBlockers = displayedBlockers.length > 0;

  useEffect(() => {
    if (approvalRows.length && !approvalRows.some((item) => item.id === selectedId)) {
      setSelectedId(approvalRows[0].id);
    }
  }, [approvalRows, selectedId]);

  const selectApproval = (item) => {
    setSelectedId(item.id);
    setApprovalMessage("");
    setServerBlockers([]);
    setComment(item.comments || "");
  };

  const submitApprovalAction = async (action) => {
    setActionLoading(true);
    setApprovalMessage("");
    setServerBlockers([]);
    try {
      const response = await fetch(`/api/projects/${PROJECT_ID}/approvals/${selected.id}/actions`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ action, actor: "medical_manager", comment }),
      });
      const payload = await response.json();
      const result = response.ok ? payload : payload.detail || payload;
      if (!response.ok && response.status !== 409) throw new Error(result?.detail || `API ${response.status}`);
      if (result.blockers?.length) setServerBlockers(result.blockers);
      if (response.status === 409) {
        setApprovalMessage("质量门未通过：后端已记录阻断审计，审批状态未改变。");
        return;
      }
      setApprovalMessage(
        action === "approve"
          ? selected.isRuxDisposition
            ? "已批准内部Query草稿/处置建议并写入审计；尚未执行对外Query、风险关闭或归档。"
            : "已批准待医学确认内容并写入审计。"
          : action === "return_for_revision"
            ? "已退回修订并写入审计。"
            : action === "reject"
              ? "已驳回并标记为作废。"
              : "已读取后端质量门结果。"
      );
      refreshDashboard?.();
    } catch (error) {
      setApprovalMessage(`审批动作失败：${error.message}`);
    } finally {
      setActionLoading(false);
    }
  };

  return (
    <main className="page">
      <SectionTitle
        eyebrow="审批中心"
        title="待医学批准内容"
        action={<button className="primary-button" disabled={actionLoading} onClick={() => submitApprovalAction("view_quality_gate")}>查看质量门</button>}
      />
      <div className="approval-layout">
        <section className="panel approval-list">
          {approvalRows.map((item) => (
            <button key={item.id} className={selected.id === item.id ? "selected" : ""} onClick={() => selectApproval(item)}>
              <strong>{item.title}</strong>
              <span>{item.type}</span>
              <Tag tone={statusClass(item.state)}>{item.state}</Tag>
            </button>
          ))}
        </section>
        <section className="panel approval-detail">
          <SectionTitle title={selected.title} />
          <div className="approval-meta">
            <Tag tone="info">{selected.type}</Tag>
            <Tag tone={statusClass(selected.state)}>{selected.state}</Tag>
            <Tag tone={hasBlockers ? "warning" : "success"}>{selected.risk}</Tag>
          </div>
          <div className="detail-grid">
            <div><strong>AI 标记</strong><span>{selected.ai}</span></div>
            <div><strong>负责人</strong><span>{selected.owner}</span></div>
            <div><strong>证据覆盖</strong><span>68%</span></div>
            <div><strong>审计记录</strong><span>12 条</span></div>
          </div>
          <div className={hasBlockers ? "approval-blockers" : "approval-clear"}>
            <strong>{hasBlockers ? "质量门阻断" : "质量门通过"}</strong>
            {hasBlockers ? displayedBlockers.map((item) => <p key={item}>{item}</p>) : (
              <p>{selected.isRuxDisposition ? "无内部审批阻断；允许进入内部医学审阅，不代表对外Query、风险关闭或归档。" : "无开放 AI 修订、无高风险阻断项，允许进入医学批准。"}</p>
            )}
          </div>
          {selected.internalApprovalBoundary && <p className="boundary-note">{selected.internalApprovalBoundary}</p>}
          <textarea value={comment} onChange={(event) => setComment(event.target.value)} placeholder="填写审批意见，退回或批准均需留痕" />
          {approvalMessage && <div className="approval-message">{approvalMessage}</div>}
          <div className="button-row">
            <button
              className="primary-button"
              disabled={actionLoading || !comment.trim()}
              onClick={() => submitApprovalAction("approve")}
            >
              {actionLoading ? "处理中" : "批准"}
            </button>
            <button disabled={actionLoading || !comment.trim()} onClick={() => submitApprovalAction("return_for_revision")}>退回修订</button>
            <button disabled={actionLoading || !comment.trim()} onClick={() => submitApprovalAction("reject")}>驳回</button>
          </div>
        </section>
      </div>
    </main>
  );
}

export function App() {
  const [activePage, setActivePage] = useState("overview");
  const [dashboard, setDashboard] = useState(fallbackDashboard);
  const [sourceManifests, setSourceManifests] = useState({});
  const [workbenchInbox, setWorkbenchInbox] = useState(null);
  const [monitoringWorkbenchInbox, setMonitoringWorkbenchInbox] = useState(null);
  const [selectedSubject, setSelectedSubject] = useState(DEFAULT_SUBJECT_ID || subjects[0].id);
  const [monitoringSubjectCatalog, setMonitoringSubjectCatalog] = useState(subjects);
  const [subjectProfiles, setSubjectProfiles] = useState({});
  const [aiGatewayStatus, setAiGatewayStatus] = useState(null);
  const [aiRuns, setAiRuns] = useState([]);

  useEffect(() => {
    let cancelled = false;
    fetch(`/api/projects/${PROJECT_ID}/dashboard`)
      .then((response) => (response.ok ? response.json() : Promise.reject(response)))
      .then((data) => {
        if (!cancelled) {
          const normalizedModules = (data.modules || []).map((module) => ({
            ...module,
            label: moduleLabels[module.module] || module.label,
          }));
          setDashboard({ ...data, modules: normalizedModules });
        }
      })
      .catch(() => {
        if (!cancelled) setDashboard(fallbackDashboard);
      });
    return () => {
      cancelled = true;
    };
  }, []);

  useEffect(() => {
    let cancelled = false;
    const projectIds = Array.from(new Set([
      PROJECT_ID,
      RAW_ELIGIBILITY_PROJECT_ID,
      RAW_MONITORING_PROJECT_ID,
      RAW_TFL_PROJECT_ID,
      RAW_SAFETY_PROJECT_ID,
    ]));
    Promise.all(
      projectIds.map((projectId) => (
        fetch(`/api/projects/${projectId}/source-manifest`)
          .then((response) => (response.ok ? response.json() : null))
          .then((manifest) => [projectId, manifest])
          .catch(() => [projectId, null])
      )),
    ).then((entries) => {
      if (cancelled) return;
      setSourceManifests(Object.fromEntries(entries.filter(([, manifest]) => manifest)));
    });
    return () => {
      cancelled = true;
    };
  }, []);

  useEffect(() => {
    let cancelled = false;
    fetch("/api/ai-gateway/status")
      .then((response) => (response.ok ? response.json() : Promise.reject(response)))
      .then((data) => {
        if (!cancelled) setAiGatewayStatus(data);
      })
      .catch(() => {
        if (!cancelled) setAiGatewayStatus({ configured: false, semantic_ai_tasks_enabled: false, codex_runtime_dependency: false, provider: "unknown", model: "not_configured", missing_env: [] });
      });
    fetch(`/api/projects/${PROJECT_ID}/ai-runs`)
      .then((response) => (response.ok ? response.json() : Promise.reject(response)))
      .then((data) => {
        if (!cancelled) setAiRuns(Array.isArray(data) ? data : []);
      })
      .catch(() => {
        if (!cancelled) setAiRuns([]);
      });
    return () => {
      cancelled = true;
    };
  }, []);

  const refreshDashboard = () => {
    fetch(`/api/projects/${PROJECT_ID}/dashboard`)
      .then((response) => (response.ok ? response.json() : Promise.reject(response)))
      .then((data) => {
        const normalizedModules = (data.modules || []).map((module) => ({
          ...module,
          label: moduleLabels[module.module] || module.label,
        }));
        setDashboard({ ...data, modules: normalizedModules });
      })
      .catch(() => undefined);
  };

  const refreshWorkbenchInbox = (payload) => {
    if (payload) {
      setWorkbenchInbox(payload);
      return;
    }
    fetch(`/api/projects/${PROJECT_ID}/workbench-inbox`)
      .then((response) => (response.ok ? response.json() : Promise.reject(response)))
      .then((data) => setWorkbenchInbox(data))
      .catch(() => undefined);
  };

  const refreshMonitoringWorkbenchInbox = (payload) => {
    if (payload) {
      setMonitoringWorkbenchInbox(payload);
      return;
    }
    fetch(`/api/projects/${RAW_MONITORING_PROJECT_ID}/workbench-inbox`)
      .then((response) => (response.ok ? response.json() : Promise.reject(response)))
      .then((data) => setMonitoringWorkbenchInbox(data))
      .catch(() => undefined);
  };

  useEffect(() => {
    let cancelled = false;
    fetch(`/api/projects/${PROJECT_ID}/workbench-inbox`)
      .then((response) => (response.ok ? response.json() : Promise.reject(response)))
      .then((data) => {
        if (!cancelled) setWorkbenchInbox(data);
      })
      .catch(() => {
        if (!cancelled) setWorkbenchInbox({ items: [], module_summaries: [], unread_count: 0, handoff_count: 0, total_open_count: 0 });
      });
    return () => {
      cancelled = true;
    };
  }, []);

  useEffect(() => {
    let cancelled = false;
    fetch(`/api/projects/${RAW_MONITORING_PROJECT_ID}/workbench-inbox`)
      .then((response) => (response.ok ? response.json() : Promise.reject(response)))
      .then((data) => {
        if (!cancelled) setMonitoringWorkbenchInbox(data);
      })
      .catch(() => {
        if (!cancelled) setMonitoringWorkbenchInbox(null);
      });
    return () => {
      cancelled = true;
    };
  }, []);

  useEffect(() => {
    let cancelled = false;
    fetch(`/api/projects/${RAW_MONITORING_PROJECT_ID}/monitoring/subjects`)
      .then((response) => (response.ok ? response.json() : Promise.reject(response)))
      .then((data) => {
        if (cancelled) return;
        const nextSubjects = Array.isArray(data.subjects) && data.subjects.length ? data.subjects : subjects;
        setMonitoringSubjectCatalog(nextSubjects);
        setSelectedSubject((current) => {
          if (current && nextSubjects.some((item) => item.id === current)) return current;
          if (DEFAULT_SUBJECT_ID && nextSubjects.some((item) => item.id === DEFAULT_SUBJECT_ID)) return DEFAULT_SUBJECT_ID;
          return nextSubjects[0]?.id || current || subjects[0].id;
        });
      })
      .catch(() => {
        if (!cancelled) setMonitoringSubjectCatalog(subjects);
      });
    return () => {
      cancelled = true;
    };
  }, []);

  const selectedSubjectProfile = subjectProfiles[selectedSubject];

  useEffect(() => {
    if (!selectedSubject || selectedSubjectProfile) return undefined;
    let cancelled = false;
    fetch(`/api/projects/${RAW_MONITORING_PROJECT_ID}/subjects/${selectedSubject}/monitoring`)
      .then((response) => (response.ok ? response.json() : Promise.reject(response)))
      .then((data) => {
        if (!cancelled) {
          setSubjectProfiles((current) => ({ ...current, [selectedSubject]: data }));
        }
      })
      .catch(() => undefined);
    return () => {
      cancelled = true;
    };
  }, [selectedSubject, selectedSubjectProfile]);

  const page = useMemo(() => {
    const subject = buildSubjectView(
      selectedSubjectProfile,
      selectedSubject,
      riskRows.find((risk) => risk.subject === selectedSubject),
      monitoringSubjectCatalog,
    );
    if (activePage === "overview") {
      return (
        <OverviewPage
          dashboard={dashboard}
          workbenchInbox={workbenchInbox}
          setActivePage={setActivePage}
          setSelectedSubject={setSelectedSubject}
          aiGatewayStatus={aiGatewayStatus}
          aiRuns={aiRuns}
          refreshWorkbenchInbox={refreshWorkbenchInbox}
        />
      );
    }
    if (activePage === "evidenceDesign") return <PlannedModulePage moduleKey="evidenceDesign" />;
    if (activePage === "eligibility") return <EligibilityPage />;
    if (activePage === "monitoring") {
      return (
        <MonitoringPage
          monitoringProjectId={RAW_MONITORING_PROJECT_ID}
          sourceManifest={sourceManifests[RAW_MONITORING_PROJECT_ID]}
          selectedSubject={selectedSubject}
          setSelectedSubject={setSelectedSubject}
          subjectProfile={selectedSubjectProfile}
          setActivePage={setActivePage}
          refreshDashboard={refreshDashboard}
          workbenchInbox={monitoringWorkbenchInbox || workbenchInbox}
          refreshWorkbenchInbox={refreshMonitoringWorkbenchInbox}
        />
      );
    }
    if (activePage === "subjectTimeline") {
      return (
        <SubjectTimelinePage
          subject={subject}
          setSelectedSubject={setSelectedSubject}
          setActivePage={setActivePage}
          subjectCatalog={monitoringSubjectCatalog}
        />
      );
    }
    if (activePage === "patientProfile") {
      return (
        <PatientProfilePage
          subject={subject}
          setSelectedSubject={setSelectedSubject}
          setActivePage={setActivePage}
          subjectCatalog={monitoringSubjectCatalog}
        />
      );
    }
    if (activePage === "tfl") return <PlannedModulePage moduleKey="tfl" />;
    if (activePage === "writing") return <WritingPage />;
    if (activePage === "safety") return <PlannedModulePage moduleKey="safety" />;
    return <ApprovalPage dashboard={dashboard} refreshDashboard={refreshDashboard} />;
  }, [activePage, dashboard, sourceManifests, workbenchInbox, monitoringWorkbenchInbox, selectedSubject, selectedSubjectProfile, monitoringSubjectCatalog, aiGatewayStatus, aiRuns]);

  const shellWorkbenchInbox = ["monitoring", "subjectTimeline", "patientProfile"].includes(activePage)
    ? (monitoringWorkbenchInbox || workbenchInbox)
    : workbenchInbox;

  return (
    <AppShell activePage={activePage} setActivePage={setActivePage} dashboard={dashboard} sourceManifests={sourceManifests} workbenchInbox={shellWorkbenchInbox}>
      {page}
    </AppShell>
  );
}
