import { memo, startTransition, useCallback, useEffect, useLayoutEffect, useMemo, useRef, useState } from "react";
import {
  createMedicalMonitoringR5Adapter,
  MedicalMonitoringR5AdapterError,
} from "./medicalMonitoringR5Adapter.mjs";
import {
  MEDICAL_MONITORING_R5_VIEWS,
  normalizeMedicalMonitoringR5RouteState,
  routeStateForMedicalMonitoringR5View,
} from "./medicalMonitoringR5RouteState.mjs";
import { layoutJourneyTimeline, parseTimelineDate, visitAxisDate } from "./medicalMonitoringR5Timeline.mjs";
import { DomainIcon } from "./DomainIcon.jsx";
import { MedicalMonitoringR7ProgressPanel } from "../MedicalMonitoringR7ProgressPanel.jsx";
import { MedicalMonitoringR7ProductLoop } from "../MedicalMonitoringR7ProductLoop.jsx";
import {
  MedicalMonitoringR7JourneyDrawer,
  R7_JOURNEY_AXIS_TITLE_ID,
  R7JourneyChangeMarker,
  r7JourneyDrawerLayoutMode,
  r7JourneyDrawerSections,
} from "../MedicalMonitoringR7JourneyDrawer.jsx";
import {
  bindR7ContinuityRowsToJourney,
  r7EventChangeMarker,
  r7JourneyContinuityRows,
  r7JourneyDrawerClosePatch,
  r7JourneyDrawerCurrentRow,
  r7JourneyTruncationText,
} from "../medicalMonitoringR7JourneyChanges.mjs";
import "./medicalMonitoringR5.css";

const VIEW_LABELS = Object.freeze({
  overview: "项目风险概览",
  site_overview: "中心风险图谱",
  journey: "受试者医学旅程",
  profile: "指标趋势",
  timeline: "事件明细",
  evidence: "风险证据",
});

const SUBJECT_VIEW_KEYS = Object.freeze(["journey", "profile", "timeline"]);
const SUBJECT_VIEW_LABELS = Object.freeze({ journey: "旅程总览", profile: "指标趋势", timeline: "事件明细" });

const DOMAIN_LABELS = Object.freeze({
  ae: "AE",
  mh: "MH",
  cm: "合并用药",
  ip: "试验用药",
  lab_exam: "检验检查",
  hospital_procedure: "诊疗操作",
  symptom_efficacy: "疗效/症状",
  protocol_compliance: "方案执行",
});

/** Soft-break lane chips so wraps stay 2+2 (or slash-balanced), never 3+1 orphans. */
function laneChipLabel(label) {
  const s = String(label || "");
  if (s.length <= 3) return s;
  const slash = s.indexOf("/");
  if (slash > 0 && slash < s.length - 1) {
    return `${s.slice(0, slash + 1)}\u200B${s.slice(slash + 1)}`;
  }
  if (s.length % 2 === 1) {
    return `${s.slice(0, 2)}\u200B${s.slice(2)}`;
  }
  let out = "";
  for (let i = 0; i < s.length; i += 2) {
    if (i) out += "\u200B";
    out += s.slice(i, i + 2);
  }
  return out;
}

const HISTORY_LABELS = Object.freeze({
  exact: "已确认同一记录",
  ambiguous: "仍需核对",
  rejected: "已排除关联",
});

const DATE_STATE_LABELS = Object.freeze({
  exact: "精确日期",
  partial: "日期部分明确",
  conflicted: "日期存在冲突",
  missing: "日期待确认",
});

const DATE_STATE_CHIPS = Object.freeze({
  exact: "精确日期",
  partial: "部分日期",
  conflicted: "日期冲突",
  missing: "日期缺失",
});

const SEMANTIC_ZOOM_LABELS = Object.freeze({
  "-1": "精简",
  "0": "标准",
  "1": "详细",
});

const FLOW_STAGE_CHANGE_LABELS = Object.freeze({
  initial: "首次纳入",
  new: "新进入",
  advanced: "阶段前进",
  returned: "阶段回退",
  corrected: "路径更正",
  unchanged: "与上次一致",
  not_comparable: "暂不可比较",
});

const FLOW_RISK_CHANGE_LABELS = Object.freeze({
  new: "新增",
  upgraded: "升级",
  continued: "持续",
  downgraded: "降级",
  resolved: "关闭",
  closed: "关闭",
  reopened: "重开",
  needs_rejudgment: "需重新判断",
});

const FLOW_PATH_STATE_LABELS = Object.freeze({
  complete: "完整",
  partial: "部分",
  conflicted: "待核实",
});

const FLOW_DATE_STATE_RANK = Object.freeze({ conflicted: 0, missing: 1, partial: 2, exact: 3 });

// 横向流向图固定画布：row_order 决定主链/分支所在行；画布保持紧凑，
// 1280 内容列缩放后仍能保住 13px 阶段名与 16px 人数。
// Wider canvas + shorter nodes: fill 1920 without leftover side whitespace; keep risk badge under the box.
const FLOW_LAYOUT = Object.freeze({ width: 1520, nodeWidth: 168, nodeHeight: 78, rowTop: 4, rowGap: 20, maxColumns: 6 });

function text(value, defaultValue = "") {
  if (value === null || value === undefined || value === "") return defaultValue;
  return String(value);
}

function semanticZoomLabel(value) {
  return SEMANTIC_ZOOM_LABELS[String(value)] || SEMANTIC_ZOOM_LABELS["0"];
}

function analysisBatchLabel(runRef) {
  return text(runRef).includes("prior") ? "上次分析批次" : "本次分析批次";
}

function dataVersionLabel(snapshotRef) {
  const value = text(snapshotRef);
  if (value.includes("comparable")) return "可比更新版本";
  if (value.includes("not-comparable")) return "覆盖范围变化版本";
  if (value.includes("density")) return "高密度验证版本";
  if (value.includes("aemh")) return "AE/MH 补录核查版本";
  if (value.includes("date-edge")) return "日期边界核查版本";
  return "当前数据版本";
}

function visitDateLabel(visit) {
  const actualDate = text(visit?.actual_date || visit?.actualDate);
  if (actualDate) return `实际 ${actualDate}`;
  const nominalDate = text(visit?.nominal_date || visit?.nominalDate);
  if (visit?.date_state === "partial" && nominalDate) return `名义 ${nominalDate} · 日期部分明确`;
  return DATE_STATE_LABELS[visit?.date_state] || "实际日期待确认";
}

function numberText(value, defaultValue = "待确认") {
  return value === null || value === undefined || value === "" ? defaultValue : String(value);
}

function centerLabel(siteRef, defaultLabel = "中心") {
  const raw = text(siteRef);
  const match = /^s7-site-(?:small-)?0*(\d+)$/i.exec(raw);
  if (match) return `中心 ${match[1]}`;
  const s08 = /^site-(.+)$/i.exec(raw);
  if (s08) return `中心 ${s08[1].toUpperCase()}`;
  return raw ? `中心 ${raw}` : defaultLabel;
}

function riskSort(left, right) {
  const rank = { critical: 0, high: 1, medium: 2, low: 3 };
  return (rank[left?.severity] ?? 9) - (rank[right?.severity] ?? 9);
}

function routeCanonical(routeState) {
  return normalizeMedicalMonitoringR5RouteState(routeState?.canonical || routeState || {});
}

function unavailableMessage(error) {
  if (error instanceof MedicalMonitoringR5AdapterError) {
    if (["IDENTITY_PROJECT_MISMATCH", "IDENTITY_TARGET_MISMATCH", "DIGEST_IDENTITY_MISMATCH", "SCHEMA_MISMATCH"].includes(error.code)) {
      return "当前定位无法确认，请返回上一级。";
    }
    if (error.code === "HTTP_READ_FAILED") return "当前来源暂不可读取，请稍后重试。";
  }
  return "当前定位无法确认，请返回上一级。";
}

function flowText(source, keys) {
  const value = source && typeof source === "object" ? source : {};
  for (const key of keys) {
    const item = value[key];
    if (item !== undefined && item !== null && item !== "") return String(item);
  }
  return "";
}

function flowNumber(source, keys) {
  const value = source && typeof source === "object" ? source : {};
  for (const key of keys) {
    const item = value[key];
    if (item === undefined || item === null || item === "") continue;
    const numeric = typeof item === "number" ? item : Number(item);
    if (Number.isFinite(numeric)) return numeric;
  }
  return null;
}

// 受试者阶段流向视图模型：读取 subject_flow 投影（优先适配器归一化结果，
// 兼容原始 snake_case 投影），按合同区分未提供 / 阻断 / 空范围 / 正常四态。
export function normalizeSubjectFlowView(projection) {
  const source = projection?.subjectFlow ?? projection?.subject_flow ?? projection?.raw?.subject_flow ?? null;
  const availability = flowText(source, ["availability"]);
  if (!source || (availability && availability !== "available") || !availability) {
    return { state: "not_provided", notice: flowText(source, ["reason_zh", "reason"]) || "本次数据未提供研究状态", gap: "" };
  }
  const stages = Array.isArray(source.stages) ? source.stages : [];
  const links = Array.isArray(source.links) ? source.links : [];
  const subjects = Array.isArray(source.subjects) ? source.subjects : [];
  const reconciliation = source.reconciliation && typeof source.reconciliation === "object" ? source.reconciliation : {};
  const reconciliationState = flowText(reconciliation, ["state", "reconciliation_state"]);
  if (reconciliationState === "blocked") {
    return {
      state: "blocked",
      notice: "阶段人数暂无法核对，请检查本次数据范围",
      gap: flowText(reconciliation, ["gap_zh", "gap_reason_zh", "reason_zh", "message_zh"]),
    };
  }
  if (stages.length > 0 && subjects.length > 0 && links.length === 0) {
    return { state: "blocked", notice: "阶段人数暂无法核对，请检查本次数据范围", gap: "阶段目录与流向记录不完整。" };
  }
  if (subjects.length === 0) {
    return { state: "empty", notice: "当前项目/中心在本次截止点暂无受试者", gap: "" };
  }
  const stageList = stages.map((stage) => ({
    ref: flowText(stage, ["stage_ref", "stageRef"]),
    label: flowText(stage, ["stage_label_zh", "stageLabelZh", "stage_label", "stageLabel", "label_zh"]),
    column: flowNumber(stage, ["column_order", "columnOrder", "column"]) ?? 0,
    rowOrder: flowNumber(stage, ["row_order", "rowOrder", "row"]) ?? 0,
    kind: flowText(stage, ["stage_kind", "stageKind"]) || "main",
    entry: Boolean(stage?.is_entry ?? stage?.isEntry),
    terminal: Boolean(stage?.is_terminal ?? stage?.isTerminal),
    reached: flowNumber(stage, ["reached_count", "reachedCount"]) ?? 0,
    current: flowNumber(stage, ["current_count", "currentCount"]) ?? 0,
    risk: flowNumber(stage, ["current_mid_high_risk_count", "currentMidHighRiskCount", "mid_high_risk_count", "midHighRiskCount"]) ?? 0,
  })).filter((stage) => stage.ref && stage.label);
  const linkList = links.map((link) => ({
    ref: flowText(link, ["link_ref", "linkRef"]),
    from: flowText(link, ["from_stage_ref", "from_ref", "fromStageRef"]),
    to: flowText(link, ["to_stage_ref", "to_ref", "toStageRef"]),
    count: flowNumber(link, ["count", "subject_count"]) ?? 0,
    risk: flowNumber(link, ["current_mid_high_risk_count", "currentMidHighRiskCount", "mid_high_risk_count", "risk_count", "midHighRiskCount"]) ?? 0,
  })).filter((link) => link.ref && link.from && link.to);
  const stageByRef = new Map(stageList.map((stage) => [stage.ref, stage]));
  const columnOrder = [...new Set(stageList.map((stage) => stage.column))].sort((left, right) => left - right);
  const columnIndex = new Map(columnOrder.map((column, index) => [column, index]));
  const rows = subjects.map((subject) => {
    const pathRefs = (Array.isArray(subject?.pathStageRefs)
      ? subject.pathStageRefs
      : Array.isArray(subject?.path_stage_refs)
      ? subject.path_stage_refs
      : Array.isArray(subject?.path_refs)
        ? subject.path_refs
        : Array.isArray(subject?.stage_refs)
          ? subject.stage_refs
          : []).map(String);
    const currentRef = flowText(subject, ["current_stage_ref", "currentStageRef"]);
    const siteRef = flowText(subject, ["site_ref", "siteRef", "site_id"]);
    const riskSummary = flowText(subject, ["risk_summary_zh", "mid_high_risk_zh", "risk_zh"]);
    const priorRef = pathRefs.length >= 2 ? pathRefs[pathRefs.length - 2] : flowText(subject, ["prior_stage_ref", "priorStageRef"]);
    return {
      subjectRef: flowText(subject, ["subject_ref", "subjectRef", "subject_id"]),
      label: flowText(subject, ["subject_label", "subjectLabel", "label"]) || flowText(subject, ["subject_ref", "subjectRef"]),
      siteRef,
      siteLabel: flowText(subject, ["site_label", "siteLabel", "site_name"]) || centerLabel(siteRef, "中心待确认"),
      spineRef: flowText(subject, ["spine_ref", "spineRef"]),
      currentRef,
      currentLabel: stageByRef.get(currentRef)?.label || flowText(subject, ["current_stage_label", "currentStageLabel"]) || "阶段待确认",
      priorLabel: (priorRef && stageByRef.get(priorRef)?.label) || flowText(subject, ["prior_stage_label", "priorStageLabel"]) || "—",
      pathRefs,
      pathLinkRefs: (Array.isArray(subject?.pathLinkRefs)
        ? subject.pathLinkRefs
        : Array.isArray(subject?.path_link_refs)
          ? subject.path_link_refs
          : []).map(String),
      column: columnIndex.get(stageByRef.get(currentRef)?.column) ?? 99,
      enteredDate: flowText(subject, ["entered_date", "enteredDate", "stage_change_date"]),
      basisDate: flowText(subject, ["basis_date", "basisDate"]),
      dateState: flowText(subject, ["date_state", "dateState"]) || "exact",
      reason: flowText(subject, ["transition_reason_zh", "transition_reason", "key_reason_zh"]) || "—",
      riskSummary,
      midHigh: subject?.currentMidHighRisk === true || subject?.current_mid_high_risk === true
        || subject?.mid_high_risk === true || subject?.is_mid_high_risk === true
        || (flowNumber(subject, ["current_mid_high_risk_count", "currentMidHighRiskCount", "mid_high_risk_count"]) ?? 0) > 0
        || Boolean(riskSummary),
      stageChange: flowText(subject, ["stage_change_kind", "stageChangeKind"]),
      riskChange: flowText(subject, ["risk_change_kind", "riskChangeKind"]),
      pathState: flowText(subject, ["path_state", "pathState"]) || "complete",
      jumpStart: flowText(subject, ["jump_window_start", "jumpWindowStart", "window_start"]),
      jumpEnd: flowText(subject, ["jump_window_end", "jumpWindowEnd", "window_end"]),
    };
  }).filter((row) => row.subjectRef);
  const coverage = source.coverage && typeof source.coverage === "object" ? source.coverage : {};
  const coverageList = [
    { key: "complete", label: "阶段路径齐备", count: flowNumber(coverage, ["complete_count", "complete"]) },
    { key: "partial", label: "路径未齐", count: flowNumber(coverage, ["partial_count", "partial"]) },
    { key: "conflicted", label: "路径待核实", count: flowNumber(coverage, ["conflicted_count", "conflicted"]) },
    { key: "not_provided", label: "数据未提供", count: flowNumber(coverage, ["not_provided_count", "not_provided"]) },
    { key: "not_applicable", label: "不适用", count: flowNumber(coverage, ["not_applicable_count", "not_applicable"]) },
  ].filter((item) => (item.count ?? 0) > 0);
  const riskChanges = { new: 0, upgraded: 0, continued: 0 };
  for (const row of rows) {
    if (!row.midHigh) continue;
    if (row.riskChange === "new") riskChanges.new += 1;
    if (row.riskChange === "upgraded") riskChanges.upgraded += 1;
    if (row.riskChange === "continued") riskChanges.continued += 1;
  }
  return {
    state: "ready",
    stages: stageList,
    links: linkList,
    rows,
    coverageList,
    riskChanges,
    reconciliationState,
    total: rows.length,
    stageByRef,
  };
}

// 主选择互斥：flow_stage_ref + flow_node_metric，或 flow_link_ref（忽略 metric）；
// flow_risk_band 只与主选择求交。
export function subjectFlowSelectionFromRoute(route) {
  const metric = flowText(route, ["flow_node_metric"]) === "reached" ? "reached" : "current";
  return {
    stageRef: flowText(route, ["flow_stage_ref"]),
    metric,
    linkRef: flowText(route, ["flow_link_ref"]),
    riskBand: flowText(route, ["flow_risk_band"]) === "mid_high" ? "mid_high" : "",
  };
}

function subjectFlowHasSelection(selection) {
  return Boolean(selection.stageRef || selection.linkRef || selection.riskBand);
}

function subjectFlowRowMatches(row, selection, linkPair) {
  if (selection.linkRef) {
    if (!linkPair) return false;
    if (row.pathLinkRefs.length > 0) {
      if (!row.pathLinkRefs.includes(selection.linkRef)) return false;
    } else {
      const [fromRef, toRef] = linkPair;
      const path = row.pathRefs;
      if (!path.some((ref, index) => ref === fromRef && path[index + 1] === toRef)) return false;
    }
  } else if (selection.stageRef) {
    if (selection.metric === "reached") {
      if (!row.pathRefs.includes(selection.stageRef)) return false;
    } else if (row.currentRef !== selection.stageRef) return false;
  }
  if (selection.riskBand === "mid_high" && !row.midHigh) return false;
  return true;
}

export function selectSubjectFlowRows(flowView, selection) {
  const linkByRef = new Map(flowView.links.map((link) => [link.ref, [link.from, link.to]]));
  const matched = flowView.rows.filter((row) => subjectFlowRowMatches(row, selection, linkByRef.get(selection.linkRef)));
  return matched.sort((left, right) => (Number(right.midHigh) - Number(left.midHigh))
    || ((FLOW_DATE_STATE_RANK[left.dateState] ?? 9) - (FLOW_DATE_STATE_RANK[right.dateState] ?? 9))
    || (left.column - right.column)
    || left.subjectRef.localeCompare(right.subjectRef, "zh"));
}

function subjectFlowSelectionSummary(flowView, selection) {
  if (selection.linkRef) {
    const link = flowView.links.find((item) => item.ref === selection.linkRef);
    if (!link) return "已筛选：流向记录待确认";
    const fromLabel = flowView.stageByRef.get(link.from)?.label || link.from;
    const toLabel = flowView.stageByRef.get(link.to)?.label || link.to;
    return `已筛选：${fromLabel} → ${toLabel}`;
  }
  if (selection.stageRef) {
    const label = flowView.stageByRef.get(selection.stageRef)?.label || selection.stageRef;
    return `已筛选：${label} · ${selection.metric === "reached" ? "累计到达" : "当前停留"}`;
  }
  if (selection.riskBand === "mid_high") return "已筛选：当前伴随中高风险";
  return "";
}

// 纯函数布局：column_order 决定时间方向，row_order 决定同列分支位置。
// 空目录节点仍展示，但沉入分支行并明确“本截止点无人到达”，避免被读成下一时间阶段。
function layoutSubjectFlowGraph(stages, links) {
  const width = FLOW_LAYOUT.width;
  const nodeWidth = FLOW_LAYOUT.nodeWidth;
  const nodeHeight = FLOW_LAYOUT.nodeHeight;
  const columns = [...new Set(stages.map((stage) => stage.column))].sort((left, right) => left - right);
  const columnX = new Map();
  const lastColumn = Math.max(columns.length - 1, 1);
  // Spread stages across the full canvas; do not cap gap (Round 5 P4 1920 whitespace).
  const columnGap = Math.max(48, Math.floor((width - nodeWidth - 56) / lastColumn));
  const usedWidth = nodeWidth + columnGap * lastColumn;
  const columnStart = Math.max(12, Math.round((width - usedWidth) / 2));
  columns.forEach((column, index) => {
    columnX.set(column, columns.length === 1
      ? Math.round((width - nodeWidth) / 2)
      : columnStart + index * columnGap);
  });
  const nodes = stages.map((stage) => {
    const emptyAtCutoff = stage.reached === 0 && stage.current === 0;
    const rowIndex = Math.max(stage.rowOrder, emptyAtCutoff && stage.kind === "branch_terminal" ? 1 : 0);
    return {
      ...stage,
      x: columnX.get(stage.column) ?? 0,
      y: FLOW_LAYOUT.rowTop + rowIndex * (nodeHeight + FLOW_LAYOUT.rowGap),
      secondRow: rowIndex > 0,
      emptyAtCutoff,
    };
  });
  const nodeByRef = new Map(nodes.map((node) => [node.ref, node]));
  const maxCount = Math.max(1, ...links.map((link) => link.count));
  const ribbons = links.map((link) => {
    const from = nodeByRef.get(link.from);
    const to = nodeByRef.get(link.to);
    if (!from || !to) return null;
    const sameColumn = from.x === to.x;
    if (sameColumn) {
      const x1 = from.x + nodeWidth / 2;
      const x2 = to.x + nodeWidth / 2;
      const y1 = from.y + nodeHeight;
      const y2 = to.y;
      const thickness = Math.max(8, Math.min(26, Math.round((link.count / Math.max(1, ...links.map((item) => item.count))) * 22)));
      const my = Math.round((y1 + y2) / 2);
      const half = thickness / 2;
      return {
        ...link,
        toKind: to.kind,
        ribbonPath: `M ${x1 - half} ${y1} C ${x1 - half} ${my} ${x2 - half} ${my} ${x2 - half} ${y2} L ${x2 + half} ${y2} C ${x2 + half} ${my} ${x1 + half} ${my} ${x1 + half} ${y1} Z`,
        hitPath: `M ${x1} ${y1} C ${x1} ${my} ${x2} ${my} ${x2} ${y2}`,
        labelX: x1 + half + 18,
        labelY: my - 2,
        fromLabel: from.label,
        toLabel: to.label,
      };
    }
    const x1 = from.x + nodeWidth;
    const x2 = to.x;
    const y1 = from.y + nodeHeight / 2;
    const y2 = to.y + nodeHeight / 2;
    const thickness = Math.max(8, Math.min(44, Math.round((link.count / maxCount) * 36)));
    const mx = x1 + Math.max(30, Math.round((x2 - x1) / 2));
    const top1 = y1 - thickness / 2;
    const bottom1 = y1 + thickness / 2;
    const top2 = y2 - thickness / 2;
    const bottom2 = y2 + thickness / 2;
    const labelX = Math.min(width - 16, Math.max(16, Math.round((x1 + x2) / 2)));
    const labelY = Math.round(y1 + (y2 - y1) * 0.5) - Math.round(thickness / 2) - 6;
    return {
      ...link,
      toKind: to.kind,
      ribbonPath: `M ${x1} ${top1} C ${mx} ${top1} ${mx} ${top2} ${x2} ${top2} L ${x2} ${bottom2} C ${mx} ${bottom2} ${mx} ${bottom1} ${x1} ${bottom1} Z`,
      hitPath: `M ${x1} ${y1} C ${mx} ${y1} ${mx} ${y2} ${x2} ${y2}`,
      labelX,
      labelY,
      fromLabel: from.label,
      toLabel: to.label,
    };
  }).filter(Boolean);
  const maxRow = nodes.reduce((acc, node) => Math.max(acc, node.secondRow ? 1 : 0), 0);
  return {
    nodes,
    ribbons,
    width,
    // Height follows used rows only (single-row main path should not reserve a blank second row).
    height: FLOW_LAYOUT.rowTop
      + nodeHeight * (maxRow + 1)
      + (maxRow > 0 ? FLOW_LAYOUT.rowGap : 0)
      + 34,
  };
}

function flowLabelLines(label) {
  const value = String(label || "");
  if (value.length <= 7) return [value, ""];
  if (value.endsWith("数据未提供")) return [value.slice(0, -5), "数据未提供"];
  const split = Math.ceil(value.length / 2);
  return [value.slice(0, split), value.slice(split)];
}

function DomainLegend({ domains }) {
  return (
    <section className="r5-domain-legend" aria-label="八域编码">
      <div className="r5-section-heading">
        <span className="r5-eyebrow">图例</span>
        <h2>事件类别与风险标记</h2>
      </div>
      <div className="r5-domain-grid">
        {domains.map((domain) => (
          <div className="r5-domain-key" key={domain.domain}>
            <DomainIcon domain={domain.domain} encoding={domain} size="legend" title={DOMAIN_LABELS[domain.domain] || domain.shortLabel} />
            <span>
              <strong>{DOMAIN_LABELS[domain.domain] || domain.shortLabel}</strong>
              <small>医学事件</small>
            </span>
          </div>
        ))}
        <div className="r5-risk-key">
          <span className="r5-risk-overlay" aria-hidden="true">AE·高</span>
          <span><strong>风险提示</strong><small>外圈、徽标与文字共同标示风险等级</small></span>
        </div>
      </div>
    </section>
  );
}

function ZoomControls({ zoomLevel, onZoomChange }) {
  const setZoom = (nextZoom) => onZoomChange?.(Math.max(-1, Math.min(1, nextZoom)));
  return (
    <div className="r5-zoom-controls" aria-label="语义缩放控制">
      <span className="r5-zoom-label">语义缩放</span>
      <div className="r5-zoom-buttons" role="group" aria-label="语义缩放级别">
        <button type="button" aria-label="缩小到精简视图" aria-pressed={zoomLevel === -1} onClick={() => setZoom(zoomLevel - 1)}>-</button>
        <button type="button" aria-label="还原标准视图" aria-pressed={zoomLevel === 0} onClick={() => setZoom(0)}>0</button>
        <button type="button" aria-label="放大到详细视图" aria-pressed={zoomLevel === 1} onClick={() => setZoom(zoomLevel + 1)}>+</button>
      </div>
      <small>{semanticZoomLabel(zoomLevel)} · 按 - / 0 / + 调整</small>
    </div>
  );
}

function riskSeverityLabel(severity) {
  if (severity === "high" || severity === "critical") return "高风险";
  if (severity === "medium") return "中风险";
  if (severity === "low") return "低风险";
  return "风险待确认";
}

function eventVisitContext(event, visits = []) {
  if (!event || event.dateState !== "exact") return "访视未定";
  const start = parseTimelineDate(event.start);
  const end = parseTimelineDate(event.end || event.start);
  const datedVisits = visits.map((visit, index) => ({
    date: parseTimelineDate(visitAxisDate(visit)),
    label: text(visit.visit_label || visit.visit_name || visit.visit_code, visit.visit_kind === "unscheduled" ? "非计划访视" : `第 ${visit.visit_number || index + 1} 次访视`),
  })).filter((visit) => visit.date != null).sort((left, right) => left.date - right.date);
  if (start == null || end == null || !datedVisits.length) return "未绑定访视";
  if (end > start) {
    const included = datedVisits.filter((visit) => visit.date >= start && visit.date <= end);
    if (included.length > 1) return `跨访视（${included[0].label}至${included.at(-1).label}）`;
    return included.length === 1 ? `跨访视期间（含${included[0].label}）` : "跨访视期间";
  }
  const exact = datedVisits.find((visit) => visit.date === start);
  if (exact) return exact.label;
  const nextIndex = datedVisits.findIndex((visit) => visit.date > start);
  if (nextIndex > 0) return `${datedVisits[nextIndex - 1].label}与${datedVisits[nextIndex].label}之间`;
  if (nextIndex === 0) return `${datedVisits[0].label}前`;
  return `${datedVisits.at(-1).label}后`;
}

function timelineMonthTicks(scale) {
  const stepMonths = scale.spanMs > 240 * 24 * 60 * 60 * 1000 ? 3 : 1;
  const cursor = new Date(scale.startMs);
  cursor.setUTCDate(1);
  cursor.setUTCMonth(cursor.getUTCMonth() + 1);
  const ticks = [];
  while (cursor.getTime() < scale.endMs) {
    const iso = cursor.toISOString().slice(0, 10);
    ticks.push({ iso, x: scale.xFor(iso), label: `${cursor.getUTCMonth() + 1}月` });
    cursor.setUTCMonth(cursor.getUTCMonth() + stepMonths);
  }
  return ticks;
}

function focusAdjacentTimelineEvent(keyboardEvent) {
  if (keyboardEvent.key !== "ArrowLeft" && keyboardEvent.key !== "ArrowRight") return;
  const lane = keyboardEvent.currentTarget.closest?.("[data-lane-canvas]");
  const events = Array.from(lane?.querySelectorAll?.("button.r5-track-event") || []);
  const current = events.indexOf(keyboardEvent.currentTarget);
  if (current < 0 || events.length < 2) return;
  const next = keyboardEvent.key === "ArrowRight"
    ? Math.min(events.length - 1, current + 1)
    : Math.max(0, current - 1);
  if (next === current) return;
  keyboardEvent.preventDefault();
  events[next]?.focus?.();
}

export function DomainTracks({
  projection,
  zoomLevel,
  selectedEventRef,
  selectedRiskAnchorRef,
  onEventSelect,
  journeyEnabled = false,
  journeyMarkerByEventRef = null,
  journeyTruncationText = "",
}) {
  const layout = useMemo(() => layoutJourneyTimeline({
    domains: projection.domains || [],
    events: projection.events || [],
    visits: projection.temporalSpine?.visits || [],
    risks: projection.currentRisks || [],
    pendingDates: projection.temporalSpine?.pendingDates || [],
    windowStart: projection.temporalSpine?.windowStart,
    windowEnd: projection.temporalSpine?.windowEnd,
    zoomLevel,
  }), [projection, zoomLevel]);
  const journeyMarkerFor = (eventRef) => (journeyEnabled && journeyMarkerByEventRef ? journeyMarkerByEventRef[eventRef] || null : null);
  const riskCounts = (projection.currentRisks || []).reduce((counts, risk) => ({ ...counts, [risk.severity]: (counts[risk.severity] || 0) + 1 }), {});
  const axisMode = text(projection.temporalSpine?.axisMode, "calendar") === "study_day" ? "研究日" : "日历日期";
  const selectedRef = selectedEventRef || "";
  const monthTicks = timelineMonthTicks(layout.scale);
  let lastVisitLabelX = -Infinity;
  const labeledVisits = layout.visitMarks.map((mark, index) => {
    const minGap = zoomLevel === 1 ? 84 : zoomLevel === 0 ? 104 : 124;
    const showLabel = index === 0 || mark.x - lastVisitLabelX >= minGap;
    if (showLabel) lastVisitLabelX = mark.x;
    return { ...mark, showLabel, labelSide: index % 2 ? "below" : "above" };
  });
  return (
    <section className="r5-domain-tracks" aria-label="共享横向时间轴与八域泳道" data-timeline-mode="shared-horizontal">
      <div className="r5-axis-heading">
        <div>
          <span className="r5-eyebrow">共享时间轴</span>
          <h2 id={journeyEnabled ? R7_JOURNEY_AXIS_TITLE_ID : undefined} tabIndex={journeyEnabled ? -1 : undefined}>{axisMode}</h2>
        </div>
        <span className="r5-axis-window">{text(projection.temporalSpine?.windowStart, layout.scale.windowStartIso)} — {text(projection.temporalSpine?.windowEnd, layout.scale.windowEndIso)}</span>
      </div>
      {journeyTruncationText ? <p className="r7-journey-truncation" role="status" data-journey-truncation>{journeyTruncationText}</p> : null}
      <div className="r5-density-summary" aria-label="高密度医学旅程摘要">
        <strong>{(projection.events || []).length} 条事件 · {(projection.temporalSpine?.visits || []).length} 次访视 · {(projection.currentRisks || []).length} 个风险锚点</strong>
        <span>
          高风险 {riskCounts.high || 0} · 中风险 {riskCounts.medium || 0}；中高风险逐项显示，低风险与常规记录
          <span className="r5-phrase-keep">按缩放级别聚合</span>
          。
        </span>
      </div>
      <div className="r5-lane-index" aria-label="八类医学事件泳道概览">
        {layout.lanes.map((lane) => (
          <span key={lane.domain}>
            <DomainIcon domain={lane.domain} size="summary" />
            <strong>{laneChipLabel(DOMAIN_LABELS[lane.domain] || lane.encoding.shortLabel)}</strong>
            <small>{lane.eventCount} 条</small>
          </span>
        ))}
      </div>
      <TimelineScrollShell>
        <div
          className="r5-timeline-canvas"
          style={{ "--timeline-plot-width": `${layout.scale.width}px`, width: `calc(${layout.scale.width}px + var(--timeline-label-width))` }}
          data-timeline-width={layout.scale.width}
        >
          <div className="r5-time-grid" aria-hidden="true">
            {monthTicks.map((tick) => <span key={tick.iso} style={{ left: `calc(var(--timeline-label-width) + ${tick.x}px)` }}><small>{tick.label}</small></span>)}
          </div>
          <div className="r5-axis-track" aria-label="访视节点">
            <div className="r5-axis-label"><strong>访视</strong><small>按实际日期定位</small></div>
            <div className="r5-axis-baseline" aria-hidden="true" />
            {labeledVisits.map((mark, index) => {
              const visit = mark.visit;
              return (
                <div
                  className={`r5-visit-node r5-visit-label-${mark.labelSide}${mark.showLabel ? " is-labeled" : ""}`}
                  data-visit-ref={mark.visitRef}
                  key={mark.visitRef || `${mark.iso}-${index}`}
                  style={{ left: `calc(var(--timeline-label-width) + ${mark.x}px)` }}
                  title={visitDateLabel(visit)}
                >
                  <span className="r5-visit-dot" aria-hidden="true" />
                  {mark.showLabel ? <><strong>{text(visit.visit_label || visit.visit_name || visit.visit_code, visit.visit_kind === "unscheduled" ? "非计划访视" : `第 ${visit.visit_number || index + 1} 次访视`)}</strong><small>{visitDateLabel(visit)}</small></> : null}
                </div>
              );
            })}
          </div>
          <div className="r5-domain-track-grid" role="list" aria-label="八域事件泳道">
            {layout.lanes.map((lane) => {
              const displayStackRows = lane.stackRows + (lane.aggregates.length ? 1 : 0);
              const eventRowOffset = lane.aggregates.length ? 1 : 0;
              return (
              <article
                className="r5-domain-track"
                data-domain-track={lane.domain}
                data-stack-rows={displayStackRows}
                aria-label={`${DOMAIN_LABELS[lane.domain] || lane.encoding.shortLabel}事件泳道`}
                key={lane.domain}
                role="listitem"
                style={{ "--lane-stack-rows": displayStackRows }}
              >
                <div className="r5-domain-track-head">
                  <DomainIcon domain={lane.domain} encoding={lane.encoding} size="lane" title={DOMAIN_LABELS[lane.domain] || lane.encoding.shortLabel} />
                  <div>
                    <strong>{DOMAIN_LABELS[lane.domain] || lane.encoding.shortLabel}</strong>
                    <small>{lane.eventCount ? `${lane.eventCount} 条` : "当前无事件"}{lane.riskAnchorCount ? ` · ${lane.riskAnchorCount} 个风险` : ""}</small>
                  </div>
                </div>
                <div className="r5-domain-track-events" data-lane-canvas="true">
                  {lane.marks.length === 0 && lane.aggregates.length === 0 ? <span className="r5-domain-track-empty">当前范围无该域记录</span> : null}
                  {lane.marks.map((mark) => {
                    const event = mark.event;
                    const selected = event.eventRef === selectedRef || (selectedRiskAnchorRef && event.riskAnchorRefs?.includes(selectedRiskAnchorRef));
                    const marker = journeyMarkerFor(event.eventRef);
                    const riskLabel = event.risk
                      ? `${DOMAIN_LABELS[event.domain] || event.domainEncoding.shortLabel}·${riskSeverityLabel(event.risk.severity)}`
                      : "";
                    const commonProps = {
                      type: "button",
                      className: `r5-track-event r5-track-event-${mark.geometry}${mark.x > layout.scale.width - 170 ? " is-near-end" : ""}${selected ? " is-selected" : ""}${event.risk ? ` has-risk r5-track-risk-${event.risk.severity}` : ""}`,
                      "data-event-ref": event.eventRef,
                      "data-timeline-geometry": mark.geometry,
                      "data-stack-row": mark.stackRow,
                      "aria-label": `${DOMAIN_LABELS[event.domain] || event.domainEncoding.shortLabel}：${event.eventLabel}${event.risk ? `，${riskSeverityLabel(event.risk.severity)}` : ""}${marker ? `，本轮变化：${marker.changeText}${marker.countSuffix}` : ""}`,
                      onClick: () => onEventSelect?.(event),
                      onKeyDown: focusAdjacentTimelineEvent,
                      title: `${event.eventLabel} · ${event.dateState === "exact" ? text(event.start, "实际日期待确认") : event.dateLabel}${event.end && event.end !== event.start ? ` — ${event.end}` : ""}`,
                    };
                    if (mark.geometry === "interval") {
                      return (
                        <button
                          key={event.eventRef}
                          {...commonProps}
                          style={{ left: `${mark.x}px`, width: `${mark.width}px`, top: `${8 + (mark.stackRow + eventRowOffset) * 22}px` }}
                        >
                          <DomainIcon domain={event.domain} encoding={event.domainEncoding} size="track" title={DOMAIN_LABELS[event.domain] || event.domainEncoding.shortLabel} />
                          {event.risk ? <span className={`r5-compact-risk-label r5-track-risk-${event.risk.severity}`}>{riskSeverityLabel(event.risk.severity).slice(0, 1)}</span> : null}
                          <span className="r5-track-event-title">{event.risk && <span className={`r5-track-risk r5-track-risk-${event.risk.severity}`}>{riskLabel}</span>}{event.eventLabel}</span>
                          {marker ? <R7JourneyChangeMarker marker={marker} /> : null}
                          <small className="r5-track-event-detail">{text(event.start)} — {text(event.end)}</small>
                          <small className="r5-track-event-source">来源定位：{event.sourceLocatorRefs.length ? `已定位到 ${event.sourceLocatorRefs.length} 条原始记录` : "待确认"}</small>
                        </button>
                      );
                    }
                    return (
                      <button
                        key={event.eventRef}
                        {...commonProps}
                        style={{ left: `${mark.x}px`, top: `${8 + (mark.stackRow + eventRowOffset) * 22}px` }}
                      >
                        <DomainIcon domain={event.domain} encoding={event.domainEncoding} size="track" title={DOMAIN_LABELS[event.domain] || event.domainEncoding.shortLabel} />
                        {event.risk ? <span className={`r5-compact-risk-label r5-track-risk-${event.risk.severity}`}>{riskSeverityLabel(event.risk.severity).slice(0, 1)}</span> : null}
                        <span className="r5-track-event-title">{event.risk && <span className={`r5-track-risk r5-track-risk-${event.risk.severity}`}>{riskLabel}</span>}{zoomLevel === 1 ? event.eventLabel : ""}</span>
                        {marker ? <R7JourneyChangeMarker marker={marker} /> : null}
                        <small className="r5-track-event-detail">{event.dateState === "exact" ? text(event.start, "实际日期待确认") : event.dateLabel}</small>
                        <small className="r5-track-event-source">来源定位：{event.sourceLocatorRefs.length ? `已定位到 ${event.sourceLocatorRefs.length} 条原始记录` : "待确认"}</small>
                      </button>
                    );
                  })}
                  {lane.aggregates.map((aggregate) => (
                    <span
                      className="r5-domain-track-aggregate r5-timeline-aggregate"
                      data-aggregate-key={aggregate.aggregateKey}
                      key={aggregate.aggregateKey}
                      style={{ left: `${aggregate.x}px` }}
                      title={`${aggregate.label}已聚合，使用右上角“+”查看全部。`}
                    >
                      {`另有 ${aggregate.count} 条`}
                    </span>
                  ))}
                </div>
              </article>
              );
            })}
          </div>
        </div>
      </TimelineScrollShell>
      <div className="r5-pending-date-zone" aria-label="日期待确认记录">
        <div className="r5-section-heading">
          <span className="r5-eyebrow">暂不定位到时间轴</span>
          <h2>日期待确认记录</h2>
        </div>
        {!layout.pendingEvents.length && !layout.pendingVisits.length && !(layout.pendingDates || []).length ? (
          <p className="r5-domain-track-empty">当前范围无日期缺失记录。</p>
        ) : null}
        {layout.pendingEvents.map((event) => {
          const marker = journeyMarkerFor(event.eventRef);
          return (
          <button
            type="button"
            className={`r5-pending-date${event.eventRef === selectedRef ? " is-selected" : ""}`}
            data-event-ref={event.eventRef}
            data-timeline-geometry="pending"
            key={event.eventRef}
            onClick={() => onEventSelect?.(event)}
          >
            <DomainIcon domain={event.domain} size="summary" />
            <span>{DATE_STATE_LABELS[event.dateState] || "日期待确认"}</span>
            <strong>{DOMAIN_LABELS[event.domain] || event.domainEncoding?.shortLabel || "其他事件"} · {event.eventLabel}</strong>
            <small>不确定访视归属；未按实际日期吸附到共享时间轴，单独列示</small>
            {event.risk ? <span className={`r5-track-risk r5-track-risk-${event.risk.severity}`}>{riskSeverityLabel(event.risk.severity)}</span> : null}
            {marker ? <R7JourneyChangeMarker marker={marker} /> : null}
            {marker ? <span className="r7-journey-sr-only">，本轮变化：{marker.changeText}{marker.countSuffix}</span> : null}
          </button>
          );
        })}
        {layout.pendingVisits.map((visit) => (
          <div className="r5-pending-date" data-visit-ref={visit.visit_ref || visit.visitRef} key={visit.visit_ref || visit.visitRef}>
            <span>{DATE_STATE_LABELS[visit.date_state] || "日期待确认"}</span>
            <strong>{text(visit.visit_label || visit.visit_name || visit.visit_code, visit.visit_kind === "unscheduled" ? "非计划访视" : "访视")} · 实际日期待确认</strong>
            <small>访视缺少实际日期，不进入共享横向时间轴定位</small>
          </div>
        ))}
        {(layout.pendingDates || []).filter((item) => {
          const ref = typeof item === "string" ? item : item?.item_ref;
          return ref && !layout.pendingEvents.some((event) => event.eventRef === ref);
        }).map((item) => {
          const ref = typeof item === "string" ? item : item.item_ref;
          const domain = typeof item === "string" ? null : item.domain;
          const dateState = typeof item === "string" ? "missing" : item.date_state;
          return (
            <div className="r5-pending-date" key={ref}>
              {domain ? <DomainIcon domain={domain} size="summary" /> : null}
              <span>{DATE_STATE_LABELS[dateState] || "日期待确认"}</span>
              <strong>{DOMAIN_LABELS[domain] || "其他事件"} · 相关记录</strong>
              <small>不确定访视归属；访视间事件未吸附到名义访视，单独列示</small>
            </div>
          );
        })}
      </div>
    </section>
  );
}

function IdentityStrip({ identity = {}, project = {} }) {
  const projectRef = text(identity.project_ref || identity.projectRef);
  const projectCode = text(project.project_code);
  const rawProjectLabel = text(project.project_label || project.project_name || projectCode || projectRef);
  const projectLabel = rawProjectLabel.startsWith("s7-") ? "S7 医学监查合成项目" : text(rawProjectLabel, "项目待确认");
  const projectDisplay = projectCode && projectCode !== projectLabel ? `${projectLabel} · ${projectCode}` : projectLabel;
  return (
    <div className="r5-identity-strip" aria-label="当前数据范围">
      <div data-r5-identity-field="project_ref"><span>项目</span><strong>{projectDisplay}</strong><small>当前医学监查范围</small></div>
      <div data-r5-identity-field="run_ref"><span>分析批次</span><strong>{analysisBatchLabel(identity.run_ref || identity.runRef)}</strong></div>
      <div data-r5-identity-field="snapshot_ref"><span>数据版本</span><strong>{dataVersionLabel(identity.snapshot_ref || identity.snapshotRef)}</strong></div>
      <div data-r5-identity-field="cutoff_ref"><span>数据截止</span><strong>{(identity.cutoff_state || identity.cutoffState) === "absent" ? "截止时间待确认" : text(identity.cutoff_ref || identity.cutoffRef, "截止时间待确认")}</strong></div>
    </div>
  );
}

function RiskBadge({ risk }) {
  const encoding = risk?.domainEncoding;
  return (
    <span className="r5-risk-badge" data-severity={risk?.severity || "unknown"}>
      {encoding ? (
        <DomainIcon domain={encoding.domain} encoding={encoding} size="badge" title={DOMAIN_LABELS[encoding.domain] || encoding.shortLabel} />
      ) : <span className="r5-risk-unresolved">域待确认</span>}
      <span className="r5-risk-overlay">{text(DOMAIN_LABELS[encoding?.domain] || encoding?.shortLabel, "域待确认")}·{text(risk?.severityLabel, "等级待确认")}风险</span>
    </span>
  );
}

export const RiskRow = memo(function RiskRow({ risk, onSelect, marker = null, omitChangeClaims = false }) {
  const metaParts = [
    text(risk.subjectLabel, "受试者"),
    text(risk.siteLabel, "中心"),
    risk.dateLabel,
  ].filter((part) => Boolean(part) && String(part).trim());
  return (
    <button
      type="button"
      role="option"
      aria-selected="false"
      className={`r5-risk-row ${risk.riskStatus === "unresolved" ? "is-unresolved" : ""}`}
      data-risk-instance-ref={risk.riskInstanceRef}
      disabled={risk.riskStatus === "unresolved"}
      onClick={() => risk.riskStatus !== "unresolved" && onSelect?.(risk)}
    >
      <RiskBadge risk={risk} />
      <span className="r5-risk-copy">
        <strong>{risk.riskType}</strong>
        <small>
          {metaParts.join(" · ")}
          {!omitChangeClaims && risk.changeCauseLabel ? ` · 变化原因：${risk.changeCauseLabel}` : ""}
        </small>
      </span>
      {marker ? (
        <span className="r5-risk-tail">
          <R7JourneyChangeMarker marker={marker} />
          <span className="r7-journey-sr-only">，本轮变化：{marker.changeText}{marker.countSuffix}</span>
        </span>
      ) : omitChangeClaims ? null : <span className="r5-change-label">{risk.changeLabel}</span>}
    </button>
  );
});

function RiskList({ risks, onSelect, selectedRiskInstanceRef = "", emptyText = "当前没有可展示的风险定位。", markersByRiskInstance = null, omitChangeClaims = false }) {
  const listRef = useRef(null);
  const rows = useMemo(() => risks.map((risk) => (
    <RiskRow
      key={risk.riskInstanceRef || risk.riskRef || risk.eventRef}
      risk={risk}
      onSelect={onSelect}
      marker={markersByRiskInstance?.[risk.riskInstanceRef] || null}
      omitChangeClaims={omitChangeClaims}
    />
  )), [markersByRiskInstance, omitChangeClaims, onSelect, risks]);
  useLayoutEffect(() => {
    for (const row of listRef.current?.querySelectorAll("button.r5-risk-row") || []) {
      const selected = row.dataset.riskInstanceRef === selectedRiskInstanceRef;
      row.classList.toggle("is-selected", selected);
      row.setAttribute("aria-selected", String(selected));
    }
  }, [selectedRiskInstanceRef, rows]);
  if (!risks.length) return <div className="r5-empty-inline">{emptyText}</div>;
  return <div className="r5-risk-list" role="listbox" aria-label="当前风险" ref={listRef}>{rows}</div>;
}

function CenterTable({ centers, onSelect }) {
  if (!centers.length) return <div className="r5-empty-inline">中心覆盖范围待确认。</div>;
  return (
    <div className="r5-center-table" role="table" aria-label="中心覆盖与风险模式">
      <div className="r5-center-row r5-center-head" role="row">
        <span>中心</span><span>风险数 / 记录数</span><span>数据完整性</span><span>统计单位</span>
      </div>
      {centers.map((center, index) => {
        const measure = center.measures[0] || {};
        return (
          <button type="button" className="r5-center-row" role="row" key={center.siteRef} onClick={() => onSelect?.(center)}>
            <strong>{center.siteLabel || `中心 ${index + 1}`}</strong>
            <span className="r5-center-pattern">{measure.denominator ? `${numberText(measure.numerator)} / ${numberText(measure.denominator)}` : "暂无法计算"}</span>
            <span>{center.coverageLabel}</span>
            <span>{text(measure.unit, "受试者")}</span>
          </button>
        );
      })}
    </div>
  );
}

// Painted scroll affordances: OS overlay scrollbars are invisible in default ego stills.
// Keep native overflow for interaction; paint ONE synced rail (native bar hidden when custom shows).
// Horizontal: clip mid-glyph header at the overflow edge so the last painted header is a whole word.
function useScrollMetrics(axis = "x") {
  const ref = useRef(null);
  const [overflow, setOverflow] = useState(false);
  const [thumb, setThumb] = useState({ start: 0, size: 40 });
  const sync = useCallback(() => {
    const el = ref.current;
    if (!el) return;
    if (axis === "x") {
      const max = el.scrollWidth - el.clientWidth;
      const has = max > 2;
      setOverflow(has);
      if (!has) {
        el.style.removeProperty("--r5-edge-clip");
        return;
      }
      const size = Math.max(12, (el.clientWidth / el.scrollWidth) * 100);
      const start = max <= 0 ? 0 : (el.scrollLeft / max) * (100 - size);
      setThumb({ start, size });
      // Snap painted edge between columns: hide any mid-glyph peek at the right.
      const wrapRight = el.getBoundingClientRect().right;
      let edgeClip = 0;
      const headers = el.querySelectorAll("thead th");
      for (let i = 0; i < headers.length; i += 1) {
        const r = headers[i].getBoundingClientRect();
        if (r.left < wrapRight - 0.5 && r.right > wrapRight + 0.5) {
          edgeClip = Math.max(0, Math.ceil(wrapRight - r.left));
          break;
        }
      }
      el.style.setProperty("--r5-edge-clip", `${edgeClip}px`);
      return;
    }
    const max = el.scrollHeight - el.clientHeight;
    const has = max > 2;
    setOverflow(has);
    if (!has) return;
    const size = Math.max(12, (el.clientHeight / el.scrollHeight) * 100);
    const start = max <= 0 ? 0 : (el.scrollTop / max) * (100 - size);
    setThumb({ start, size });
  }, [axis]);
  useLayoutEffect(() => {
    sync();
    const el = ref.current;
    if (!el) return undefined;
    const ro = typeof ResizeObserver === "function" ? new ResizeObserver(sync) : null;
    ro?.observe(el);
    el.addEventListener("scroll", sync, { passive: true });
    window.addEventListener("resize", sync);
    return () => {
      ro?.disconnect();
      el.removeEventListener("scroll", sync);
      window.removeEventListener("resize", sync);
    };
  }, [sync]);
  const scrollToRatio = useCallback((ratio) => {
    const el = ref.current;
    if (!el) return;
    const clamped = Math.min(1, Math.max(0, ratio));
    if (axis === "x") {
      const max = el.scrollWidth - el.clientWidth;
      el.scrollLeft = clamped * Math.max(0, max);
      return;
    }
    const max = el.scrollHeight - el.clientHeight;
    el.scrollTop = clamped * Math.max(0, max);
  }, [axis]);
  return { ref, overflow, thumb, sync, scrollToRatio };
}

function FlowTableScroll({ children }) {
  const { ref, overflow, thumb, scrollToRatio } = useScrollMetrics("x");
  const wrapId = "r5-flow-table-scroll-pane";
  const seekFromEvent = (event) => {
    const track = event.currentTarget;
    const rect = track.getBoundingClientRect();
    if (rect.width <= 0) return;
    scrollToRatio((event.clientX - rect.left) / rect.width);
  };
  return (
    <div className={`r5-flow-table-scroll${overflow ? " is-overflow" : ""}`} data-r5-table-scroll={overflow ? "overflow" : "fit"}>
      {overflow ? (
        <p className="r5-flow-table-scroll-cue" data-r5-table-scroll-cue="true" id="r5-flow-table-scroll-cue">
          左右滑动查看完整明细（含数据完整性、医学旅程）
        </p>
      ) : null}
      <div className="r5-flow-table-wrap" id={wrapId} ref={ref}>{children}</div>
      {overflow ? (
        <div
          className="r5-flow-table-hrail"
          data-r5-table-hrail="true"
          role="scrollbar"
          aria-orientation="horizontal"
          aria-controls={wrapId}
          aria-valuemin={0}
          aria-valuemax={100}
          aria-valuenow={Math.round(thumb.start + thumb.size / 2)}
          aria-label="左右滑动查看完整明细"
          aria-describedby="r5-flow-table-scroll-cue"
          tabIndex={0}
          onPointerDown={(event) => {
            event.currentTarget.setPointerCapture?.(event.pointerId);
            seekFromEvent(event);
          }}
          onPointerMove={(event) => {
            if (event.buttons === 1) seekFromEvent(event);
          }}
          onKeyDown={(event) => {
            const el = ref.current;
            if (!el) return;
            if (event.key === "ArrowRight") { event.preventDefault(); el.scrollLeft += 96; }
            if (event.key === "ArrowLeft") { event.preventDefault(); el.scrollLeft -= 96; }
            if (event.key === "Home") { event.preventDefault(); scrollToRatio(0); }
            if (event.key === "End") { event.preventDefault(); scrollToRatio(1); }
          }}
        >
          <div className="r5-flow-table-hrail-track">
            <div className="r5-flow-table-hrail-thumb" style={{ width: `${thumb.size}%`, left: `${thumb.start}%` }} />
          </div>
        </div>
      ) : null}
    </div>
  );
}

function TimelineScrollShell({ children }) {
  const { ref, overflow, thumb, scrollToRatio } = useScrollMetrics("y");
  const paneId = "r5-timeline-scroll-pane";
  const seekFromEvent = (event) => {
    const track = event.currentTarget;
    const rect = track.getBoundingClientRect();
    if (rect.height <= 0) return;
    scrollToRatio((event.clientY - rect.top) / rect.height);
  };
  return (
    <div className={`r5-timeline-scroll-shell${overflow ? " is-overflow-y" : ""}`} data-r5-timeline-scroll={overflow ? "overflow" : "fit"}>
      <div className="r5-timeline-scroll" id={paneId} ref={ref}>{children}</div>
      {overflow ? (
        <div
          className="r5-timeline-vrail"
          data-r5-timeline-vrail="true"
          role="scrollbar"
          aria-orientation="vertical"
          aria-controls={paneId}
          aria-valuemin={0}
          aria-valuemax={100}
          aria-valuenow={Math.round(thumb.start + thumb.size / 2)}
          aria-label="上下滑动查看完整时间轴泳道"
          tabIndex={0}
          onPointerDown={(event) => {
            event.currentTarget.setPointerCapture?.(event.pointerId);
            seekFromEvent(event);
          }}
          onPointerMove={(event) => {
            if (event.buttons === 1) seekFromEvent(event);
          }}
          onKeyDown={(event) => {
            const el = ref.current;
            if (!el) return;
            if (event.key === "ArrowDown") { event.preventDefault(); el.scrollTop += 72; }
            if (event.key === "ArrowUp") { event.preventDefault(); el.scrollTop -= 72; }
            if (event.key === "Home") { event.preventDefault(); scrollToRatio(0); }
            if (event.key === "End") { event.preventDefault(); scrollToRatio(1); }
          }}
        >
          <div className="r5-timeline-vrail-track">
            <div className="r5-timeline-vrail-thumb" style={{ height: `${thumb.size}%`, top: `${thumb.start}%` }} />
          </div>
        </div>
      ) : null}
    </div>
  );
}

// 受试者阶段流向：全宽横向 SVG、current/reached/link 筛选、风险摘要、折叠明细表
// 与三种非正常展示。焦点位于本节内时，文档级快捷键已由页面统一隔离。
export function SubjectFlowSection({
  flow,
  selection,
  onStageSelect,
  onLinkSelect,
  onMetricSelect,
  onRiskToggle,
  onClear,
  onSubjectJump,
  initialTableOpen = false,
  hideIncremental = false,
}) {
  const [tableOpen, setTableOpen] = useState(initialTableOpen);
  const focusItems = useRef([]);
  const registerFlowFocus = (orderIndex) => (element) => {
    if (element) focusItems.current[orderIndex] = element;
  };
  const handleFlowKeyDown = (event) => {
    if (event.key === "Escape") {
      if (subjectFlowHasSelection(selection)) {
        event.preventDefault();
        onClear?.();
      }
      return;
    }
    if (!(event.target instanceof SVGElement)) return;
    const items = focusItems.current.filter(Boolean);
    if (!items.length) return;
    const current = items.indexOf(event.target);
    let next = -1;
    if (event.key === "ArrowRight" || event.key === "ArrowDown") next = current < 0 ? 0 : Math.min(items.length - 1, current + 1);
    if (event.key === "ArrowLeft" || event.key === "ArrowUp") next = current < 0 ? items.length - 1 : Math.max(0, current - 1);
    if (next >= 0) {
      event.preventDefault();
      items[next]?.focus?.();
    }
  };
  const graph = flow.state === "ready" ? layoutSubjectFlowGraph(flow.stages, flow.links) : null;
  const nodeSelectionActive = Boolean(selection.stageRef || selection.linkRef);
  const filteredRows = flow.state === "ready" ? selectSubjectFlowRows(flow, selection) : [];
  const summaryLine = subjectFlowSelectionSummary(flow, selection);
  return (
    <section
      className="r5-panel r5-flow-section"
      data-r5-flow-state={flow.state}
      data-r5-flow-scope="true"
      aria-label="受试者阶段流向"
      onKeyDown={handleFlowKeyDown}
    >
      <div className="r5-section-heading"><span className="r5-eyebrow">受试者阶段流向</span><h2>阶段流向总览</h2></div>
      <p className="r5-flow-note">连线表示截至本次截止点的规范阶段路径；节点同时显示累计到达人数和当前停留人数。退回或重新筛选情况见阶段较上次。</p>
      {flow.state === "not_provided" && (
        <div className="r5-flow-notice" role="status">
          <strong>本次数据未提供研究状态</strong>
          {flow.notice && flow.notice !== "本次数据未提供研究状态" ? <span>{flow.notice}</span> : null}
        </div>
      )}
      {flow.state === "blocked" && (
        <div className="r5-flow-notice is-blocked" role="alert">
          <strong>阶段人数暂无法核对，请检查本次数据范围</strong>
          {flow.gap ? <span>{flow.gap}</span> : null}
        </div>
      )}
      {flow.state === "empty" && (
        <div className="r5-flow-notice" role="status">
          <strong>当前项目/中心在本次截止点暂无受试者</strong>
        </div>
      )}
      {flow.state === "ready" && graph && (
        <>
          <div className="r5-flow-controls">
            <label>
              阶段
              <select aria-label="按阶段筛选受试者" value={selection.stageRef} onChange={(event) => onStageSelect?.(event.target.value, selection.metric)}>
                <option value="">全部阶段</option>
                {graph.nodes.map((node) => <option key={node.ref} value={node.ref}>{node.label}</option>)}
              </select>
            </label>
            <label>
              查看
              <select aria-label="阶段人数查看方式" value={selection.metric} disabled={Boolean(selection.linkRef)} onChange={(event) => onMetricSelect?.(event.target.value)}>
                <option value="current">当前停留</option>
                <option value="reached">累计到达</option>
              </select>
            </label>
            <button type="button" aria-pressed={selection.riskBand === "mid_high"} onClick={() => onRiskToggle?.()}>仅看中高风险</button>
            {subjectFlowHasSelection(selection) && <button type="button" className="r5-flow-clear" onClick={() => onClear?.()}>清除筛选</button>}
            {summaryLine && <span className="r5-flow-filter-hint">{summaryLine}</span>}
          </div>
          <svg
            className="r5-flow-svg"
            viewBox={`0 0 ${graph.width} ${graph.height}`}
            role="group"
            aria-label="受试者阶段流向图"
          >
            {graph.ribbons.map((ribbon, index) => (
              <g
                key={ribbon.ref}
                role="button"
                tabIndex={0}
                data-flow-link={ribbon.ref}
                className={`${selection.linkRef === ribbon.ref ? "is-selected" : ""}${nodeSelectionActive && selection.linkRef !== ribbon.ref ? " is-dim" : ""}`}
                aria-label={`从${ribbon.fromLabel}到${ribbon.toLabel}，${ribbon.count} 人，该流向受试者中当前伴随中高风险 ${ribbon.risk} 人`}
                ref={registerFlowFocus(flow.stages.length + index)}
                onClick={() => onLinkSelect?.(ribbon.ref)}
                onKeyDown={(event) => {
                  if (event.key === "Enter" || event.key === " ") {
                    event.preventDefault();
                    onLinkSelect?.(ribbon.ref);
                  }
                }}
              >
                <title>{`从${ribbon.fromLabel}到${ribbon.toLabel}：${ribbon.count} 人，该流向受试者中当前伴随中高风险 ${ribbon.risk} 人`}</title>
                <path d={ribbon.ribbonPath} className="r5-flow-ribbon" />
                <path d={ribbon.hitPath} className="r5-flow-link-hit" />
                <text x={ribbon.labelX} y={ribbon.labelY} className="r5-flow-link-count">{ribbon.count}</text>
                {/* Mid/high risk stays on nodes only. Ribbon “中高 N” sits on the stroke and
                    fails first-screen scan (conference R3 P2). Title/aria still carry the count. */}
              </g>
            ))}
            {graph.nodes.map((node, index) => {
              const [line1, line2] = flowLabelLines(node.label);
              const centerX = node.x + FLOW_LAYOUT.nodeWidth / 2;
              const nodeSelected = selection.stageRef === node.ref;
              return (
                <g
                  key={node.ref}
                  role="button"
                  tabIndex={0}
                  data-flow-node={node.ref}
                  data-stage-kind={node.kind}
                  data-flow-empty={node.emptyAtCutoff ? "true" : "false"}
                  className={`${nodeSelected ? "is-selected" : ""}${nodeSelectionActive && !nodeSelected ? " is-dim" : ""}`}
                  aria-label={`${node.label}，到达 ${node.reached} 人，当前 ${node.current} 人，其中中高风险 ${node.risk} 人`}
                  ref={registerFlowFocus(index)}
                  onClick={() => onStageSelect?.(node.ref, "current")}
                  onKeyDown={(event) => {
                    if (event.key === "Enter" || event.key === " ") {
                      event.preventDefault();
                      onStageSelect?.(node.ref, "current");
                    }
                  }}
                >
                  <title>{node.label}</title>
                  <rect x={node.x} y={node.y} width={FLOW_LAYOUT.nodeWidth} height={FLOW_LAYOUT.nodeHeight} rx={10} className="r5-flow-node-box" />
                  <text x={centerX} y={node.y + 18} className="r5-flow-node-label">{line1}</text>
                  {line2 ? <text x={centerX} y={node.y + 34} className="r5-flow-node-label">{line2}</text> : null}
                  <text x={centerX} y={node.y + 54} className="r5-flow-node-counts">{`到达 ${node.reached} · 当前 ${node.current}`}</text>
                  {node.risk > 0 && !node.emptyAtCutoff ? (
                    <text x={centerX} y={node.y + FLOW_LAYOUT.nodeHeight + 18} className="r5-flow-node-risk">{`中高风险 ${node.risk}`}</text>
                  ) : null}
                  {node.emptyAtCutoff && <text x={centerX} y={node.y + 72} className="r5-flow-node-empty">本截止点无人到达</text>}
                  <g
                    role="button"
                    tabIndex={0}
                    data-flow-reached-target={node.ref}
                    aria-label={`查看${node.label}累计到达 ${node.reached} 人`}
                    ref={registerFlowFocus(flow.stages.length + graph.ribbons.length + index)}
                    onClick={(event) => {
                      event.stopPropagation();
                      onStageSelect?.(node.ref, "reached");
                    }}
                    onKeyDown={(event) => {
                      if (event.key === "Enter" || event.key === " ") {
                        event.preventDefault();
                        event.stopPropagation();
                        onStageSelect?.(node.ref, "reached");
                      }
                    }}
                  >
                    <rect x={centerX - 72} y={node.y + 36} width={64} height={24} fill="rgba(0,0,0,0)" />
                  </g>
                </g>
              );
            })}
          </svg>
          {!hideIncremental ? (
            <p className="r5-flow-risk-summary" data-r5-flow-risk-summary="true">
              <strong>中高风险变化摘要</strong>
              <span>{`新增 ${flow.riskChanges.new} · 升级 ${flow.riskChanges.upgraded} · 持续 ${flow.riskChanges.continued}`}</span>
            </p>
          ) : null}
          <p className="r5-flow-scope-bar">
            <strong>{`范围受试者 ${flow.total} 人`}</strong>
            {flow.coverageList
              // When every subject is already “齐备”, the chip restates the total — drop it.
              .filter((item) => !(item.key === "complete" && item.count === flow.total))
              .map((item) => <span key={item.key}>{`${item.label} ${item.count}`}</span>)}
            <small>当前项目/中心整体范围</small>
          </p>
          <div className="r5-flow-table" data-r5-flow-table="true">
            <div className="r5-flow-table-summary">
              <strong>受试者阶段流向明细</strong>
              <span>{subjectFlowHasSelection(selection) ? `共 ${flow.total} 人 · 当前筛选 ${filteredRows.length} 人` : `共 ${flow.total} 人`}</span>
              <button type="button" aria-expanded={tableOpen} onClick={() => setTableOpen((open) => !open)}>{tableOpen ? "收起明细" : "展开明细"}</button>
            </div>
            {tableOpen && (
              <FlowTableScroll>
                <table>
                  <thead>
                    <tr>
                      <th scope="col">受试者</th>
                      <th scope="col">中心</th>
                      <th scope="col">当前阶段</th>
                      <th scope="col">上一阶段</th>
                      <th scope="col">状态变化日期及依据日期</th>
                      <th scope="col">关键原因</th>
                      <th scope="col">中高风险摘要</th>
                      {!hideIncremental ? <th scope="col">阶段变化</th> : null}
                      {!hideIncremental ? <th scope="col">风险变化</th> : null}
                      <th scope="col">数据完整性</th>
                      <th scope="col">医学旅程</th>
                    </tr>
                  </thead>
                  <tbody>
                    {filteredRows.map((row) => {
                      const canJump = Boolean(row.spineRef && row.jumpStart && row.jumpEnd);
                      return (
                        <tr key={row.subjectRef} data-flow-subject-ref={row.subjectRef}>
                          <td>{row.label}</td>
                          <td>{row.siteLabel}</td>
                          <td>{row.currentLabel}</td>
                          <td>{row.priorLabel}</td>
                          <td>
                            <span className={`r5-date-chip r5-date-${row.dateState}`}>{DATE_STATE_CHIPS[row.dateState] || "日期待核实"}</span>
                            {row.enteredDate || "日期待确认"}
                            {row.basisDate ? `（依据 ${row.basisDate}）` : ""}
                          </td>
                          <td>{row.reason}</td>
                          <td>{row.riskSummary || "—"}</td>
                          {!hideIncremental ? <td>{FLOW_STAGE_CHANGE_LABELS[row.stageChange] || "—"}</td> : null}
                          {!hideIncremental ? <td>{FLOW_RISK_CHANGE_LABELS[row.riskChange] || "—"}</td> : null}
                          <td>{FLOW_PATH_STATE_LABELS[row.pathState] || "待确认"}</td>
                          <td>
                            <button
                              type="button"
                              className="r5-flow-jump-button"
                              disabled={!canJump}
                              title={canJump ? "进入受试者医学旅程" : "时间窗待确认"}
                              onClick={() => canJump && onSubjectJump?.(row)}
                            >
                              {canJump ? "进入医学旅程" : "时间窗待确认"}
                            </button>
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </FlowTableScroll>
            )}
          </div>
        </>
      )}
    </section>
  );
}

function OverviewView({
  payload,
  route,
  selectedRiskInstanceRef,
  onRiskSelect,
  onCenterSelect,
  onSubjectSelect,
  onSource,
  onFlowStageSelect,
  onFlowLinkSelect,
  onFlowMetricSelect,
  onFlowRiskToggle,
  onFlowClear,
  onFlowSubjectJump,
  suppressVersionClaim = false,
  flowTableOpen = true,
  continuityCounts = null,
}) {
  const projection = payload.projection;
  const flow = normalizeSubjectFlowView(projection);
  const flowSelection = subjectFlowSelectionFromRoute(route);
  const risks = [...projection.currentRisks].sort(riskSort);
  const selectedRisk = risks.find((risk) => risk.riskInstanceRef === selectedRiskInstanceRef) || null;
  const currentCounts = payload.counts?.currentRisk || {};
  const changes = projection.changeBands || [];
  const centerLabels = new Map((projection.centers || []).map((center, index) => [center.siteRef, center.siteLabel || `中心 ${index + 1}`]));
  const keyCountItems = [
    { key: "new", label: "新增" },
    { key: "upgraded", label: "升级" },
    { key: "reopened", label: "重开" },
    { key: "needs_rejudgment", label: "需重新判断" },
    { key: "mid_high_total", label: "中高风险" },
  ];
  // Live continuity counts are the public comparable signal. prior_snapshot_ref is forbidden
  // on R7 public envelopes (*_snapshot_ref), so incremental pages must not depend on it.
  const liveContinuity = Boolean(continuityCounts)
    && keyCountItems.some((item) => Number(continuityCounts?.[item.key] || 0) > 0);
  const compared = liveContinuity || changes.some((item) => item.prior_snapshot_ref);
  const comparable = liveContinuity
    || (compared && !changes.every((item) => item.change_kind === "not_comparable"));
  const scopedCenter = payload.identity?.site_ref ? projection.centers.find((center) => center.siteRef === payload.identity.site_ref) : null;
  const scopedMeasure = scopedCenter?.measures?.[0] || null;
  const showContinuityKpis = liveContinuity && !suppressVersionClaim;
  return (
    <div className="r5-view-stack">
      {!suppressVersionClaim ? (
        <section className="r5-comparison-note" data-comparable={comparable ? "yes" : compared ? "no" : "initial"}>
          <strong>{comparable ? "已与上一数据版本比较" : compared ? "本次暂不作增减比较" : "当前为首个监查版本"}</strong>
          <span>{comparable ? "变化类别与原因已逐项标示。" : compared ? "前后数据覆盖范围不一致，以下仅展示当前风险。" : "以下展示当前全部中高风险，后续版本将保留增量变化。"}</span>
        </section>
      ) : null}
      {showContinuityKpis ? (
        <section className="r5-summary-grid r5-summary-grid-continuity" data-r5-continuity-kpis="true" aria-label="本轮变化关键计数">
          {keyCountItems.map((item) => (
            <article key={item.key} className={`r5-stat-card${item.key === "mid_high_total" ? " r5-stat-danger" : ""}`}>
              <span>{item.label}</span>
              <strong data-count-key={item.key}>{numberText(continuityCounts[item.key], "0")}</strong>
              <small>本轮范围</small>
            </article>
          ))}
        </section>
      ) : suppressVersionClaim ? null : (
        <section className="r5-summary-grid">
          <article className="r5-stat-card r5-stat-danger"><span>高风险</span><strong>{numberText(currentCounts.high)}</strong><small>{scopedCenter?.coverageState === "small_sample" ? "当前中心计数；比例暂不评价" : "当前范围"}</small></article>
          <article className="r5-stat-card r5-stat-warning"><span>中风险</span><strong>{numberText(currentCounts.medium)}</strong><small>{scopedCenter?.coverageState === "small_sample" ? "当前中心计数；比例暂不评价" : "当前范围"}</small></article>
          <article className="r5-stat-card"><span>覆盖情况</span><strong>{projection.coverage?.denominator ? `${numberText(projection.coverage?.numerator)} / ${numberText(projection.coverage?.denominator)}` : "暂无法计算"}</strong><small>{projection.coverage?.denominator ? text(projection.coverage?.label, projection.coverage?.coverage_state || "覆盖待确认") : "样本量较小，暂不评价"}</small></article>
          <article className="r5-stat-card"><span>{compared && !comparable ? "当前风险总数" : "变化摘要"}</span><strong>{numberText(compared && !comparable ? currentCounts.total : payload.counts?.changeBand)}</strong><small>{scopedCenter?.coverageState === "small_sample" ? "当前中心计数；比例暂不评价" : compared && !comparable ? "本次不作增减比较" : "本次范围变化"}</small></article>
        </section>
      )}

      <SubjectFlowSection
        flow={flow}
        selection={flowSelection}
        onStageSelect={onFlowStageSelect}
        onLinkSelect={onFlowLinkSelect}
        onMetricSelect={onFlowMetricSelect}
        onRiskToggle={onFlowRiskToggle}
        onClear={onFlowClear}
        onSubjectJump={onFlowSubjectJump}
        initialTableOpen={flowTableOpen}
        hideIncremental={suppressVersionClaim}
      />

      <div className="r5-overview-columns">
        <section className="r5-panel r5-panel-wide">
          <div className="r5-section-heading"><span className="r5-eyebrow">当前风险</span><h2>高、中风险定位</h2></div>
          <RiskList
            risks={risks.filter((risk) => ["critical", "high", "medium"].includes(risk.severity))}
            onSelect={onRiskSelect}
            selectedRiskInstanceRef={selectedRiskInstanceRef}
            omitChangeClaims={suppressVersionClaim}
          />
        </section>
        <section className="r5-panel">
          {selectedRisk ? (
            <div className="r5-overview-inspector">
              <div className="r5-section-heading"><span className="r5-eyebrow">风险证据</span><h2>{selectedRisk.riskType}</h2></div>
              <RiskBadge risk={selectedRisk} />
              <dl>
                <div><dt>受试者</dt><dd>{text(selectedRisk.subjectLabel, "待确认")}</dd></div>
                <div><dt>日期</dt><dd>{selectedRisk.dateLabel}</dd></div>
                {!suppressVersionClaim ? <div><dt>本次变化</dt><dd>{selectedRisk.changeLabel}</dd></div> : null}
                {!suppressVersionClaim ? <div><dt>变化原因</dt><dd>{selectedRisk.changeCauseLabel}</dd></div> : null}
              </dl>
              {selectedRisk.evidenceSummary && (
                <div className="r5-evidence-summary">
                  <section><h3>为什么提醒</h3><p>{selectedRisk.evidenceSummary.why_reminded}</p></section>
                  <section><h3>依据</h3><p>{selectedRisk.evidenceSummary.basis}</p></section>
                  <section><h3>发现</h3><p>{selectedRisk.evidenceSummary.finding}</p></section>
                  <section><h3>行动项</h3><p>{selectedRisk.evidenceSummary.action_item}</p></section>
                  <section><h3>正反证</h3><p><strong>支持：</strong>{selectedRisk.evidenceSummary.supporting_evidence}</p><p><strong>不支持：</strong>{selectedRisk.evidenceSummary.counter_evidence}</p></section>
                  <section><h3>风险历史</h3><p>{selectedRisk.evidenceSummary.risk_history}</p></section>
                  <section><h3>核查问题草稿</h3><p>{selectedRisk.evidenceSummary.query_draft}</p></section>
                </div>
              )}
              {selectedRisk.analysisDisagreement && (
                <div className="r5-disagreement" aria-label="分析分歧">
                  <h3>分歧内容</h3><p>{selectedRisk.analysisDisagreement.disagreement}</p>
                  <div><strong>分析一</strong><span>{selectedRisk.analysisDisagreement.analysis_one}</span></div>
                  <div><strong>分析二</strong><span>{selectedRisk.analysisDisagreement.analysis_two}</span></div>
                  <div><strong>独立核对</strong><span>{selectedRisk.analysisDisagreement.independent_check}</span></div>
                  <p><strong>支持证据：</strong>{selectedRisk.analysisDisagreement.supporting_evidence}</p>
                  <p><strong>不支持证据：</strong>{selectedRisk.analysisDisagreement.counter_evidence}</p>
                  <p className="r5-disagreement-status">{selectedRisk.analysisDisagreement.status_zh}</p>
                </div>
              )}
              <button type="button" className="r5-source-button" onClick={() => onRiskSelect?.(selectedRisk)}>进入受试者医学旅程</button>
              <button type="button" className="r5-back-button" disabled={!selectedRisk.sourceLocatorRef} onClick={() => onSource?.(selectedRisk)}>查看原始来源</button>
            </div>
          ) : (
            <>
              <div className="r5-section-heading"><span className="r5-eyebrow">受试者入口</span><h2>查看受试者医学旅程</h2></div>
              <div className="r5-subject-list">
                {(projection.subjects || []).map((subject) => (
                  <button type="button" key={subject.subject_ref || subject.subject_id} onClick={() => onSubjectSelect?.(subject)}>
                    <span>{text(subject.label, subject.subject_ref || subject.subject_id)}</span>
                    <small>{centerLabels.get(subject.site_ref || subject.site_id) || "中心待确认"}</small>
                  </button>
                ))}
              </div>
            </>
          )}
        </section>
      </div>

      {scopedCenter && (
        <section className="r5-panel r5-center-summary" aria-label="中心模式与计算口径">
          <div className="r5-section-heading"><span className="r5-eyebrow">中心风险图谱</span><h2>{text(scopedCenter.siteLabel, centerLabel(scopedCenter.siteRef, "当前中心"))}</h2></div>
          <div className="r5-center-summary-grid">
            <div><span>重复模式</span><strong>{scopedMeasure?.denominator ? `${DOMAIN_LABELS[scopedCenter.domain] || "相关"}记录需关注` : "样本量不足，暂无法评价重复模式"}</strong></div>
            <div><span>受影响受试者</span><strong>{numberText(payload.counts?.affected_subject, "0")}</strong></div>
            <div><span>事件数</span><strong>{numberText(payload.counts?.event, "0")}</strong></div>
            <div><span>分子</span><strong>{scopedMeasure?.denominator ? numberText(scopedMeasure.numerator) : "暂无法计算"}</strong></div>
            <div><span>分母</span><strong>{scopedMeasure?.denominator ? numberText(scopedMeasure.denominator) : "暂无法计算"}</strong></div>
            <div><span>覆盖情况</span><strong>{text(scopedCenter.coverageLabel, "覆盖待确认")}</strong></div>
          </div>
          {!scopedMeasure?.denominator && <p className="r5-center-explanation"><strong>原因：</strong>当前中心没有可用于计算比例的有效分母，样本量较小，暂不评价中心重复模式。</p>}
        </section>
      )}

      <section className="r5-panel r5-center-overview-panel">
        <div className="r5-section-heading"><span className="r5-eyebrow">中心概览</span><h2>中心风险与数据覆盖</h2></div>
        <CenterTable centers={projection.centers} onSelect={onCenterSelect} />
      </section>
      <DomainLegend domains={projection.domains} />
    </div>
  );
}

const EventRow = memo(function EventRow({ event, onSelect, marker = null }) {
  const select = (pointerEvent) => {
    for (const row of pointerEvent.currentTarget.parentElement?.querySelectorAll("button.r5-event-row") || []) row.classList.remove("is-selected");
    pointerEvent.currentTarget.classList.add("is-selected");
    onSelect?.(event);
  };
  return (
    <button type="button" className="r5-event-row" data-event-ref={event.eventRef} onClick={select}>
      <DomainIcon domain={event.domain} encoding={event.domainEncoding} size="row" title={DOMAIN_LABELS[event.domain] || event.domainEncoding.shortLabel} />
      <span className="r5-event-main"><strong><span className={`r5-date-chip r5-date-${event.dateState}`}>{DATE_STATE_CHIPS[event.dateState] || "日期待核实"}</span>{event.eventLabel}</strong><small>{event.dateLabel} · {text(event.start, "日期待确认")}{event.end ? ` — ${event.end}` : ""}</small></span>
      {event.risk && <span className={`r5-event-risk-count r5-track-risk-${event.risk.severity}`}>{DOMAIN_LABELS[event.domain] || event.domainEncoding.shortLabel}·{riskSeverityLabel(event.risk.severity)}</span>}
      {marker ? <R7JourneyChangeMarker marker={marker} /> : null}
      {marker ? <span className="r7-journey-sr-only">，本轮变化：{marker.changeText}{marker.countSuffix}</span> : null}
    </button>
  );
});

function EventDetailPanel({ event }) {
  if (!event) return null;
  return (
    <div className="r5-inspector-card" data-event-detail={event.eventRef}>
      <span className="r5-eyebrow">事件详情</span>
      <span className={`r5-date-chip r5-date-${event.dateState}`}>{DATE_STATE_CHIPS[event.dateState] || "日期待核实"}</span>
      <h3>{event.eventLabel}</h3>
      <dl>
        <div><dt>医学域</dt><dd>{DOMAIN_LABELS[event.domain] || event.domainEncoding?.shortLabel || "域待确认"}</dd></div>
        <div><dt>日期状态</dt><dd>{event.dateLabel}</dd></div>
        <div><dt>起止</dt><dd>{text(event.start, "日期待确认")}{event.end ? ` — ${event.end}` : ""}</dd></div>
        <div><dt>访视</dt><dd>{text(event.visitLabel, "未绑定访视")}</dd></div>
        <div><dt>来源定位</dt><dd>{event.sourceLocatorRefs?.length ? `已定位到 ${event.sourceLocatorRefs.length} 条原始记录` : "待确认"}</dd></div>
      </dl>
    </div>
  );
}

function SubjectWorkspaceView({
  payload,
  route,
  view,
  zoomLevel,
  onRiskSelect,
  onEventSelect,
  onSource,
  onDrawerClose,
  onJourneyRowSelect,
  continuityResult = null,
  continuityUnavailable = "",
  continuityLoading = false,
}) {
  const projection = payload.projection;
  const [trendIndicator, setTrendIndicator] = useState(0);
  const [selectedJourneyRowRef, setSelectedJourneyRowRef] = useState("");
  const indicators = projection.indicators;
  const selectedEvent = (projection.events || []).find((event) => event.eventRef === route.event_ref)
    || (projection.events || []).find((event) => route.risk_anchor_ref && event.riskAnchorRefs?.includes(route.risk_anchor_ref))
    || null;
  const selectedEventRisk = selectedEvent
    ? projection.currentRisks.find((risk) => selectedEvent.riskAnchorRefs?.includes(risk.riskAnchorRef)) || null
    : null;
  const selectedRisk = selectedEvent
    ? selectedEventRisk
    : projection.currentRisks.find((risk) => risk.riskInstanceRef === route.risk_instance_ref) || null;
  const priorityRisks = projection.currentRisks.filter((risk) => ["critical", "high", "medium"].includes(risk.severity));
  const inspectorRisks = priorityRisks.length > 40 ? priorityRisks.slice(0, 16) : priorityRisks;
  const subjectLabel = projection.raw.subject?.subject_label || "当前受试者";
  const risksByAnchor = new Map((projection.currentRisks || []).map((risk) => [risk.riskAnchorRef, risk]));
  const enrichedSelectedEvent = selectedEvent
    ? {
      ...selectedEvent,
      risk: selectedEvent.riskAnchorRefs.map((ref) => risksByAnchor.get(ref)).filter(Boolean).sort(riskSort)[0],
      visitLabel: eventVisitContext(selectedEvent, projection.temporalSpine?.visits || []),
    }
    : null;

  // Slice-08C-3 R7-only gating (§5.1): the change markers and the detail
  // drawer are enabled only on product routes with a result_context_token;
  // legacy R5 keeps the existing inline inspector untouched.
  const journeyEnabled = payload?.publicResultContext === true && Boolean(route.result_context_token);
  const journeyRows = journeyEnabled
    ? r7JourneyContinuityRows(continuityResult, payload, route)
    : [];
  const journeyBinding = journeyEnabled
    ? bindR7ContinuityRowsToJourney(journeyRows, projection.events || [], projection.currentRisks || [])
    : null;
  const rowsByEventRef = new Map();
  const rowsByRiskInstance = new Map();
  const markersByEventRef = new Map();
  const markersByRiskInstance = new Map();
  if (journeyBinding) {
    for (const group of journeyBinding.events) {
      rowsByEventRef.set(group.eventRef, group.rows);
      for (const row of group.rows) {
        const instance = text(row.risk_instance_ref);
        if (!instance) continue;
        if (!rowsByRiskInstance.has(instance)) rowsByRiskInstance.set(instance, []);
        rowsByRiskInstance.get(instance).push(row);
      }
    }
    for (const group of journeyBinding.risks) {
      if (!rowsByRiskInstance.has(group.riskInstanceRef)) rowsByRiskInstance.set(group.riskInstanceRef, []);
      rowsByRiskInstance.get(group.riskInstanceRef).push(...group.rows);
    }
    for (const [eventRef, rows] of rowsByEventRef.entries()) markersByEventRef.set(eventRef, r7EventChangeMarker(rows));
    for (const [instance, rows] of rowsByRiskInstance.entries()) markersByRiskInstance.set(instance, r7EventChangeMarker(rows));
  }
  const journeyComparison = journeyEnabled && continuityResult?.ok
    ? continuityResult.value?.comparison || null
    : null;
  const journeyTruncationText = journeyEnabled ? r7JourneyTruncationText(journeyComparison) : "";
  const selectedEventRows = selectedEvent ? rowsByEventRef.get(selectedEvent.eventRef) || [] : [];
  const selectedRiskRows = selectedRisk ? rowsByRiskInstance.get(selectedRisk.riskInstanceRef) || [] : [];
  const continuityOnlyRows = journeyEnabled && !selectedEvent && !selectedRisk && route.risk_instance_ref
    ? journeyRows.filter((row) => text(row.risk_instance_ref) === text(route.risk_instance_ref))
    : [];
  const drawerRows = selectedRiskRows.length && route.risk_instance_ref
    ? selectedRiskRows
    : selectedEventRows.length
      ? selectedEventRows
      : selectedRiskRows.length
      ? selectedRiskRows
      : continuityOnlyRows;
  const drawerOpen = journeyEnabled && Boolean(selectedEvent || selectedRisk || continuityOnlyRows.length);
  const drawerRow = drawerRows.find((row) => text(row.row_ref) === selectedJourneyRowRef)
    || (drawerRows.length ? r7JourneyDrawerCurrentRow(drawerRows, route) : null);
  const drawerRowIndex = drawerRow ? drawerRows.findIndex((row) => row.row_ref === drawerRow.row_ref) : -1;
  const drawerRisk = drawerRow
    ? projection.currentRisks.find((risk) => text(risk.riskInstanceRef) === text(drawerRow.risk_instance_ref)) || selectedRisk
    : selectedRisk;
  const drawerSections = drawerOpen
    ? r7JourneyDrawerSections({ event: enrichedSelectedEvent, risk: drawerRisk, currentRow: drawerRow, comparison: journeyComparison, domainLabels: DOMAIN_LABELS })
    : null;
  const drawerSourceRisk = drawerRow || drawerRisk
    ? {
      riskRef: drawerRisk?.riskRef || "",
      riskInstanceRef: drawerRow?.risk_instance_ref || drawerRisk?.riskInstanceRef || "",
      sourceLocatorRef: drawerRow?.source_locator_ref || drawerRisk?.sourceLocatorRef || "",
      subjectRef: drawerRisk?.subjectRef || route.subject_ref,
      siteRef: drawerRisk?.siteRef || route.site_ref,
      spineRef: drawerRisk?.spineRef || route.spine_ref,
      visit_ref: drawerRisk?.visit_ref || route.visit_ref,
    }
    : null;
  const selectJourneyRow = (row) => {
    if (!row || typeof row !== "object") return;
    setSelectedJourneyRowRef(text(row.row_ref));
    if (onJourneyRowSelect) onJourneyRowSelect(row);
    else onRiskSelect?.({ ...(drawerRisk || {}), riskInstanceRef: text(row.risk_instance_ref) });
  };
  const closeJourneyDrawer = () => {
    setSelectedJourneyRowRef("");
    onDrawerClose?.();
  };
  const selectWorkspaceRisk = (risk) => {
    setSelectedJourneyRowRef("");
    onRiskSelect?.(risk);
  };
  const selectWorkspaceEvent = (event) => {
    setSelectedJourneyRowRef("");
    onEventSelect?.(event);
  };
  // Overlay/push decision (§5.3) measures the viewport and the host content
  // column; both are shared constants so offline tests and 08C-4 agree.
  const subjectColumnsRef = useRef(null);
  const [drawerViewport, setDrawerViewport] = useState(0);
  const [drawerHostWidth, setDrawerHostWidth] = useState(0);
  useLayoutEffect(() => {
    if (!journeyEnabled || typeof window === "undefined") return undefined;
    const update = () => {
      setDrawerViewport(window.innerWidth);
      setDrawerHostWidth(subjectColumnsRef.current?.getBoundingClientRect()?.width || 0);
    };
    update();
    window.addEventListener("resize", update);
    return () => window.removeEventListener("resize", update);
  }, [journeyEnabled]);
  const drawerMode = r7JourneyDrawerLayoutMode({ viewportWidth: drawerViewport, hostContentWidth: drawerHostWidth });
  const openSource = (risk) => {
    if (risk) onSource?.(risk);
  };
  return (
    <div className="r5-view-stack">
      <section className="r5-subject-banner">
        <div><span className="r5-eyebrow">受试者医学旅程</span><h2>{subjectLabel}</h2></div>
        <div className="r5-subject-meta"><span>{centerLabel(projection.raw.subject?.site_ref)}</span><span>{text(projection.temporalSpine.axisMode, "calendar") === "study_day" ? "研究日" : "日历日期"}</span></div>
      </section>
      <nav className="r5-workspace-tabs" aria-label="受试者工作区视图">
        {SUBJECT_VIEW_KEYS.map((key) => <button type="button" key={key} className={view === key ? "is-active" : ""} onClick={() => selectWorkspaceRisk({ __view: key })}>{SUBJECT_VIEW_LABELS[key]}</button>)}
      </nav>
      <div className={`r5-subject-columns${drawerOpen && drawerMode === "push" ? " is-r7-drawer-push" : ""}`} ref={subjectColumnsRef}>
        <section className="r5-panel r5-panel-wide">
          {view === "profile" ? indicators?.length ? (
            <section className="r5-indicator-panel" aria-label="指标趋势">
              <div className="r5-axis-heading r5-trend-window"><div><span className="r5-eyebrow">共享时间轴</span><h2 id={journeyEnabled ? R7_JOURNEY_AXIS_TITLE_ID : undefined} tabIndex={journeyEnabled ? -1 : undefined}>{text(projection.temporalSpine.axisMode, "calendar") === "study_day" ? "研究日" : "日历日期"}</h2></div><span className="r5-axis-window">{text(projection.temporalSpine.windowStart, "起点待确认")} — {text(projection.temporalSpine.windowEnd, "终点待确认")}</span></div>
              <div className="r5-section-heading"><span className="r5-eyebrow">指标趋势</span><h2>{text(indicators[trendIndicator]?.label, "指标待确认")}</h2></div>
              <div className="r5-indicator-switcher">{indicators.map((indicator, index) => <button type="button" key={indicator.indicator_ref || indicator.label} className={index === trendIndicator ? "is-active" : ""} onClick={() => setTrendIndicator(index)}>{indicator.label}</button>)}</div>
              <div className="r5-trend-chart" role="img" aria-label="指标趋势图">
                {(indicators[trendIndicator]?.points || []).map((point) => <div className="r5-trend-point" key={`${point.date}-${point.value}`}><span style={{ "--point-height": `${Math.max(14, Math.min(92, Number(point.value) * 8 || 14))}%` }} /><strong>{numberText(point.value)}</strong><small>{text(point.date, "日期待确认")}</small></div>)}
              </div>
            </section>
          ) : <div className="r5-empty-state">当前范围未提供指标趋势。</div>
          : (
            <DomainTracks
              projection={projection}
              zoomLevel={zoomLevel}
              selectedEventRef={route.event_ref}
              selectedRiskAnchorRef={route.risk_anchor_ref}
              onEventSelect={selectWorkspaceEvent}
              journeyEnabled={journeyEnabled}
              journeyMarkerByEventRef={journeyEnabled ? Object.fromEntries(markersByEventRef.entries()) : null}
              journeyTruncationText={journeyTruncationText}
            />
          )}
          {view === "journey" && <DomainLegend domains={projection.domains} />}
          {view === "timeline" && enrichedSelectedEvent && (
            <section className="r5-event-lane" aria-label="选中事件明细">
              <EventRow event={enrichedSelectedEvent} onSelect={selectWorkspaceEvent} marker={journeyEnabled ? markersByEventRef.get(enrichedSelectedEvent.eventRef) || null : null} />
            </section>
          )}
          {projection.aemhHistory?.length > 0 && (
            <section className="r5-history-panel"><div className="r5-section-heading"><span className="r5-eyebrow">AE/MH 前后记录</span><h2>漏报提示与补录匹配历史</h2></div>{projection.aemhHistory.map((item) => <div className="r5-history-detail" key={item.candidate_ref || item.item_ref}><div><span>原疑似漏报</span><strong>疑似 AE 漏报 / 疑似既往史未录入</strong></div><div><span>后续已补录记录</span><strong>{item.later_fact_ref ? "已发现对应补录记录" : "暂未发现"}</strong></div><div><span>匹配关系</span><strong>{HISTORY_LABELS[item.match_state] || "状态待确认"}</strong></div><p>匹配历史保留：原提示与后续记录均保留，便于复核前后变化。</p><p><strong>核查问题草稿：</strong>{selectedRisk?.evidenceSummary?.query_draft || "请核实原疑似漏报与后续记录是否为同一医学事件，并确认 AE/MH 记录是否完整。"}</p></div>)}</section>
          )}
        </section>
        <aside className="r5-panel r5-inspector" aria-label="风险定位">
          <div className="r5-section-heading"><span className="r5-eyebrow">风险定位</span><h2>检查依据</h2></div>
          <RiskList risks={inspectorRisks} onSelect={selectWorkspaceRisk} selectedRiskInstanceRef={selectedRisk?.riskInstanceRef} markersByRiskInstance={journeyEnabled ? Object.fromEntries(markersByRiskInstance.entries()) : null} />
          {priorityRisks.length > inspectorRisks.length && <p className="r5-event-lane-note">这里优先列出 16 项；其余 {priorityRisks.length - inspectorRisks.length} 项中高风险已在左侧八域泳道逐项呈现。</p>}
          {journeyEnabled ? (
            drawerOpen && drawerSections ? (
              <MedicalMonitoringR7JourneyDrawer
                mode={drawerMode}
                sections={drawerSections}
                changeRows={drawerRows}
                currentRowIndex={drawerRowIndex}
                onSelectRow={selectJourneyRow}
                onClose={closeJourneyDrawer}
                onSource={() => openSource(drawerSourceRisk)}
              />
            ) : null
          ) : (
            <>
              <EventDetailPanel event={enrichedSelectedEvent} />
              {selectedRisk && (
                <div className="r5-inspector-card">
                  <RiskBadge risk={selectedRisk} />
                  <h3>{selectedRisk.riskType}</h3>
                  <dl><div><dt>日期状态</dt><dd>{selectedRisk.dateLabel}</dd></div><div><dt>变化</dt><dd>{selectedRisk.changeLabel}</dd></div><div><dt>关联记录</dt><dd>{selectedRisk.riskType?.includes("AE/MH") ? "AE + MH" : text(selectedRisk.domainEncoding?.shortLabel, "待确认")}</dd></div></dl>
                  {selectedRisk.evidenceSummary && <div className="r5-query-draft"><strong>依据 / 发现 / 行动项</strong><p>{selectedRisk.evidenceSummary.query_draft}</p></div>}
                  <button type="button" className="r5-source-button" disabled={!selectedRisk.sourceLocatorRef} onClick={() => onSource?.(selectedRisk)}>查看来源证据</button>
                </div>
              )}
            </>
          )}
        </aside>
      </div>
    </div>
  );
}

function EvidenceView({ payload, route, onBack }) {
  const publicResult = payload?.publicResultContext === true;
  const evidence = payload.projection.sourceEvidence || {};
  const sourceRef = (payload.source_refs || []).find((item) => item.locator_ref === evidence.sourceLocatorRef) || payload.source_refs?.[0] || {};
  const canonicalLocation = text(evidence.canonical_location || sourceRef.canonical_location, "当前定位无法确认");
  const recordRef = text(evidence.record_ref || sourceRef.record_ref, "记录号待确认");
  const excerpt = text(evidence.excerpt || sourceRef.excerpt, "来源片段暂不可读取。");
  const lineage = Array.isArray(evidence.lineage) && evidence.lineage.length ? evidence.lineage : sourceRef.lineage;
  return (
    <div className="r5-view-stack">
      <section className="r5-panel r5-evidence-panel">
        <div className="r5-section-heading"><span className="r5-eyebrow">风险证据</span><h2>{text(evidence.title, publicResult ? "本次结果来源定位" : "精确来源定位")}</h2></div>
        <div className="r5-evidence-locator" data-r5-evidence-field="canonical_location"><span>原始来源</span><strong title={canonicalLocation}>{canonicalLocation}</strong><small>已定位到具体 listing 行或方案条款</small></div>
        <blockquote className="r5-evidence-excerpt" data-r5-evidence-field="excerpt"><span>原始引文</span><p>{excerpt}</p></blockquote>
        <dl className="r5-evidence-meta">
          <div data-r5-evidence-field="record_ref"><dt>记录号</dt><dd>{recordRef}</dd></div>
          <div data-r5-evidence-field="canonical_location"><dt>原始定位</dt><dd>{canonicalLocation}</dd></div>
          <div><dt>来源文件</dt><dd>{text(evidence.source_file_label || sourceRef.source_file_label, publicResult ? "本次结果来源" : "方案执行 Data Listing（合成验证）")}</dd></div>
          <div><dt>来源修订</dt><dd>{text(evidence.source_revision_label || sourceRef.source_revision_label, publicResult ? "本次数据范围" : "本次数据版本")}</dd></div>
          <div><dt>来源链路</dt><dd>{Array.isArray(lineage) && lineage.length ? lineage.join(" → ") : "来源链路待确认"}</dd></div>
          <div><dt>来源版本</dt><dd>{publicResult ? "本次公开结果" : dataVersionLabel(route.snapshot_ref)}</dd></div>
          <div><dt>风险时间窗</dt><dd>{route.window_start && route.window_end ? `${route.window_start} — ${route.window_end}` : "与当前风险 / 事件时间窗一致"}</dd></div>
          <div><dt>打开状态</dt><dd>已完成来源一跳定位</dd></div>
        </dl>
        <button type="button" className="r5-back-button" onClick={onBack}>返回受试者医学旅程</button>
      </section>
    </div>
  );
}

export function MedicalMonitoringR5Page({ routeState, onRouteChange, onReturn }) {
  const adapter = useMemo(() => createMedicalMonitoringR5Adapter(), []);
  const route = routeCanonical(routeState);
  const effectiveView = route.view === "overview" && route.site_ref ? "site_overview" : route.view;
  const isR7ProductRoute = Boolean(
    route.project_ref
      && (!route.run_ref || route.public_run_token || route.result_context_token),
  );
  const routeValid = routeState?.valid !== false && Boolean(route.project_ref);
  const [payload, setPayload] = useState(null);
  const [status, setStatus] = useState(routeValid ? "loading" : "invalid");
  const [error, setError] = useState(null);
  const [focusIndex, setFocusIndex] = useState(0);
  const [zoomLevel, setZoomLevel] = useState(0);
  const lastRouteKey = useRef("");
  const risks = payload?.projection?.currentRisks || [];
  const currentRouteRef = useRef(route);
  const currentRisksRef = useRef(risks);
  currentRouteRef.current = route;
  currentRisksRef.current = risks;

  useEffect(() => {
    if (isR7ProductRoute) {
      setPayload(null);
      setStatus("product");
      setError(null);
      lastRouteKey.current = "";
      return undefined;
    }
    const routeKey = JSON.stringify(route.view === "overview" || route.view === "site_overview"
      ? ["overview", route.project_ref, route.run_ref, route.snapshot_ref, route.cutoff_ref, route.site_ref]
      : route.view === "evidence"
        ? ["evidence", route.project_ref, route.run_ref, route.snapshot_ref, route.cutoff_ref, route.risk_instance_ref, route.source_locator_ref]
        : ["subject", route.project_ref, route.run_ref, route.snapshot_ref, route.cutoff_ref, route.site_ref, route.subject_ref, route.spine_ref, route.window_start, route.window_end]);
    if (lastRouteKey.current === routeKey && payload) return undefined;
    lastRouteKey.current = routeKey;
    if (!routeValid) {
      setPayload(null);
      setStatus("invalid");
      setError(null);
      return undefined;
    }
    const controller = new AbortController();
    setPayload(null);
    setError(null);
    setStatus("loading");
    const read = route.view === "overview" || route.view === "site_overview"
      ? adapter.getOverview({ projectId: route.project_ref, runRef: route.run_ref, snapshotRef: route.snapshot_ref, cutoffRef: route.cutoff_ref, siteRef: route.site_ref || "", signal: controller.signal })
      : route.view === "evidence"
        ? adapter.getSourceEvidence({ projectId: route.project_ref, runRef: route.run_ref, snapshotRef: route.snapshot_ref, cutoffRef: route.cutoff_ref, riskInstanceRef: route.risk_instance_ref, sourceLocatorRef: route.source_locator_ref, signal: controller.signal })
        : adapter.getSubjectWorkspace({ projectId: route.project_ref, subjectId: route.subject_ref, runRef: route.run_ref, snapshotRef: route.snapshot_ref, cutoffRef: route.cutoff_ref, siteRef: route.site_ref, spineRef: route.spine_ref, windowStart: route.window_start, windowEnd: route.window_end, riskInstanceRef: route.risk_instance_ref, riskAnchorRef: route.risk_anchor_ref, visitRef: route.visit_ref, eventRef: route.event_ref, signal: controller.signal });
    read.then((nextPayload) => {
      if (!controller.signal.aborted) {
        const responseIdentity = nextPayload?.identity || {};
        const nextRoute = normalizeMedicalMonitoringR5RouteState({
          ...route,
          ...Object.fromEntries(
            Object.entries(responseIdentity).filter(([key, value]) => key !== "return_context_key" && !route[key] && value !== null && value !== undefined && value !== ""),
          ),
          // The backend returns the API surface view (journey/overview); keep
          // the local presentation subview in the deep link.
          view: route.view,
        });
        setPayload(nextPayload);
        setStatus("ready");
        if (JSON.stringify(nextRoute) !== JSON.stringify(route)) onRouteChange?.(nextRoute);
      }
    }).catch((nextError) => {
      if (!controller.signal.aborted) {
        setPayload(null);
        setError(nextError);
        setStatus("error");
      }
    });
    return () => controller.abort();
  }, [adapter, isR7ProductRoute, onRouteChange, routeValid, route.project_ref, route.run_ref, route.snapshot_ref, route.cutoff_ref, route.site_ref, route.subject_ref, route.risk_instance_ref, route.view, route.spine_ref, route.axis_mode, route.window_start, route.window_end, route.visit_ref, route.event_ref, route.risk_anchor_ref, route.source_locator_ref]);

  useEffect(() => {
    const handleKey = (event) => {
      if (event.target instanceof HTMLInputElement || event.target instanceof HTMLTextAreaElement || event.target instanceof HTMLSelectElement || event.target?.isContentEditable) return;
      // 焦点位于流向图、流向筛选或流向表格时，不触发文档级风险列表与缩放快捷键。
      if (event.target instanceof SVGElement) return;
      if (event.target instanceof Element && event.target.closest("[data-r5-flow-scope]")) return;
      if (event.key === "-" || event.key === "0" || event.key === "+" || (event.key === "=" && event.shiftKey)) {
        event.preventDefault();
        setZoomLevel((current) => event.key === "0" ? 0 : event.key === "-" ? Math.max(-1, current - 1) : Math.min(1, current + 1));
        return;
      }
      const available = risks.filter((risk) => ["critical", "high", "medium"].includes(risk.severity));
      if (event.key === "ArrowDown" || event.key === "ArrowUp") {
        if (!available.length) return;
        event.preventDefault();
        setFocusIndex((current) => event.key === "ArrowDown"
          ? Math.min(available.length - 1, current + 1)
          : Math.max(0, current - 1));
      }
      if (event.key === "Enter" && available[focusIndex]) {
        event.preventDefault();
        const risk = available[focusIndex];
        onRouteChange?.(routeStateForMedicalMonitoringR5View(route, "journey", {
          subject_ref: risk.subjectRef || route.subject_ref,
          site_ref: risk.siteRef || route.site_ref,
          risk_ref: risk.riskRef,
          risk_instance_ref: risk.riskInstanceRef,
          event_ref: risk.eventRef,
          risk_anchor_ref: risk.riskAnchorRef,
          spine_ref: risk.spineRef,
          visit_ref: risk.visit_ref || route.visit_ref,
        }));
      }
    };
    window.addEventListener("keydown", handleKey);
    return () => window.removeEventListener("keydown", handleKey);
  }, [focusIndex, onRouteChange, risks, route, routeState]);

  const navigate = (view, patch = {}) => onRouteChange?.(routeStateForMedicalMonitoringR5View(route, view, patch));
  const selectRisk = useCallback((risk) => {
    const currentRoute = currentRouteRef.current;
    if (risk?.__view) {
      onRouteChange?.(routeStateForMedicalMonitoringR5View(currentRoute, risk.__view));
      return;
    }
    const next = { risk_ref: risk.riskRef, risk_instance_ref: risk.riskInstanceRef, event_ref: risk.eventRef, risk_anchor_ref: risk.riskAnchorRef, subject_ref: risk.subjectRef || currentRoute.subject_ref, site_ref: risk.siteRef || currentRoute.site_ref, spine_ref: risk.spineRef || currentRoute.spine_ref, visit_ref: risk.visit_ref || currentRoute.visit_ref };
    const nextView = currentRoute.view === "overview" || currentRoute.view === "site_overview" ? "journey" : currentRoute.view;
    onRouteChange?.(routeStateForMedicalMonitoringR5View(currentRoute, nextView, next));
  }, [onRouteChange]);
  const selectCenter = (center) => navigate("site_overview", { site_ref: center.siteRef });
  const selectSubject = (subject) => navigate("journey", { subject_ref: subject.subject_ref || subject.subject_id, site_ref: subject.site_ref || subject.site_id, spine_ref: subject.spine_ref || route.spine_ref, run_ref: route.run_ref, snapshot_ref: route.snapshot_ref, cutoff_ref: route.cutoff_ref, window_start: route.window_start, window_end: route.window_end });
  const selectEvent = useCallback((event) => {
    const currentRoute = currentRouteRef.current;
    const riskAnchorRef = event.riskAnchorRefs[0] || "";
    const linkedRisk = currentRisksRef.current.find((risk) => risk.riskAnchorRef === riskAnchorRef);
    startTransition(() => onRouteChange?.(routeStateForMedicalMonitoringR5View(currentRoute, currentRoute.view, {
        event_ref: event.eventRef,
        visit_ref: event.visitRef || event.visit_ref || "",
        risk_anchor_ref: riskAnchorRef,
        risk_ref: linkedRisk?.riskRef || "",
        risk_instance_ref: linkedRisk?.riskInstanceRef || "",
      })));
  }, [onRouteChange]);
  const openSource = (risk) => navigate("evidence", { risk_ref: risk.riskRef, risk_instance_ref: risk.riskInstanceRef, source_locator_ref: risk.sourceLocatorRef, subject_ref: risk.subjectRef || route.subject_ref, site_ref: risk.siteRef || route.site_ref, spine_ref: risk.spineRef || route.spine_ref, window_start: route.window_start, window_end: route.window_end });
  const backFromEvidence = () => navigate("journey");
  // Slice-08C-3 drawer close: clears only the four selection keys and keeps
  // the project/result/center/subject/spine/window and the current view.
  const closeJourneyDrawer = useCallback(() => {
    onRouteChange?.(r7JourneyDrawerClosePatch(currentRouteRef.current));
  }, [onRouteChange]);
  // 流向筛选统一写回路由（主选择互斥）；Journey 往返由路由层保留 flow 键。
  const selectFlowStage = useCallback((stageRef, metric) => {
    const currentRoute = currentRouteRef.current;
    startTransition(() => onRouteChange?.(routeStateForMedicalMonitoringR5View(currentRoute, currentRoute.view, {
      flow_stage_ref: stageRef,
      flow_node_metric: metric === "reached" ? "reached" : "current",
      flow_link_ref: "",
    })));
  }, [onRouteChange]);
  const selectFlowLink = useCallback((linkRef) => {
    const currentRoute = currentRouteRef.current;
    startTransition(() => onRouteChange?.(routeStateForMedicalMonitoringR5View(currentRoute, currentRoute.view, {
      flow_link_ref: linkRef,
      flow_stage_ref: "",
      flow_node_metric: "",
    })));
  }, [onRouteChange]);
  const selectFlowMetric = useCallback((metric) => {
    const currentRoute = currentRouteRef.current;
    startTransition(() => onRouteChange?.(routeStateForMedicalMonitoringR5View(currentRoute, currentRoute.view, {
      flow_node_metric: metric === "reached" ? "reached" : "current",
    })));
  }, [onRouteChange]);
  const toggleFlowRiskBand = useCallback(() => {
    const currentRoute = currentRouteRef.current;
    const next = flowText(currentRoute, ["flow_risk_band"]) === "mid_high" ? "" : "mid_high";
    startTransition(() => onRouteChange?.(routeStateForMedicalMonitoringR5View(currentRoute, currentRoute.view, {
      flow_risk_band: next,
    })));
  }, [onRouteChange]);
  const clearFlowSelection = useCallback(() => {
    const currentRoute = currentRouteRef.current;
    startTransition(() => onRouteChange?.(routeStateForMedicalMonitoringR5View(currentRoute, currentRoute.view, {
      flow_stage_ref: "",
      flow_node_metric: "",
      flow_link_ref: "",
      flow_risk_band: "",
    })));
  }, [onRouteChange]);
  const jumpFlowSubject = useCallback((row) => {
    if (!row?.spineRef || !row?.jumpStart || !row?.jumpEnd) return;
    const currentRoute = currentRouteRef.current;
    onRouteChange?.(routeStateForMedicalMonitoringR5View(currentRoute, "journey", {
      subject_ref: row.subjectRef,
      site_ref: row.siteRef || currentRoute.site_ref,
      spine_ref: row.spineRef,
      window_start: row.jumpStart,
      window_end: row.jumpEnd,
    }));
  }, [onRouteChange]);
  const availableViews = MEDICAL_MONITORING_R5_VIEWS.filter((view) => {
    if (view === "overview") return true;
    if (view === "site_overview") return Boolean(route.site_ref);
    if (SUBJECT_VIEW_KEYS.includes(view)) return Boolean(route.subject_ref);
    if (view === "evidence") return Boolean(route.risk_instance_ref && route.source_locator_ref);
    return false;
  });

  if (isR7ProductRoute) {
    return (
      <MedicalMonitoringR7ProductLoop
        projectId={route.project_ref}
        route={route}
        onRouteChange={onRouteChange}
        onReturn={onReturn}
        OverviewView={OverviewView}
        SubjectWorkspaceView={SubjectWorkspaceView}
        EvidenceView={EvidenceView}
      />
    );
  }

  return (
    <main className="r5-page" data-r5-view={effectiveView || "invalid"} data-r5-status={status} data-r5-zoom={zoomLevel}>
      <header className="r5-page-header">
        <div><span className="r5-eyebrow">医学监查</span><h1>{VIEW_LABELS[effectiveView] || "项目风险概览"}</h1><p>从项目风险进入中心与受试者，沿时间轴查看事件、趋势和来源依据</p></div>
        <div className="r5-page-actions"><ZoomControls zoomLevel={zoomLevel} onZoomChange={setZoomLevel} /><button type="button" className="r5-back-button" onClick={onReturn}>医学监查首页</button></div>
      </header>
      <IdentityStrip identity={route} project={payload?.projection?.project || {}} />
      <nav className="r5-route-tabs" aria-label="医学监查页面导航">
        {availableViews.map((view) => {
          const label = view === "overview" && route.return_context_key && route.view !== "overview" ? "返回项目风险概览" : VIEW_LABELS[view];
          return <button type="button" key={view} className={effectiveView === view ? "is-active" : ""} onClick={() => navigate(view)}>{label}</button>;
        })}
      </nav>
      <MedicalMonitoringR7ProgressPanel routeCanonical={route} />
      {status === "invalid" && <section className="r5-state-panel" role="alert"><strong>当前定位无法确认</strong><span>请返回上一级并重新打开已绑定的项目范围。</span></section>}
      {status === "loading" && <section className="r5-state-panel" role="status"><strong>正在读取当前范围</strong><span>项目身份、数据截止与来源链路保持一致后展示。</span></section>}
      {status === "error" && <section className="r5-state-panel" role="alert"><strong>当前范围暂不可用</strong><span>{unavailableMessage(error)}</span><button type="button" onClick={() => onRouteChange?.({ ...route })}>重新读取</button></section>}
      {status === "ready" && payload && (
        <>
          {route.view === "overview" || route.view === "site_overview" ? <OverviewView payload={payload} route={route} selectedRiskInstanceRef={route.risk_instance_ref} onRiskSelect={selectRisk} onCenterSelect={selectCenter} onSubjectSelect={selectSubject} onSource={openSource} onFlowStageSelect={selectFlowStage} onFlowLinkSelect={selectFlowLink} onFlowMetricSelect={selectFlowMetric} onFlowRiskToggle={toggleFlowRiskBand} onFlowClear={clearFlowSelection} onFlowSubjectJump={jumpFlowSubject} /> : null}
          {SUBJECT_VIEW_KEYS.includes(route.view) ? <SubjectWorkspaceView payload={payload} route={route} view={route.view} zoomLevel={zoomLevel} onRiskSelect={selectRisk} onEventSelect={selectEvent} onSource={openSource} onDrawerClose={closeJourneyDrawer} /> : null}
          {route.view === "evidence" ? <EvidenceView payload={payload} route={route} onBack={backFromEvidence} /> : null}
        </>
      )}
    </main>
  );
}

export default MedicalMonitoringR5Page;
