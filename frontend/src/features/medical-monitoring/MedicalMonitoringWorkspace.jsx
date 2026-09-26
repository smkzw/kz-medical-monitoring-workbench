import { memo, startTransition, useCallback, useEffect, useLayoutEffect, useMemo, useRef, useState } from "react";
import {
  createMedicalMonitoringWorkspaceApi,
  MedicalMonitoringWorkspaceApiError,
  medicalMonitoringWorkspaceDomainRegistry,
} from "./medicalMonitoringWorkspaceApi.mjs";
import {
  MEDICAL_MONITORING_WORKSPACE_VIEWS,
  normalizeMedicalMonitoringWorkspaceRouteState,
  routeStateForMedicalMonitoringWorkspaceView,
} from "./medicalMonitoringWorkspaceRouteState.mjs";
import { layoutJourneyTimeline, parseTimelineDate, timelineDatePrecision, visitAxisDate } from "./medicalMonitoringJourneyTimeline.mjs";
import { DomainIcon } from "./DomainIcon.jsx";
import { KzSubjectFlowSankey, KzRiskTypeBars, KzCenterDomainHeatmap } from "./medicalMonitoringKzChart.jsx";
import { MedicalMonitoringProgressPanel } from "./MedicalMonitoringProgressPanel.jsx";
import { MedicalMonitoringProductLoop } from "./MedicalMonitoringProductLoop.jsx";
import {
  MedicalMonitoringJourneyDrawer,
  MONITORING_JOURNEY_AXIS_TITLE_ID,
  MonitoringJourneyChangeMarker,
  monitoringJourneyDrawerLayoutMode,
  monitoringJourneyDrawerSections,
} from "./MedicalMonitoringJourneyDrawer.jsx";
import {
  bindMonitoringContinuityRowsToJourney,
  monitoringEventChangeMarker,
  monitoringJourneyContinuityRows,
  monitoringJourneyDrawerClosePatch,
  monitoringJourneyDrawerCurrentRow,
  monitoringJourneyTruncationText,
} from "./medicalMonitoringJourneyChanges.mjs";
import {
  MONITORING_COMPARISON_STATE_COMPARED,
  MONITORING_COMPARISON_STATE_UNCERTAIN,
  monitoringComparisonState,
} from "./medicalMonitoringComparisonState.mjs";
import {
  MONITORING_TREND_MODE_BARS,
  monitoringTrendScaleView,
} from "./medicalMonitoringTrendScale.mjs";
import "./medicalMonitoringWorkspace.css";

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

const DOMAIN_LABELS = Object.freeze(Object.fromEntries(
  Object.entries(medicalMonitoringWorkspaceDomainRegistry).map(
    ([domain, encoding]) => [domain, encoding.label],
  ),
));

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
  return normalizeMedicalMonitoringWorkspaceRouteState(routeState?.canonical || routeState || {});
}

function unavailableMessage(error) {
  if (error instanceof MedicalMonitoringWorkspaceApiError) {
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
    <section className="monitoring-domain-legend" aria-label="八域编码">
      <div className="monitoring-section-heading">
        <span className="monitoring-eyebrow">图例</span>
        <h2>事件类别与风险标记</h2>
      </div>
      <div className="monitoring-domain-grid">
        {domains.map((domain) => (
          <div className="monitoring-domain-key" key={domain.domain}>
            <DomainIcon domain={domain.domain} encoding={domain} size="legend" title={DOMAIN_LABELS[domain.domain] || domain.shortLabel} />
            <span>
              <strong>{DOMAIN_LABELS[domain.domain] || domain.shortLabel}</strong>
              <small>医学事件</small>
            </span>
          </div>
        ))}
        <div className="monitoring-risk-key">
          <span className="monitoring-risk-overlay" aria-hidden="true">AE·高</span>
          <span><strong>风险提示</strong><small>外圈、徽标与文字共同标示风险等级</small></span>
        </div>
      </div>
    </section>
  );
}

const DETAIL_DENSITY_LABELS = { compact: "精简", standard: "标准", detailed: "详细" };

function ZoomControls({
  timeViewport,
  timeZoom,
  detailDensity,
  onViewportChange,
  onDensityChange,
  focusAvailable = false,
}) {
  // W05-J1 §3②：时间视窗（全程/自选/聚焦）与信息密度（精简/标准/详细）
  // 拆成两个独立控制组——视窗决定px/day与scale范围；密度只改聚合阈值/
  // 标签详略，切换密度不移动时间轴（A17）。
  const setViewport = (next, zoom = 0) => onViewportChange?.(next, zoom);
  return (
    <div className="monitoring-zoom-controls" aria-label="时间视窗与信息密度控制">
      <span className="monitoring-zoom-label">时间视窗</span>
      <div className="monitoring-zoom-buttons" role="group" aria-label="时间视窗模式">
        <button type="button" aria-label="全程自适应（默认）" aria-pressed={timeViewport === "fit"} onClick={() => setViewport("fit")}>全程</button>
        <button type="button" aria-label="自选更密时间尺度" aria-pressed={timeViewport === "custom" && timeZoom < 0} onClick={() => setViewport("custom", -1)}>更密</button>
        <button type="button" aria-label="自选更疏时间尺度" aria-pressed={timeViewport === "custom" && timeZoom > 0} onClick={() => setViewport("custom", 1)}>更疏</button>
        <button
          type="button"
          aria-label="聚焦选中问题周边时间窗"
          aria-pressed={timeViewport === "focus"}
          disabled={!focusAvailable}
          title={focusAvailable ? "" : "先在时间轴上选中一个事件后可聚焦"}
          onClick={() => setViewport("focus")}
        >聚焦</button>
      </div>
      <span className="monitoring-zoom-label">信息密度</span>
      <div className="monitoring-zoom-buttons" role="group" aria-label="信息密度级别">
        {["compact", "standard", "detailed"].map((density) => (
          <button
            key={density}
            type="button"
            aria-label={`信息密度${DETAIL_DENSITY_LABELS[density]}`}
            aria-pressed={detailDensity === density}
            onClick={() => onDensityChange?.(density)}
          >{DETAIL_DENSITY_LABELS[density]}</button>
        ))}
      </div>
      <small>
        {timeViewport === "fit"
          ? "全程自适应容器宽度"
          : timeViewport === "focus"
            ? "聚焦选中问题周边时间窗"
            : semanticZoomLabel(timeZoom)}
        {" "}· 密度只改聚合与标签详略，不移动时间轴
      </small>
    </div>
  );
}

// R24V2-B02：风险徽章按severity_source诚实呈现——recorded才有
// 高/中/低风险着色；unknown显示"严重度未知"（severity字段只是占位，
// 不得当医学分级）；inferred（非AE推定锚点）不作为医学风险徽章呈现。
function riskSeverityInfo(risk) {
  if (!risk) return null;
  const source = risk.severity_source || risk.severitySource || "recorded";
  if (source === "inferred") return null;
  if (source === "unknown") return { label: "严重度未知", css: "unknown", chip: "未" };
  if (risk.severity === "high" || risk.severity === "critical") return { label: "高风险", css: risk.severity, chip: "高" };
  if (risk.severity === "medium") return { label: "中风险", css: "medium", chip: "中" };
  if (risk.severity === "low") return { label: "低风险", css: "low", chip: "低" };
  return null;
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
  // W05-J2 A23：全无有效日期时不画月份刻度——不制造假2026时间轴。
  if (scale.hasValidDates === false) return [];
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
  const events = Array.from(lane?.querySelectorAll?.("button.monitoring-track-event") || []);
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
  timeViewport = "fit",
  detailDensity = "standard",
  timeZoom = 0,
  selectedEventRef,
  selectedRiskAnchorRef,
  onEventSelect,
  journeyEnabled = false,
  journeyMarkerByEventRef = null,
  journeyTruncationText = "",
}) {
  // R24V2-U01/U02：ResizeObserver绑定实际plot宿主——容器/侧栏/抽屉
  // 宽度变化都触发重测；零宽初始状态等待测量（containerWidth=null时
  // scale保持旧行为，不留永久兜底宽度）。卸载时断开观察。
  const [expandedAggregates, setExpandedAggregates] = useState(() => new Set());
  // W05-J2 J14：显式收起选中聚合应有有效状态出口——用户收起后，选中
  // 联动不再强制重新展开（收起优先于选中自动展开）。
  const [collapsedAggregates, setCollapsedAggregates] = useState(() => new Set());
  // R24V2-U13：聚合键盘路径——展开时焦点进入首个成员，收起时焦点
  // 回到组开关（keyboard user不因按钮卸载而丢失位置）。autoFocus只在
  // 用户显式展开的那次mount生效（选择联动自动展开不抢焦点）。
  const aggregateToggleRefs = useRef(new Map());
  const aggregateUserToggleKey = useRef(null);
  const scrollShellRef = useRef(null);
  const [containerWidth, setContainerWidth] = useState(null);
  // W05-J1 A18：聚焦视窗的窗口=选中事件日期±15天（scale范围只由viewport
  // 决定）；未选中/无有效日期时不进入聚焦，按钮在父层禁用。
  const focusWindow = useMemo(() => {
    if (timeViewport !== "focus") return null;
    const target = (projection.events || []).find(
      (event) => event.eventRef === selectedEventRef,
    );
    const rawStart = target?.start || target?.start_date || null;
    const rawEnd = target?.end || target?.end_date || rawStart;
    const startMs = parseTimelineDate(rawStart);
    const endMs = parseTimelineDate(rawEnd) ?? startMs;
    if (startMs == null) return null;
    const padMs = 15 * 24 * 60 * 60 * 1000;
    const iso = (ms) => new Date(ms).toISOString().slice(0, 10);
    return { start: iso(startMs - padMs), end: iso((endMs ?? startMs) + padMs) };
  }, [timeViewport, selectedEventRef, projection.events]);
  useEffect(() => {
    // 观察滚动外壳（宿主宽度=可用宽度），不是被scale撑大的canvas本身。
    const host = scrollShellRef.current;
    if (!host || typeof ResizeObserver === "undefined") return undefined;
    const observer = new ResizeObserver((entries) => {
      const width = entries?.[0]?.contentRect?.width;
      if (typeof width === "number" && width > 0) {
        // 减去标签列宽度（CSS变量176px），得到真实绘图可用宽
        const labelW = 176;
        const available = Math.floor(width) - labelW;
        if (available > 200) setContainerWidth(available);
      }
    });
    observer.observe(host);
    return () => observer.disconnect();
  }, []);
  const layout = useMemo(() => layoutJourneyTimeline({
    domains: projection.domains || [],
    events: projection.events || [],
    visits: projection.temporalSpine?.visits || [],
    risks: projection.currentRisks || [],
    pendingDates: projection.temporalSpine?.pendingDates || [],
    windowStart: projection.temporalSpine?.windowStart,
    windowEnd: projection.temporalSpine?.windowEnd,
    viewport: timeViewport,
    timeZoom,
    density: detailDensity,
    focusWindow,
    // 标签栏宽度在CSS侧计入；此处给的是canvas宿主的全宽，scale内部
    // 会减去pad；标签列（--timeline-label-width）在fit模式下由调用方
    // 宽度承担，fit结果=宿主全宽（含标签列），绘图区=减pad后。
    // custom视窗画布按px/day自扩展，不传入容器宽。
    containerWidth: timeViewport !== "custom" && containerWidth ? containerWidth : null,
  }), [projection, timeViewport, timeZoom, detailDensity, focusWindow, containerWidth]);
  const journeyMarkerFor = (eventRef) => (journeyEnabled && journeyMarkerByEventRef ? journeyMarkerByEventRef[eventRef] || null : null);
  // R24V2-B02：中/高风险计数只统计severity_source=recorded的行；
  // unknown/inferred锚点不进风险分级统计（另有N条单独标示）。
  const recordedRiskCounts = (projection.currentRisks || []).reduce(
    (counts, risk) => {
      const source = risk.severity_source || risk.severitySource || "recorded";
      if (source === "recorded") counts[risk.severity] = (counts[risk.severity] || 0) + 1;
      return counts;
    },
    {},
  );
  const unrecordedRiskCount = (projection.currentRisks || []).length
    - Object.values(recordedRiskCounts).reduce((sum, n) => sum + n, 0);
  const axisMode = text(projection.temporalSpine?.axisMode, "calendar") === "study_day" ? "研究日" : "日历日期";
  const selectedRef = selectedEventRef || "";
  const monthTicks = timelineMonthTicks(layout.scale);
  let lastVisitLabelX = -Infinity;
  const labeledVisits = layout.visitMarks.map((mark, index) => {
    // W05-J1：标签间距跟随信息密度（详略预算），与时间视窗无关。
    const minGap = detailDensity === "detailed" ? 84 : detailDensity === "compact" ? 124 : 104;
    const showLabel = index === 0 || mark.x - lastVisitLabelX >= minGap;
    if (showLabel) lastVisitLabelX = mark.x;
    return { ...mark, showLabel, labelSide: index % 2 ? "below" : "above" };
  });
  return (
    <section className="monitoring-domain-tracks" aria-label="共享横向时间轴与八域泳道" data-timeline-mode="shared-horizontal">
      <div className="monitoring-axis-heading">
        <div>
          <span className="monitoring-eyebrow">共享时间轴</span>
          <h2 id={journeyEnabled ? MONITORING_JOURNEY_AXIS_TITLE_ID : undefined} tabIndex={journeyEnabled ? -1 : undefined}>{axisMode}</h2>
        </div>
        <span className="monitoring-axis-window">{layout.scale.hasValidDates === false ? "无有效日期" : `${text(projection.temporalSpine?.windowStart, layout.scale.windowStartIso)} — ${text(projection.temporalSpine?.windowEnd, layout.scale.windowEndIso)}`}</span>
      </div>
      {layout.scale.hasValidDates === false ? (
        <p className="monitoring-query-intro" data-monitoring-timeline-empty>当前数据没有可上轴的有效日期：月份刻度与时间窗已隐藏，日期待确认的记录在下方单独列示。</p>
      ) : null}
      {journeyTruncationText ? <p className="monitoring-journey-truncation" role="status" data-journey-truncation>{journeyTruncationText}</p> : null}
      <div className="monitoring-density-summary" aria-label="高密度医学旅程摘要">
        <strong>{(projection.events || []).length} 条事件 · {(projection.temporalSpine?.visits || []).length} 次访视 · {(projection.currentRisks || []).length} 个风险锚点</strong>
        <span>
          高风险 {recordedRiskCounts.high || 0} · 中风险 {recordedRiskCounts.medium || 0}；中高风险逐项显示，低风险与常规记录
          <span className="monitoring-phrase-keep">按缩放级别聚合</span>
          {unrecordedRiskCount > 0 ? `；另有 ${unrecordedRiskCount} 条事件严重度未知或为系统推定锚点，不作分级展示` : ""}。
        </span>
      </div>
      <div className="monitoring-lane-index" aria-label="医学事件泳道概览（零事件域已折叠）">
        {layout.lanes.map((lane) => {
          // R24V2-U06：零事件域折叠为明确的“无记录”chip而非大空框；
          // 计数即筛选入口的语义标签（点击滚动到对应泳道由既有锚点承担）。
          const empty = lane.eventCount === 0;
          return (
            <span
              key={lane.domain}
              className={empty ? "monitoring-lane-chip is-empty" : "monitoring-lane-chip"}
              aria-label={empty ? `${DOMAIN_LABELS[lane.domain] || lane.encoding.shortLabel}：无记录` : undefined}
            >
              <DomainIcon domain={lane.domain} size="summary" />
              <strong>{laneChipLabel(DOMAIN_LABELS[lane.domain] || lane.encoding.shortLabel)}</strong>
              <small>{empty ? "无记录" : `${lane.eventCount} 条`}</small>
            </span>
          );
        })}
      </div>
      <TimelineScrollShell>
        <div ref={scrollShellRef} style={{ width: "100%", minWidth: 0 }}>
        <div
          className="monitoring-timeline-canvas"
          style={{ "--timeline-plot-width": `${layout.scale.width}px`, width: `calc(${layout.scale.width}px + var(--timeline-label-width))` }}
          data-timeline-width={layout.scale.width}
        >
          <div className="monitoring-time-grid" aria-hidden="true">
            {monthTicks.map((tick) => <span key={tick.iso} style={{ left: `calc(var(--timeline-label-width) + ${tick.x}px)` }}><small>{tick.label}</small></span>)}
          </div>
          <div className="monitoring-axis-track" aria-label="访视节点">
            <div className="monitoring-axis-label"><strong>访视</strong><small>按实际日期定位</small></div>
            <div className="monitoring-axis-baseline" aria-hidden="true" />
            {labeledVisits.map((mark, index) => {
              const visit = mark.visit;
              return (
                <div
                  className={`monitoring-visit-node monitoring-visit-label-${mark.labelSide}${mark.showLabel ? " is-labeled" : ""}`}
                  data-visit-ref={mark.visitRef}
                  key={mark.visitRef || `${mark.iso}-${index}`}
                  style={{ left: `calc(var(--timeline-label-width) + ${mark.x}px)` }}
                  title={visitDateLabel(visit)}
                >
                  <span className="monitoring-visit-dot" aria-hidden="true" />
                  {mark.showLabel ? <><strong>{text(visit.visit_label || visit.visit_name || visit.visit_code, visit.visit_kind === "unscheduled" ? "非计划访视" : `第 ${visit.visit_number || index + 1} 次访视`)}</strong><small>{visitDateLabel(visit)}</small></> : null}
                </div>
              );
            })}
          </div>
          <div className="monitoring-domain-track-grid" role="list" aria-label="八域事件泳道">
            {layout.lanes.map((lane) => {
              const displayStackRows = lane.stackRows + (lane.aggregates.length ? 1 : 0);
              const eventRowOffset = lane.aggregates.length ? 1 : 0;
              return (
              <article
                className="monitoring-domain-track"
                data-domain-track={lane.domain}
                data-stack-rows={displayStackRows}
                aria-label={`${DOMAIN_LABELS[lane.domain] || lane.encoding.shortLabel}事件泳道`}
                key={lane.domain}
                role="listitem"
                style={{ "--lane-stack-rows": displayStackRows }}
              >
                <div className="monitoring-domain-track-head">
                  <DomainIcon domain={lane.domain} encoding={lane.encoding} size="lane" title={DOMAIN_LABELS[lane.domain] || lane.encoding.shortLabel} />
                  <div>
                    <strong>{DOMAIN_LABELS[lane.domain] || lane.encoding.shortLabel}</strong>
                    <small>{lane.eventCount ? `${lane.eventCount} 条` : "当前无事件"}{lane.riskAnchorCount ? ` · ${lane.riskAnchorCount} 个风险` : ""}</small>
                  </div>
                </div>
                <div className="monitoring-domain-track-events" data-lane-canvas="true">
                  {lane.marks.length === 0 && lane.aggregates.length === 0 ? <span className="monitoring-domain-track-empty">当前范围无该域记录</span> : null}
                  {lane.marks.map((mark) => {
                    const event = mark.event;
                    const selected = event.eventRef === selectedRef || (selectedRiskAnchorRef && event.riskAnchorRefs?.includes(selectedRiskAnchorRef));
                    const marker = journeyMarkerFor(event.eventRef);
                    const riskInfo = riskSeverityInfo(event.risk);
                    const riskLabel = riskInfo
                      ? `${DOMAIN_LABELS[event.domain] || event.domainEncoding.shortLabel}·${riskInfo.label}`
                      : "";
                    // W05-J2：窗外方向（before/after）以继续符号呈现，
                    // title与aria携带原始日期与方向——窗外事件不伪装同日。
                    const beyondCopy = mark.beyondStart === "before"
                      ? "开始于时间窗之前"
                      : mark.beyondEnd === "after"
                        ? "持续到时间窗之后"
                        : mark.beyond === "before"
                          ? "发生于时间窗之前"
                          : mark.beyond === "after"
                            ? "发生于时间窗之后"
                            : "";
                    const detailText = event.dateState === "exact" ? text(event.start, "实际日期待确认") : event.dateLabel;
                    const openEnd = mark.geometry === "ongoing" || mark.geometry === "end_unknown";
                    const commonProps = {
                      type: "button",
                      className: `monitoring-track-event monitoring-track-event-${mark.geometry}${mark.width > 0 ? " monitoring-track-event-span" : ""}${openEnd ? " monitoring-track-event-open-end" : ""}${mark.beyondStart || mark.beyondEnd || mark.beyond ? " monitoring-track-event-beyond" : ""}${mark.x > layout.scale.width - 170 ? " is-near-end" : ""}${selected ? " is-selected" : ""}${riskInfo ? ` has-risk monitoring-track-risk-${riskInfo.css}` : ""}`,
                      "data-event-ref": event.eventRef,
                      "data-timeline-geometry": mark.geometry,
                      "data-stack-row": mark.stackRow,
                      "data-finding-beyond": mark.beyondStart || mark.beyondEnd || mark.beyond || "",
                      "aria-label": `${DOMAIN_LABELS[event.domain] || event.domainEncoding.shortLabel}：${event.eventLabel}${beyondCopy ? `，${beyondCopy}` : ""}${riskInfo ? `，${riskInfo.label}` : ""}${marker ? `，本轮变化：${marker.changeText}${marker.countSuffix}` : ""}`,
                      onClick: () => onEventSelect?.(event),
                      onKeyDown: focusAdjacentTimelineEvent,
                      title: `${event.eventLabel}${beyondCopy ? `（${beyondCopy}：${event.start || ""}）` : ""} · ${detailText}${event.end && event.end !== event.start ? ` — ${event.end}` : ""}`,
                    };
                    // W05-J2 A22：interval/ongoing/end_unknown/月精度都以
                    // 条形（宽度>0）呈现；ongoing/end_unknown附加开-end视觉。
                    if (mark.width > 0) {
                      return (
                        <button
                          key={event.eventRef}
                          {...commonProps}
                          style={{ left: `${mark.x}px`, width: `${mark.width}px`, top: `${8 + (mark.stackRow + eventRowOffset) * 22}px` }}
                        >
                          <DomainIcon domain={event.domain} encoding={event.domainEncoding} size="track" title={DOMAIN_LABELS[event.domain] || event.domainEncoding.shortLabel} />
                          {riskInfo ? <span className={`monitoring-compact-risk-label monitoring-track-risk-${riskInfo.css}`}>{riskInfo.chip}</span> : null}
                          <span className="monitoring-track-event-title">{riskInfo && <span className={`monitoring-track-risk monitoring-track-risk-${riskInfo.css}`}>{riskLabel}</span>}{event.eventLabel}</span>
                          {marker ? <MonitoringJourneyChangeMarker marker={marker} /> : null}
                          <small className="monitoring-track-event-detail">{beyondCopy ? `${beyondCopy} · ` : ""}{text(event.start)} — {text(event.end)}</small>
                          <small className="monitoring-track-event-source">来源定位：{event.sourceLocatorRefs.length ? `已定位到 ${event.sourceLocatorRefs.length} 条原始记录` : "待确认"}</small>
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
                        {riskInfo ? <span className={`monitoring-compact-risk-label monitoring-track-risk-${riskInfo.css}`}>{riskInfo.chip}</span> : null}
                        <span className="monitoring-track-event-title">{riskInfo && <span className={`monitoring-track-risk monitoring-track-risk-${riskInfo.css}`}>{riskLabel}</span>}{detailDensity === "detailed" ? event.eventLabel : ""}</span>
                        {marker ? <MonitoringJourneyChangeMarker marker={marker} /> : null}
                        <small className="monitoring-track-event-detail">{beyondCopy ? `${beyondCopy} · ` : ""}{detailText}</small>
                        <small className="monitoring-track-event-source">来源定位：{event.sourceLocatorRefs.length ? `已定位到 ${event.sourceLocatorRefs.length} 条原始记录` : "待确认"}</small>
                      </button>
                    );
                  })}
                  {lane.aggregates.map((aggregate) => {
                    // R24V2-U04/U14：聚合是显示组织不是黑箱——toggle用
                    // React state展开成员列表（就地可点/键盘可达）；选中
                    // 事件在本聚合内时自动展开。
                    const containsSelected = aggregate.eventRefs.includes(selectedRef);
                    const expanded =
                      expandedAggregates.has(aggregate.aggregateKey)
                      || (containsSelected && !collapsedAggregates.has(aggregate.aggregateKey));
                    return (
                      <span
                        className={`monitoring-domain-track-aggregate monitoring-timeline-aggregate${expanded ? " is-expanded" : ""}`}
                        data-aggregate-key={aggregate.aggregateKey}
                        key={aggregate.aggregateKey}
                        style={{ left: `${aggregate.x}px` }}
                      >
                        {expanded ? (
                          <span className="monitoring-aggregate-members" role="list" aria-label={`本组 ${aggregate.count} 条记录`}>
                            {aggregate.eventRefs.map((ref, memberIndex) => (
                              <button
                                key={ref}
                                type="button"
                                role="listitem"
                                className="monitoring-aggregate-member"
                                data-event-ref={ref}
                                aria-pressed={ref === selectedRef}
                                autoFocus={
                                  memberIndex === 0
                                  && aggregateUserToggleKey.current === aggregate.aggregateKey
                                }
                                onClick={() => onEventSelect?.({ event_ref: ref })}
                              >
                                {ref}
                              </button>
                            ))}
                            <button
                              type="button"
                              className="monitoring-aggregate-collapse"
                              aria-expanded="true"
                              aria-label={`收起本组 ${aggregate.count} 条记录`}
                              onClick={() => {
                                aggregateUserToggleKey.current = aggregate.aggregateKey;
                                setCollapsedAggregates((prev) => {
                                  const next = new Set(prev);
                                  next.add(aggregate.aggregateKey);
                                  return next;
                                });
                                setExpandedAggregates((prev) => {
                                  const next = new Set(prev);
                                  next.delete(aggregate.aggregateKey);
                                  return next;
                                });
                                requestAnimationFrame(() => {
                                  aggregateToggleRefs.current.get(aggregate.aggregateKey)?.focus?.();
                                  if (aggregateUserToggleKey.current === aggregate.aggregateKey) {
                                    aggregateUserToggleKey.current = null;
                                  }
                                });
                              }}
                            >
                              收起
                            </button>
                          </span>
                        ) : (
                          <button
                            type="button"
                            className="monitoring-aggregate-toggle"
                            aria-expanded={expanded}
                            aria-label={`展开本组 ${aggregate.count} 条记录`}
                            title={aggregate.label}
                            ref={(el) => {
                              if (el) aggregateToggleRefs.current.set(aggregate.aggregateKey, el);
                              else aggregateToggleRefs.current.delete(aggregate.aggregateKey);
                            }}
                            onClick={() => {
                              aggregateUserToggleKey.current = aggregate.aggregateKey;
                              setCollapsedAggregates((prev) => {
                                const next = new Set(prev);
                                next.delete(aggregate.aggregateKey);
                                return next;
                              });
                              setExpandedAggregates((prev) => {
                                const next = new Set(prev);
                                next.add(aggregate.aggregateKey);
                                return next;
                              });
                              requestAnimationFrame(() => {
                                if (aggregateUserToggleKey.current === aggregate.aggregateKey) {
                                  aggregateUserToggleKey.current = null;
                                }
                              });
                            }}
                          >
                            {`另有 ${aggregate.count} 条`}
                          </button>
                        )}
                      </span>
                    );
                  })}
                </div>
              </article>
              );
            })}
          </div>
        </div>
        </div>
      </TimelineScrollShell>
      <div className="monitoring-pending-date-zone" aria-label="日期待确认记录">
        <div className="monitoring-section-heading">
          <span className="monitoring-eyebrow">暂不定位到时间轴</span>
          <h2>日期待确认记录</h2>
        </div>
        {!layout.pendingEvents.length && !layout.pendingVisits.length && !(layout.pendingDates || []).length ? (
          <p className="monitoring-domain-track-empty">当前范围无日期缺失记录。</p>
        ) : null}
        {layout.pendingEvents.map((event) => {
          const marker = journeyMarkerFor(event.eventRef);
          return (
          <button
            type="button"
            className={`monitoring-pending-date${event.eventRef === selectedRef ? " is-selected" : ""}`}
            data-event-ref={event.eventRef}
            data-timeline-geometry="pending"
            key={event.eventRef}
            onClick={() => onEventSelect?.(event)}
          >
            <DomainIcon domain={event.domain} size="summary" />
            <span>{DATE_STATE_LABELS[event.dateState] || "日期待确认"}</span>
            <strong>{DOMAIN_LABELS[event.domain] || event.domainEncoding?.shortLabel || "其他事件"} · {event.eventLabel}</strong>
            <small>不确定访视归属；未按实际日期吸附到共享时间轴，单独列示</small>
            {timelineDatePrecision(event.start || event.start_date) === "month" ? (
              <small className="monitoring-pending-precision" data-date-precision="month">月精度：{event.start}（YYYY-MM，不以01日为实际日）</small>
            ) : null}
            {event.risk ? <span className={`monitoring-track-risk monitoring-track-risk-${event.risk.severity}`}>{riskSeverityLabel(event.risk.severity)}</span> : null}
            {marker ? <MonitoringJourneyChangeMarker marker={marker} /> : null}
            {marker ? <span className="monitoring-journey-sr-only">，本轮变化：{marker.changeText}{marker.countSuffix}</span> : null}
          </button>
          );
        })}
        {layout.pendingVisits.map((visit) => (
          <div className="monitoring-pending-date" data-visit-ref={visit.visit_ref || visit.visitRef} key={visit.visit_ref || visit.visitRef}>
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
            <div className="monitoring-pending-date" key={ref}>
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
    <div className="monitoring-identity-strip" aria-label="当前数据范围">
      <div data-monitoring-identity-field="project_ref"><span>项目</span><strong>{projectDisplay}</strong><small>当前医学监查范围</small></div>
      <div data-monitoring-identity-field="run_ref"><span>分析批次</span><strong>{analysisBatchLabel(identity.run_ref || identity.runRef)}</strong></div>
      <div data-monitoring-identity-field="snapshot_ref"><span>数据版本</span><strong>{dataVersionLabel(identity.snapshot_ref || identity.snapshotRef)}</strong></div>
      <div data-monitoring-identity-field="cutoff_ref"><span>数据截止</span><strong>{(identity.cutoff_state || identity.cutoffState) === "absent" ? "截止时间待确认" : text(identity.cutoff_ref || identity.cutoffRef, "截止时间待确认")}</strong></div>
    </div>
  );
}

function RiskBadge({ risk }) {
  const encoding = risk?.domainEncoding;
  return (
    <span className="monitoring-risk-badge" data-severity={risk?.severity || "unknown"}>
      {encoding ? (
        <DomainIcon domain={encoding.domain} encoding={encoding} size="badge" title={DOMAIN_LABELS[encoding.domain] || encoding.shortLabel} />
      ) : <span className="monitoring-risk-unresolved">域待确认</span>}
      <span className="monitoring-risk-overlay">{text(DOMAIN_LABELS[encoding?.domain] || encoding?.shortLabel, "域待确认")}·{text(risk?.severityLabel, "等级待确认")}风险</span>
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
      className={`monitoring-risk-row ${risk.riskStatus === "unresolved" ? "is-unresolved" : ""}`}
      data-risk-instance-ref={risk.riskInstanceRef}
      disabled={risk.riskStatus === "unresolved"}
      onClick={() => risk.riskStatus !== "unresolved" && onSelect?.(risk)}
    >
      <RiskBadge risk={risk} />
      <span className="monitoring-risk-copy">
        <strong>{risk.riskType}</strong>
        <small>
          {metaParts.join(" · ")}
          {!omitChangeClaims && risk.changeCauseLabel ? ` · 变化原因：${risk.changeCauseLabel}` : ""}
        </small>
      </span>
      {marker ? (
        <span className="monitoring-risk-tail">
          <MonitoringJourneyChangeMarker marker={marker} />
          <span className="monitoring-journey-sr-only">，本轮变化：{marker.changeText}{marker.countSuffix}</span>
        </span>
      ) : omitChangeClaims ? null : <span className="monitoring-change-label">{risk.changeLabel}</span>}
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
    for (const row of listRef.current?.querySelectorAll("button.monitoring-risk-row") || []) {
      const selected = row.dataset.riskInstanceRef === selectedRiskInstanceRef;
      row.classList.toggle("is-selected", selected);
      row.setAttribute("aria-selected", String(selected));
    }
  }, [selectedRiskInstanceRef, rows]);
  if (!risks.length) return <div className="monitoring-empty-inline">{emptyText}</div>;
  return <div className="monitoring-risk-list" role="listbox" aria-label="当前风险" ref={listRef}>{rows}</div>;
}

function CenterTable({ centers, onSelect }) {
  if (!centers.length) return <div className="monitoring-empty-inline">中心覆盖范围待确认。</div>;
  return (
    <div className="monitoring-center-table" role="table" aria-label="中心覆盖与风险模式">
      <div className="monitoring-center-row monitoring-center-head" role="row">
        <span>中心</span><span>风险数 / 记录数</span><span>数据完整性</span><span>统计单位</span>
      </div>
      {centers.map((center, index) => {
        const measure = center.measures[0] || {};
        return (
          <button type="button" className="monitoring-center-row" role="row" key={center.siteRef} onClick={() => onSelect?.(center)}>
            <strong>{center.siteLabel || `中心 ${index + 1}`}</strong>
            <span className="monitoring-center-pattern">{measure.denominator ? `${numberText(measure.numerator)} / ${numberText(measure.denominator)}` : "暂无法计算"}</span>
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
        el.style.removeProperty("--monitoring-edge-clip");
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
      el.style.setProperty("--monitoring-edge-clip", `${edgeClip}px`);
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
  const wrapId = "monitoring-flow-table-scroll-pane";
  const seekFromEvent = (event) => {
    const track = event.currentTarget;
    const rect = track.getBoundingClientRect();
    if (rect.width <= 0) return;
    scrollToRatio((event.clientX - rect.left) / rect.width);
  };
  return (
    <div className={`monitoring-flow-table-scroll${overflow ? " is-overflow" : ""}`} data-monitoring-table-scroll={overflow ? "overflow" : "fit"}>
      {overflow ? (
        <p className="monitoring-flow-table-scroll-cue" data-monitoring-table-scroll-cue="true" id="monitoring-flow-table-scroll-cue">
          左右滑动查看完整明细（含数据完整性、医学旅程）
        </p>
      ) : null}
      <div className="monitoring-flow-table-wrap" id={wrapId} ref={ref}>{children}</div>
      {overflow ? (
        <div
          className="monitoring-flow-table-hrail"
          data-monitoring-table-hrail="true"
          role="scrollbar"
          aria-orientation="horizontal"
          aria-controls={wrapId}
          aria-valuemin={0}
          aria-valuemax={100}
          aria-valuenow={Math.round(thumb.start + thumb.size / 2)}
          aria-label="左右滑动查看完整明细"
          aria-describedby="monitoring-flow-table-scroll-cue"
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
          <div className="monitoring-flow-table-hrail-track">
            <div className="monitoring-flow-table-hrail-thumb" style={{ width: `${thumb.size}%`, left: `${thumb.start}%` }} />
          </div>
        </div>
      ) : null}
    </div>
  );
}

function TimelineScrollShell({ children }) {
  const { ref, overflow, thumb, scrollToRatio } = useScrollMetrics("y");
  const paneId = "monitoring-timeline-scroll-pane";
  const seekFromEvent = (event) => {
    const track = event.currentTarget;
    const rect = track.getBoundingClientRect();
    if (rect.height <= 0) return;
    scrollToRatio((event.clientY - rect.top) / rect.height);
  };
  return (
    <div className={`monitoring-timeline-scroll-shell${overflow ? " is-overflow-y" : ""}`} data-monitoring-timeline-scroll={overflow ? "overflow" : "fit"}>
      <div className="monitoring-timeline-scroll" id={paneId} ref={ref}>{children}</div>
      {overflow ? (
        <div
          className="monitoring-timeline-vrail"
          data-monitoring-timeline-vrail="true"
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
          <div className="monitoring-timeline-vrail-track">
            <div className="monitoring-timeline-vrail-thumb" style={{ height: `${thumb.size}%`, top: `${thumb.start}%` }} />
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
      className="monitoring-panel monitoring-flow-section"
      data-monitoring-flow-state={flow.state}
      data-monitoring-flow-scope="true"
      aria-label="受试者阶段流向"
      onKeyDown={handleFlowKeyDown}
    >
      <div className="monitoring-section-heading"><span className="monitoring-eyebrow">受试者阶段流向</span><h2>阶段流向总览</h2></div>
      <p className="monitoring-flow-note">连线表示截至本次截止点的规范阶段路径；节点同时显示累计到达人数和当前停留人数。退回或重新筛选情况见阶段较上次。</p>
      {flow.state === "not_provided" && (
        <div className="monitoring-flow-notice" role="status">
          <strong>本次数据未提供研究状态</strong>
          {flow.notice && flow.notice !== "本次数据未提供研究状态" ? <span>{flow.notice}</span> : null}
        </div>
      )}
      {flow.state === "blocked" && (
        <div className="monitoring-flow-notice is-blocked" role="alert">
          <strong>阶段人数暂无法核对，请检查本次数据范围</strong>
          {flow.gap ? <span>{flow.gap}</span> : null}
        </div>
      )}
      {flow.state === "empty" && (
        <div className="monitoring-flow-notice" role="status">
          <strong>当前项目/中心在本次截止点暂无受试者</strong>
        </div>
      )}
      {flow.state === "ready" && graph && (
        <>
          <div className="monitoring-flow-controls">
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
            {subjectFlowHasSelection(selection) && <button type="button" className="monitoring-flow-clear" onClick={() => onClear?.()}>清除筛选</button>}
            {summaryLine && <span className="monitoring-flow-filter-hint">{summaryLine}</span>}
          </div>
          <KzSubjectFlowSankey
            flow={flow}
            selection={selection}
            onStageSelect={onStageSelect}
            onLinkSelect={onLinkSelect}
          />
          <ul className="monitoring-flow-a11y-list">
            {graph.nodes.map((node) => (
              <li key={node.ref}>
                <button
                  type="button"
                  data-flow-node={node.ref}
                  onClick={() => onStageSelect?.(node.ref, "current")}
                >{`${node.label}：到达 ${node.reached} 人，当前 ${node.current} 人，中高风险 ${node.risk} 人`}</button>
              </li>
            ))}
            {graph.ribbons.map((ribbon) => (
              <li key={ribbon.ref}>
                <button
                  type="button"
                  data-flow-link={ribbon.ref}
                  onClick={() => onLinkSelect?.(ribbon.ref)}
                >{`从${ribbon.fromLabel}到${ribbon.toLabel}：${ribbon.count} 人，中高风险 ${ribbon.risk} 人`}</button>
              </li>
            ))}
          </ul>
          {!hideIncremental ? (
            <p className="monitoring-flow-risk-summary" data-monitoring-flow-risk-summary="true">
              <strong>中高风险变化摘要</strong>
              <span>{`新增 ${flow.riskChanges.new} · 升级 ${flow.riskChanges.upgraded} · 持续 ${flow.riskChanges.continued}`}</span>
            </p>
          ) : null}
          <p className="monitoring-flow-scope-bar">
            <strong>{`范围受试者 ${flow.total} 人`}</strong>
            {flow.coverageList
              // When every subject is already “齐备”, the chip restates the total — drop it.
              .filter((item) => !(item.key === "complete" && item.count === flow.total))
              .map((item) => <span key={item.key}>{`${item.label} ${item.count}`}</span>)}
            <small>当前项目/中心整体范围</small>
          </p>
          <div className="monitoring-flow-table" data-monitoring-flow-table="true">
            <div className="monitoring-flow-table-summary">
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
                            <span className={`monitoring-date-chip monitoring-date-${row.dateState}`}>{DATE_STATE_CHIPS[row.dateState] || "日期待核实"}</span>
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
                              className="monitoring-flow-jump-button"
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

export function OverviewView({
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
  onOpenQueries,
  suppressVersionClaim = false,
  flowTableOpen = true,
  continuityCounts = null,
  continuityComparisonText = "",
  continuityLoading = false,
}) {
  const projection = payload.projection;
  const flow = normalizeSubjectFlowView(projection);
  const flowSelection = subjectFlowSelectionFromRoute(route);
  const risks = [...projection.currentRisks].sort(riskSort);
  const queryRiskCount = risks.filter((risk) => !risk.aggregate && ["critical", "high", "medium"].includes(risk.severity)).length;
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
  // on public result envelopes (*_snapshot_ref), so incremental pages must not depend on it.
  // The note follows the actual comparison evidence: counts that prove prior-state
  // transitions mean "compared"; when the counts record cannot prove a baseline either
  // way (first analysis vs. zero-change round), the note stays neutral instead of guessing.
  const comparisonState = monitoringComparisonState({ continuityCounts, changes, comparisonText: continuityComparisonText, loading: continuityLoading });
  const compared = comparisonState.state === MONITORING_COMPARISON_STATE_COMPARED;
  const comparable = compared
    && (comparisonState.basis === "continuity"
      || !changes.every((item) => item.change_kind === "not_comparable"));
  const comparisonUncertain = comparisonState.state === MONITORING_COMPARISON_STATE_UNCERTAIN;
  const scopedCenter = payload.identity?.site_ref ? projection.centers.find((center) => center.siteRef === payload.identity.site_ref) : null;
  const scopedMeasure = scopedCenter?.measures?.[0] || null;
  const scopedAffectedSubjects = new Set((scopedCenter?.risks || []).map((risk) => risk.subjectRef).filter(Boolean)).size;
  const scopedEventCount = (scopedCenter?.risks || []).length;
  const showContinuityKpis = compared && comparisonState.basis === "continuity" && !suppressVersionClaim;
  return (
    <div className="monitoring-view-stack">
      {!suppressVersionClaim ? (
        <section className="monitoring-comparison-note" data-comparable={comparable ? "yes" : compared ? "no" : comparisonUncertain ? "unknown" : "initial"}>
          <strong>{comparable ? "已与上次监查结果比较" : compared ? "本次暂不作增减比较" : comparisonUncertain ? (continuityLoading ? "正在读取本轮比较结果…" : "本轮比较状态暂无法判断") : "当前为首个监查版本"}</strong>
          <span>{comparable ? "变化类别与原因已逐项标示。" : compared ? "前后数据覆盖范围不一致，以下仅展示当前风险。" : comparisonUncertain ? (continuityLoading ? "当前风险可先查看，比较结果稍后显示。" : "暂无法确认本轮是否已与上次监查结果比较；变化明细以下方“本轮变化”为准。") : "以下展示当前全部中高风险，后续版本将保留增量变化。"}</span>
        </section>
      ) : null}
      {showContinuityKpis ? (
        <section className="monitoring-summary-grid monitoring-summary-grid-continuity" data-monitoring-continuity-kpis="true" aria-label="本轮变化关键计数">
          {keyCountItems.map((item) => (
            <article key={item.key} className={`monitoring-stat-card${item.key === "mid_high_total" ? " monitoring-stat-danger" : ""}`}>
              <span>{item.label}</span>
              <strong data-count-key={item.key}>{numberText(continuityCounts[item.key], "0")}</strong>
              <small>本轮范围</small>
            </article>
          ))}
        </section>
      ) : suppressVersionClaim ? null : (
        <section className="monitoring-summary-grid">
          <article className="monitoring-stat-card monitoring-stat-danger"><span>高风险</span><strong>{numberText(currentCounts.high)}</strong><small>{scopedCenter?.coverageState === "small_sample" ? "当前中心计数；比例暂不评价" : "当前范围"}</small></article>
          <article className="monitoring-stat-card monitoring-stat-warning"><span>中风险</span><strong>{numberText(currentCounts.medium)}</strong><small>{scopedCenter?.coverageState === "small_sample" ? "当前中心计数；比例暂不评价" : "当前范围"}</small></article>
          <article className="monitoring-stat-card"><span>覆盖情况</span><strong>{projection.coverage?.denominator ? `${numberText(projection.coverage?.numerator)} / ${numberText(projection.coverage?.denominator)}` : "暂无法计算"}</strong><small>{projection.coverage?.denominator ? text(projection.coverage?.label, projection.coverage?.coverage_state || "覆盖待确认") : "样本量较小，暂不评价"}</small></article>
          <article className="monitoring-stat-card"><span>{compared && !comparable ? "当前风险总数" : "变化摘要"}</span><strong>{numberText(compared && !comparable ? currentCounts.total : payload.counts?.changeBand)}</strong><small>{scopedCenter?.coverageState === "small_sample" ? "当前中心计数；比例暂不评价" : compared && !comparable ? "本次不作增减比较" : "本次范围变化"}</small></article>
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

      <div className="monitoring-overview-columns">
        <section className="monitoring-panel monitoring-panel-wide">
          <div className="monitoring-section-heading"><span className="monitoring-eyebrow">当前风险</span><h2>高、中风险定位</h2></div>
              <RiskList
                risks={risks.filter((risk) => !risk.aggregate && ["critical", "high", "medium"].includes(risk.severity))}
            onSelect={onRiskSelect}
            selectedRiskInstanceRef={selectedRiskInstanceRef}
            omitChangeClaims={suppressVersionClaim}
          />
        </section>
        <section className="monitoring-panel">
          {selectedRisk ? (
            <div className="monitoring-overview-inspector">
              <div className="monitoring-section-heading"><span className="monitoring-eyebrow">风险证据</span><h2>{selectedRisk.riskType}</h2></div>
              <RiskBadge risk={selectedRisk} />
              <dl>
                <div><dt>受试者</dt><dd>{text(selectedRisk.subjectLabel, "待确认")}</dd></div>
                <div><dt>日期</dt><dd>{selectedRisk.dateLabel}</dd></div>
                {!suppressVersionClaim ? <div><dt>本次变化</dt><dd>{selectedRisk.changeLabel}</dd></div> : null}
                {!suppressVersionClaim ? <div><dt>变化原因</dt><dd>{selectedRisk.changeCauseLabel}</dd></div> : null}
              </dl>
              {selectedRisk.evidenceSummary && (
                <div className="monitoring-evidence-summary">
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
                <div className="monitoring-disagreement" aria-label="分析分歧">
                  <h3>分歧内容</h3><p>{selectedRisk.analysisDisagreement.disagreement}</p>
                  <div><strong>分析一</strong><span>{selectedRisk.analysisDisagreement.analysis_one}</span></div>
                  <div><strong>分析二</strong><span>{selectedRisk.analysisDisagreement.analysis_two}</span></div>
                  <div><strong>独立核对</strong><span>{selectedRisk.analysisDisagreement.independent_check}</span></div>
                  <p><strong>支持证据：</strong>{selectedRisk.analysisDisagreement.supporting_evidence}</p>
                  <p><strong>不支持证据：</strong>{selectedRisk.analysisDisagreement.counter_evidence}</p>
                  <p className="monitoring-disagreement-status">{selectedRisk.analysisDisagreement.status_zh}</p>
                </div>
              )}
              <button type="button" className="monitoring-source-button" onClick={() => onRiskSelect?.(selectedRisk)}>进入受试者医学旅程</button>
              <button type="button" className="monitoring-back-button" disabled={!selectedRisk.sourceLocatorRef} onClick={() => onSource?.(selectedRisk)}>查看原始来源</button>
            </div>
          ) : (
            <>
              <div className="monitoring-section-heading"><span className="monitoring-eyebrow">受试者入口</span><h2>查看受试者医学旅程</h2></div>
              <div className="monitoring-subject-list">
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
        <section className="monitoring-panel monitoring-center-summary" aria-label="中心模式与计算口径">
          <div className="monitoring-section-heading"><span className="monitoring-eyebrow">中心风险图谱</span><h2>{text(scopedCenter.siteLabel, centerLabel(scopedCenter.siteRef, "当前中心"))}</h2></div>
          <div className="monitoring-center-summary-grid">
            <div><span>重复模式</span><strong>{scopedMeasure?.denominator ? `${DOMAIN_LABELS[scopedCenter.domain] || "相关"}记录需关注` : "样本量不足，暂无法评价重复模式"}</strong></div>
            <div><span>受影响受试者</span><strong>{numberText(scopedAffectedSubjects, "0")}</strong></div>
            <div><span>风险提示数</span><strong>{numberText(scopedEventCount, "0")}</strong></div>
            <div><span>分子</span><strong>{scopedMeasure?.denominator ? numberText(scopedMeasure.numerator) : "暂无法计算"}</strong></div>
            <div><span>分母</span><strong>{scopedMeasure?.denominator ? numberText(scopedMeasure.denominator) : "暂无法计算"}</strong></div>
            <div><span>覆盖情况</span><strong>{text(scopedCenter.coverageLabel, "覆盖待确认")}</strong></div>
          </div>
          {!scopedMeasure?.denominator && <p className="monitoring-center-explanation"><strong>原因：</strong>当前中心没有可用于计算比例的有效分母，样本量较小，暂不评价中心重复模式。</p>}
        </section>
      )}

      {projection.aggregation?.mode === "aggregate" && projection.currentRisks.some((risk) => risk.aggregate) ? (
        <section className="monitoring-panel monitoring-panel-wide">
          <div className="monitoring-section-heading">
            <span className="monitoring-eyebrow">全量风险分布</span>
            <h2>风险类型 × 严重度（全量 {numberText(projection.aggregation.risk_count)} 条锚点）</h2>
            {onOpenQueries ? <button type="button" className="monitoring-product-button is-primary monitoring-query-entry" onClick={onOpenQueries}>查询工作区：{queryRiskCount} 项待核实</button> : null}
          </div>
          <KzRiskTypeBars rows={projection.currentRisks} height={340} />
        </section>
      ) : null}

      <section className="monitoring-panel monitoring-center-overview-panel">
        <div className="monitoring-section-heading"><span className="monitoring-eyebrow">中心概览</span><h2>中心风险与数据覆盖</h2></div>
        {projection.centers.some((center) => center.riskCount !== undefined) ? (
          <KzCenterDomainHeatmap
            cells={projection.centers.filter((center) => center.domain)}
            domains={projection.domains}
            height={560}
          />
        ) : null}
        <CenterTable centers={projection.centers} onSelect={onCenterSelect} />
      </section>
      <DomainLegend domains={projection.domains} />
    </div>
  );
}

const EventRow = memo(function EventRow({ event, onSelect, marker = null }) {
  const select = (pointerEvent) => {
    for (const row of pointerEvent.currentTarget.parentElement?.querySelectorAll("button.monitoring-event-row") || []) row.classList.remove("is-selected");
    pointerEvent.currentTarget.classList.add("is-selected");
    onSelect?.(event);
  };
  return (
    <button type="button" className="monitoring-event-row" data-event-ref={event.eventRef} onClick={select}>
      <DomainIcon domain={event.domain} encoding={event.domainEncoding} size="row" title={DOMAIN_LABELS[event.domain] || event.domainEncoding.shortLabel} />
      <span className="monitoring-event-main"><strong><span className={`monitoring-date-chip monitoring-date-${event.dateState}`}>{DATE_STATE_CHIPS[event.dateState] || "日期待核实"}</span>{event.eventLabel}</strong><small>{event.dateLabel} · {text(event.start, "日期待确认")}{event.end ? ` — ${event.end}` : ""}</small></span>
      {event.risk && <span className={`monitoring-event-risk-count monitoring-track-risk-${event.risk.severity}`}>{DOMAIN_LABELS[event.domain] || event.domainEncoding.shortLabel}·{riskSeverityLabel(event.risk.severity)}</span>}
      {marker ? <MonitoringJourneyChangeMarker marker={marker} /> : null}
      {marker ? <span className="monitoring-journey-sr-only">，本轮变化：{marker.changeText}{marker.countSuffix}</span> : null}
    </button>
  );
});

function EventDetailPanel({ event }) {
  if (!event) return null;
  return (
    <div className="monitoring-inspector-card" data-event-detail={event.eventRef}>
      <span className="monitoring-eyebrow">事件详情</span>
      <span className={`monitoring-date-chip monitoring-date-${event.dateState}`}>{DATE_STATE_CHIPS[event.dateState] || "日期待核实"}</span>
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

export function SubjectWorkspaceView({
  payload,
  route,
  view,
  timeViewport = "fit",
  detailDensity = "standard",
  timeZoom = 0,
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
  const trendView = monitoringTrendScaleView(indicators?.[trendIndicator] || null);
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

  // Result-context gating: the change markers and the detail
  // drawer are enabled only on product routes with a result_context_token;
  // setup preview keeps the existing inline inspector untouched.
  const journeyEnabled = payload?.publicResultContext === true && Boolean(route.result_context_token);
  const journeyRows = journeyEnabled
    ? monitoringJourneyContinuityRows(continuityResult, payload, route)
    : [];
  const journeyBinding = journeyEnabled
    ? bindMonitoringContinuityRowsToJourney(journeyRows, projection.events || [], projection.currentRisks || [])
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
    for (const [eventRef, rows] of rowsByEventRef.entries()) markersByEventRef.set(eventRef, monitoringEventChangeMarker(rows));
    for (const [instance, rows] of rowsByRiskInstance.entries()) markersByRiskInstance.set(instance, monitoringEventChangeMarker(rows));
  }
  const journeyComparison = journeyEnabled && continuityResult?.ok
    ? continuityResult.value?.comparison || null
    : null;
  const journeyTruncationText = journeyEnabled ? monitoringJourneyTruncationText(journeyComparison) : "";
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
    || (drawerRows.length ? monitoringJourneyDrawerCurrentRow(drawerRows, route) : null);
  const drawerRowIndex = drawerRow ? drawerRows.findIndex((row) => row.row_ref === drawerRow.row_ref) : -1;
  const drawerRisk = drawerRow
    ? projection.currentRisks.find((risk) => text(risk.riskInstanceRef) === text(drawerRow.risk_instance_ref)) || selectedRisk
    : selectedRisk;
  const drawerSections = drawerOpen
    ? monitoringJourneyDrawerSections({ event: enrichedSelectedEvent, risk: drawerRisk, currentRow: drawerRow, comparison: journeyComparison, domainLabels: DOMAIN_LABELS })
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
  const drawerMode = monitoringJourneyDrawerLayoutMode({ viewportWidth: drawerViewport, hostContentWidth: drawerHostWidth });
  const openSource = (risk) => {
    if (risk) onSource?.(risk);
  };
  return (
    <div className="monitoring-view-stack">
      <section className="monitoring-subject-banner">
        <div><span className="monitoring-eyebrow">受试者医学旅程</span><h2>{subjectLabel}</h2></div>
        <div className="monitoring-subject-meta"><span>{centerLabel(projection.raw.subject?.site_ref)}</span><span>{text(projection.temporalSpine.axisMode, "calendar") === "study_day" ? "研究日" : "日历日期"}</span></div>
      </section>
      <nav className="monitoring-workspace-tabs" aria-label="受试者工作区视图">
        {SUBJECT_VIEW_KEYS.map((key) => <button type="button" key={key} className={view === key ? "is-active" : ""} onClick={() => selectWorkspaceRisk({ __view: key })}>{SUBJECT_VIEW_LABELS[key]}</button>)}
      </nav>
      <div className={`monitoring-subject-columns${drawerOpen && drawerMode === "push" ? " is-monitoring-drawer-push" : ""}`} ref={subjectColumnsRef}>
        <section className="monitoring-panel monitoring-panel-wide">
          {view === "profile" ? indicators?.length ? (
            <section className="monitoring-indicator-panel" aria-label="指标趋势">
              <div className="monitoring-axis-heading monitoring-trend-window"><div><span className="monitoring-eyebrow">共享时间轴</span><h2 id={journeyEnabled ? MONITORING_JOURNEY_AXIS_TITLE_ID : undefined} tabIndex={journeyEnabled ? -1 : undefined}>{text(projection.temporalSpine.axisMode, "calendar") === "study_day" ? "研究日" : "日历日期"}</h2></div><span className="monitoring-axis-window">{text(projection.temporalSpine.windowStart, "起点待确认")} — {text(projection.temporalSpine.windowEnd, "终点待确认")}</span></div>
              <div className="monitoring-section-heading"><span className="monitoring-eyebrow">指标趋势</span><h2>{text(indicators[trendIndicator]?.label, "指标待确认")}{trendView.unit ? `（单位：${trendView.unit}）` : ""}</h2></div>
              <div className="monitoring-indicator-switcher">{indicators.map((indicator, index) => <button type="button" key={indicator.indicator_ref || indicator.label} className={index === trendIndicator ? "is-active" : ""} onClick={() => setTrendIndicator(index)}>{indicator.label}</button>)}</div>
              <div
                className="monitoring-trend-chart"
                role="img"
                aria-label={trendView.mode === MONITORING_TREND_MODE_BARS
                  ? `指标趋势图：真实数值标尺 0 至 ${trendView.max}${trendView.unit ? `（${trendView.unit}）` : ""}，柱高按数值等比绘制，缺数值不画柱`
                  : "指标趋势数值列表：该指标数值无法共用同一真实标尺，仅逐点列出原始数值"}
              >
                {trendView.items.map((item) => (
                  <div className="monitoring-trend-point" key={`${item.index}-${item.date}`}>
                    <div style={{ height: 140, width: 28, display: "flex", alignItems: "end", flexShrink: 0 }}>
                      {trendView.mode === MONITORING_TREND_MODE_BARS && item.value !== null ? (
                        <span style={{ "--point-height": `${item.heightPercent}%`, minHeight: 0, flexShrink: 0 }} />
                      ) : null}
                    </div>
                    <strong>{numberText(item.displayValue)}{item.unit ? ` ${item.unit}` : ""}</strong>
                    <small>{text(item.date, "日期待确认")}</small>
                  </div>
                ))}
              </div>
              {trendView.mode === MONITORING_TREND_MODE_BARS ? (
                <p className="monitoring-trend-scale-note">标尺 0 — {trendView.max}{trendView.unit ? `（${trendView.unit}）` : ""}；柱高按真实数值等比绘制，缺数值不画柱。</p>
              ) : trendView.reason === "mixed_units" ? (
                <p className="monitoring-trend-scale-note">该指标各点单位不一致，不能合并到同一标尺，暂逐点列出数值；缺数值待确认。</p>
              ) : trendView.reason === "negative" ? (
                <p className="monitoring-trend-scale-note">该指标含负值，暂逐点列出原始数值。</p>
              ) : (
                <p className="monitoring-trend-scale-note">该指标暂无可绘制的数值，待数据补齐后按真实标尺绘制。</p>
              )}
            </section>
          ) : <div className="monitoring-empty-state">当前范围未提供指标趋势。</div>
          : (
            <DomainTracks
              projection={projection}
              timeViewport={timeViewport}
              detailDensity={detailDensity}
              timeZoom={timeZoom}
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
            <section className="monitoring-event-lane" aria-label="选中事件明细">
              <EventRow event={enrichedSelectedEvent} onSelect={selectWorkspaceEvent} marker={journeyEnabled ? markersByEventRef.get(enrichedSelectedEvent.eventRef) || null : null} />
            </section>
          )}
          {projection.aemhHistory?.length > 0 && (
            <section className="monitoring-history-panel"><div className="monitoring-section-heading"><span className="monitoring-eyebrow">AE/MH 前后记录</span><h2>漏报提示与补录匹配历史</h2></div>{projection.aemhHistory.map((item) => <div className="monitoring-history-detail" key={item.candidate_ref || item.item_ref}><div><span>原疑似漏报</span><strong>疑似 AE 漏报 / 疑似既往史未录入</strong></div><div><span>后续已补录记录</span><strong>{item.later_fact_ref ? "已发现对应补录记录" : "暂未发现"}</strong></div><div><span>匹配关系</span><strong>{HISTORY_LABELS[item.match_state] || "状态待确认"}</strong></div><p>匹配历史保留：原提示与后续记录均保留，便于复核前后变化。</p><p><strong>核查问题草稿：</strong>{selectedRisk?.evidenceSummary?.query_draft || "请核实原疑似漏报与后续记录是否为同一医学事件，并确认 AE/MH 记录是否完整。"}</p></div>)}</section>
          )}
        </section>
        <aside className="monitoring-panel monitoring-inspector" aria-label="风险定位">
          <div className="monitoring-section-heading"><span className="monitoring-eyebrow">风险定位</span><h2>检查依据</h2></div>
          <RiskList risks={inspectorRisks} onSelect={selectWorkspaceRisk} selectedRiskInstanceRef={selectedRisk?.riskInstanceRef} markersByRiskInstance={journeyEnabled ? Object.fromEntries(markersByRiskInstance.entries()) : null} />
          {priorityRisks.length > inspectorRisks.length && <p className="monitoring-event-lane-note">这里优先列出 16 项；其余 {priorityRisks.length - inspectorRisks.length} 项中高风险已在左侧八域泳道逐项呈现。</p>}
          {journeyEnabled ? (
            drawerOpen && drawerSections ? (
              <MedicalMonitoringJourneyDrawer
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
                <div className="monitoring-inspector-card">
                  <RiskBadge risk={selectedRisk} />
                  <h3>{selectedRisk.riskType}</h3>
                  <dl><div><dt>日期状态</dt><dd>{selectedRisk.dateLabel}</dd></div><div><dt>变化</dt><dd>{selectedRisk.changeLabel}</dd></div><div><dt>关联记录</dt><dd>{selectedRisk.riskType?.includes("AE/MH") ? "AE + MH" : text(selectedRisk.domainEncoding?.shortLabel, "待确认")}</dd></div></dl>
                  {selectedRisk.evidenceSummary && <div className="monitoring-query-draft"><strong>依据 / 发现 / 行动项</strong><p>{selectedRisk.evidenceSummary.query_draft}</p></div>}
                  <button type="button" className="monitoring-source-button" disabled={!selectedRisk.sourceLocatorRef} onClick={() => onSource?.(selectedRisk)}>查看来源证据</button>
                </div>
              )}
            </>
          )}
        </aside>
      </div>
    </div>
  );
}

export function EvidenceView({ payload, route, onBack }) {
  const publicResult = payload?.publicResultContext === true;
  const evidence = payload.projection.sourceEvidence || {};
  // R24-07：目标locator无法匹配时明确“不可定位”，绝不回退第一条来源
  // 冒充定位成功；只有精确匹配的sourceRef才参与展示兜底。
  const matchedRef = (payload.source_refs || []).find((item) => item.locator_ref === evidence.sourceLocatorRef);
  const sourceRef = matchedRef || {};
  const located = Boolean(matchedRef) || Boolean(evidence.canonical_location);
  const canonicalLocation = text(evidence.canonical_location || sourceRef.canonical_location, "当前定位无法确认");
  const recordRef = text(evidence.record_ref || sourceRef.record_ref, "记录号待确认");
  const excerpt = text(evidence.excerpt || sourceRef.excerpt, "来源片段暂不可读取。");
  const lineage = Array.isArray(evidence.lineage) && evidence.lineage.length ? evidence.lineage : sourceRef.lineage;
  return (
    <div className="monitoring-view-stack">
      <section className="monitoring-panel monitoring-evidence-panel">
        <div className="monitoring-section-heading"><span className="monitoring-eyebrow">风险证据</span><h2>{text(evidence.title, publicResult ? "本次结果来源定位" : "精确来源定位")}</h2></div>
        <div className="monitoring-evidence-locator" data-monitoring-evidence-field="canonical_location"><span>原始来源</span><strong title={canonicalLocation}>{canonicalLocation}</strong><small>{located ? "已定位到具体 listing 行或方案条款" : "未能精确匹配目标来源定位，请返回后重试或直接查看原始数据"}</small></div>
        <blockquote className="monitoring-evidence-excerpt" data-monitoring-evidence-field="excerpt"><span>原始引文</span><p>{excerpt}</p></blockquote>
        <dl className="monitoring-evidence-meta">
          <div data-monitoring-evidence-field="record_ref"><dt>记录号</dt><dd>{recordRef}</dd></div>
          <div data-monitoring-evidence-field="canonical_location"><dt>原始定位</dt><dd>{canonicalLocation}</dd></div>
          <div><dt>来源文件</dt><dd>{text(evidence.source_file_label || sourceRef.source_file_label, publicResult ? "本次结果来源" : "方案执行 Data Listing（合成验证）")}</dd></div>
          <div><dt>来源修订</dt><dd>{text(evidence.source_revision_label || sourceRef.source_revision_label, publicResult ? "本次数据范围" : "本次数据版本")}</dd></div>
          <div><dt>来源链路</dt><dd>{Array.isArray(lineage) && lineage.length ? lineage.join(" → ") : "来源链路待确认"}</dd></div>
          <div><dt>来源版本</dt><dd>{publicResult ? "本次公开结果" : dataVersionLabel(route.snapshot_ref)}</dd></div>
          <div><dt>风险时间窗</dt><dd>{route.window_start && route.window_end ? `${route.window_start} — ${route.window_end}` : "与当前风险 / 事件时间窗一致"}</dd></div>
          <div><dt>打开状态</dt><dd>{located ? "已完成来源一跳定位" : "来源定位未命中（未跳到其他来源冒充）"}</dd></div>
        </dl>
        <button type="button" className="monitoring-back-button" onClick={onBack}>返回受试者医学旅程</button>
      </section>
    </div>
  );
}

export function QueryWorkspaceView({ payload, route, onSubjectSelect, onSource, onFindingSelect, onBack }) {
  const projection = payload.projection;
  const subjectsByRef = new Map((projection.subjects || []).map((subject) => [subject.subject_ref || subject.subject_id, subject]));
  const risks = (projection.currentRisks || [])
    .filter((risk) => !risk.aggregate && ["critical", "high", "medium"].includes(risk.severity))
    .sort((left, right) => ["critical", "high", "medium"].indexOf(left.severity) - ["critical", "high", "medium"].indexOf(right.severity));
  const totalCount = projection.aggregation?.risk_count ?? risks.length;
  const aiFindings = Array.isArray(projection.aiQueryFindings) ? projection.aiQueryFindings : [];
  // W01-R26 A12：真实Finding卡——query_findings是Finding冻结DTO
  // （与QueryDraft分离），claim/source按分类与逐条入口渲染；旧形态
  // （legacy_query_drafts）如实按draft呈现并标注来源形态。
  const findingCards = Array.isArray(projection.findingCards) ? projection.findingCards : [];
  const queryFindingsMeta = projection.queryFindingsMeta || {};
  const queryDraftRows = Array.isArray(projection.queryDraftRows) ? projection.queryDraftRows : [];
  const legacyDraftRows = queryFindingsMeta.shape === "legacy_query_drafts" ? queryDraftRows : [];
  const FINDING_STATE_LABELS = { open: "待核实", confirmed: "已确认", closed: "已关闭" };
  const CLAIM_KIND_LABELS = { basis: "依据", finding: "发现", action: "行动项" };
  const aiAccepted = aiFindings.filter((item) => item.state === "accepted").length;
  const aiEscalated = aiFindings.filter((item) => item.state === "escalated").length;
  const aiGaps = aiFindings.filter((item) => item.state === "unverifiable_gap" || item.state === "coverage_gap").length;
  return (
    <div className="monitoring-view-stack monitoring-query-workspace" data-monitoring-query-count={risks.length}>
      {aiFindings.length ? (
        <section className="monitoring-panel monitoring-panel-wide">
          <div className="monitoring-section-heading"><span className="monitoring-eyebrow">双模型分析</span><h2>AI 跨表线索（{aiFindings.length} 条 · 双cohort一致 {aiAccepted} · 分歧 {aiEscalated} · 待补核 {aiGaps}）</h2></div>
          <p className="monitoring-query-intro">以下线索由主分析与独立盲核（双模型全量盲核对）产出；模型一致性是核验状态而非医学结论，最终判断由您对照原始记录作出。</p>
          <ul className="monitoring-query-card-list">
            {aiFindings.map((item) => {
              // N4：subject身份由服务端投影解析（subject_ref），不再按
              // subject-${label}猜ID；分页外受试者仍可按ref导航。
              const subject = (item.subject_ref && subjectsByRef.get(item.subject_ref))
                || (projection.subjects || []).find((row) => row.subject_label === item.subject_label)
                || (item.subject_ref ? { subject_ref: item.subject_ref, site_ref: item.site_ref, spine_ref: item.spine_ref } : null);
              const stateBadge = item.state === "accepted" ? "双cohort一致" : item.state === "escalated" ? "分歧待裁决" : "待补核";
              const claims = Array.isArray(item.claims) ? item.claims : [];
              const anchorEvent = Array.isArray(item.anchor_event_refs) && item.anchor_event_refs.length
                ? item.anchor_event_refs[0] : "";
              return (
                <li key={item.finding_id} className="monitoring-query-card" data-query-finding={item.finding_id} data-finding-state={item.state} data-finding-kind={item.kind || "finding"}>
                  <header className="monitoring-query-card-head">
                    <span className={`monitoring-query-state-chip monitoring-query-state-${item.state}`}>{stateBadge}</span>
                    <strong>{item.title}</strong>
                    <span className="monitoring-query-card-target">
                      受试者{" "}
                      {subject ? (
                        <button type="button" className="monitoring-subject-link" onClick={() => onSubjectSelect?.(subject)}>{item.subject_label || "查看"}</button>
                      ) : (
                        <span>{item.subject_label || "待确认"}</span>
                      )}
                    </span>
                  </header>
                  <div className="monitoring-query-card-body">
                    {claims.length ? (
                      <section aria-label="观察与依据"><h3>观察与依据</h3>
                        <ul className="monitoring-claim-list">
                          {claims.map((claim, claimIndex) => (
                            <li key={claimIndex} data-claim-kind={claim.kind || ""}>
                              {claim.text}
                              {claim.evidence_ids?.length ? (
                                <span className="monitoring-claim-evidence">（证据 {claim.evidence_ids.length} 条）</span>
                              ) : null}
                            </li>
                          ))}
                        </ul>
                      </section>
                    ) : (
                      <section aria-label="发现"><h3>发现</h3><p>{item.text || item.title}</p></section>
                    )}
                    {item.kind === "coverage_gap" ? (
                      <section aria-label="覆盖说明"><h3>覆盖说明</h3><p>{item.state_reason_zh || "本轮双cohort未能完成该受试者的核实，覆盖不足如实标出，待下轮补核。"}</p></section>
                    ) : null}
                  </div>
                  <footer className="monitoring-query-card-actions">
                    <button type="button" disabled={!subject} onClick={() => subject && onSubjectSelect?.(subject)}>进入受试者医学旅程</button>
                    {item.anchor_event_refs?.length && onFindingSelect ? (
                      <button type="button" className="monitoring-back-button" onClick={() => onFindingSelect?.(item)}>定位关联事件</button>
                    ) : null}
                  </footer>
                </li>
              );
            })}
          </ul>
        </section>
      ) : null}
      {findingCards.length || legacyDraftRows.length || (queryFindingsMeta.shape === "finding_dto_v1" && queryFindingsMeta.state !== "not_applicable") ? (
        <section className="monitoring-panel monitoring-panel-wide" data-monitoring-finding-cards>
          <div className="monitoring-section-heading"><span className="monitoring-eyebrow">真实发现</span><h2>发现（{findingCards.length} 条 · 载荷形态 {queryFindingsMeta.shape === "legacy_query_drafts" ? "旧版draft载荷" : "Finding DTO"}）</h2></div>
          {findingCards.length ? (
            <ul className="monitoring-query-card-list">
              {findingCards.map((item) => {
                const claims = Array.isArray(item.claims) ? item.claims : [];
                const sourceRefs = Array.isArray(item.sourceRefs) ? item.sourceRefs : [];
                const windowText = item.windowStart || item.windowEnd
                  ? `${item.windowStart || "未知"} — ${item.windowEnd || "未知"}`
                  : "时间窗待确认";
                return (
                  <li key={item.findingId} className="monitoring-query-card" data-query-finding={item.findingId} data-finding-state={item.findingState} data-finding-kind={item.scopeKind || "finding"}>
                    <header className="monitoring-query-card-head">
                      <span className={`monitoring-query-state-chip monitoring-query-state-${item.findingState}`}>{FINDING_STATE_LABELS[item.findingState] || item.findingState}</span>
                      <strong>{item.findingId}</strong>
                      <span className="monitoring-query-card-target">
                        受试者{" "}
                        <button type="button" className="monitoring-subject-link" onClick={() => onSubjectSelect?.({ subject_ref: item.subjectRef, site_ref: item.siteRef })}>{item.subjectRef || "—"}</button>
                        {" "}· 中心 {item.siteRef || "—"}
                      </span>
                    </header>
                    <div className="monitoring-query-card-body">
                      <section aria-label="事件与时间窗"><h3>事件与时间窗</h3>
                        <p data-finding-event-ref={item.eventRef || ""}>{item.eventRef || "未关联具体事件"} · {windowText}</p>
                      </section>
                      <section aria-label="分类型主张"><h3>分类型主张</h3>
                        <ul className="monitoring-claim-list">
                          {claims.map((claim, claimIndex) => (
                            <li key={claimIndex} data-claim-kind={claim.kind}>{CLAIM_KIND_LABELS[claim.kind] || claim.kind}：{claim.text}</li>
                          ))}
                        </ul>
                      </section>
                      <section aria-label="来源定位"><h3>来源定位（{sourceRefs.length} 条）</h3>
                        <ul>
                          {sourceRefs.map((ref, refIndex) => (
                            <li key={ref.evidenceId || refIndex} data-source-evidence-id={ref.evidenceId}>
                              {ref.path ? `${ref.path} · ${ref.recordId || ""} · ${ref.field || ""}` : ref.evidenceId}
                              <button type="button" className="monitoring-subject-link" onClick={() => onSource?.({ risk_instance_ref: item.riskId, source_locator_ref: ref.evidenceId })}>来源定位</button>
                            </li>
                          ))}
                        </ul>
                        {item.locator ? <p>{[item.locator.path, item.locator.recordId, item.locator.field].filter(Boolean).join(" · ")}</p> : null}
                      </section>
                    </div>
                    <footer className="monitoring-query-card-actions">
                      <button type="button" onClick={() => onSubjectSelect?.({ subject_ref: item.subjectRef, site_ref: item.siteRef })}>进入受试者医学旅程</button>
                      {item.eventRef && onFindingSelect ? (
                        <button type="button" className="monitoring-back-button" data-event-ref={item.eventRef} onClick={() => onFindingSelect?.({ subject_ref: item.subjectRef, site_ref: item.siteRef, anchor_event_refs: [item.eventRef] })}>定位关联事件</button>
                      ) : null}
                    </footer>
                  </li>
                );
              })}
            </ul>
          ) : legacyDraftRows.length ? (
            <div>
              <p className="monitoring-query-intro" data-monitoring-findings-legacy-note>本次结果为旧版载荷形态：仅含查询草稿（QueryDraft），以下按草稿如实呈现，不伪造Finding。</p>
              <ul className="monitoring-query-card-list">
                {legacyDraftRows.map((draft) => (
                  <li key={draft.queryDraftId} className="monitoring-query-card" data-query-draft={draft.queryDraftId}>
                    <header className="monitoring-query-card-head">
                      <span className="monitoring-query-state-chip monitoring-query-state-draft">草稿</span>
                      <strong>{draft.queryDraftId}</strong>
                      <span className="monitoring-query-card-target">引用Finding {draft.findingId || "—"}</span>
                    </header>
                    <div className="monitoring-query-card-body"><section aria-label="草稿内容"><h3>草稿内容</h3><p>{draft.displayText || "草稿内容待确认"}</p></section></div>
                  </li>
                ))}
              </ul>
            </div>
          ) : (
            <p className="monitoring-query-intro" data-monitoring-findings-empty>本轮零发现：findings为显式空集，不存在可导航的发现卡。</p>
          )}
        </section>
      ) : null}
      <section className="monitoring-panel monitoring-panel-wide">
        <div className="monitoring-section-heading"><span className="monitoring-eyebrow">查询工作区</span><h2>请核实事项（{risks.length} 项待核对 · 全量锚点 {numberText(totalCount)}）</h2></div>
        <p className="monitoring-query-intro">以下每张卡片按「依据 — 发现 — 请核实事项」三段呈现：先看数据依据，再看医学发现，最后由您核对原始记录后决定是否发出数据核查问题。AI 只定位证据和风险，医学判断由您终审。</p>
        {risks.length === 0 ? (
          <div className="monitoring-empty-inline">当前范围内没有待核实的查询事项。</div>
        ) : (
          <ul className="monitoring-query-card-list">
            {risks.map((risk) => {
              const subject = subjectsByRef.get(risk.subjectRef);
              const evidence = risk.evidenceSummary || {};
              return (
                <li key={risk.riskInstanceRef || risk.riskRef} className="monitoring-query-card" data-query-risk={risk.riskInstanceRef || risk.riskRef}>
                  <header className="monitoring-query-card-head">
                    <RiskBadge risk={risk} />
                    <strong>{risk.riskType}</strong>
                    <span className="monitoring-query-card-target">
                      受试者 {text(risk.subjectLabel, risk.subjectRef)} · 中心 {risk.siteLabel}
                    </span>
                    <span className={`monitoring-date-chip monitoring-date-${risk.dateState}`}>{risk.dateLabel}</span>
                  </header>
                  <div className="monitoring-query-card-body">
                    <section aria-label="依据"><h3>依据</h3><p>{text(evidence.basis, "依据当前项目监查规则及已绑定记录。")}</p></section>
                    <section aria-label="发现"><h3>发现</h3><p>{text(evidence.finding, `发现${risk.subjectLabel || risk.subjectRef}存在“${risk.riskType}”相关记录。`)}</p></section>
                    <section aria-label="请核实事项"><h3>请核实事项</h3><p>{text(evidence.query_draft || evidence.action_item, "请核对原始记录、研究方案与数据录入情况，并确认是否需要发出数据核查问题。")}</p></section>
                  </div>
                  <footer className="monitoring-query-card-actions">
                    <button type="button" disabled={!subject} onClick={() => subject && onSubjectSelect?.(subject)}>进入受试者医学旅程</button>
                    <button type="button" className="monitoring-back-button" disabled={!risk.sourceLocatorRef} onClick={() => onSource?.(risk)}>查看原始来源</button>
                  </footer>
                </li>
              );
            })}
          </ul>
        )}
        {onBack ? <div className="monitoring-query-footer"><button type="button" className="monitoring-back-button" onClick={onBack}>返回项目风险概览</button></div> : null}
      </section>
    </div>
  );
}

export function MedicalMonitoringWorkspace({ routeState, onRouteChange, onReturn }) {
  const adapter = useMemo(() => createMedicalMonitoringWorkspaceApi(), []);
  const route = routeCanonical(routeState);
  const effectiveView = route.view === "overview" && route.site_ref ? "site_overview" : route.view;
  const isMonitoringProductRoute = Boolean(
    route.project_ref
      && (!route.run_ref || route.public_run_token || route.result_context_token),
  );
  const routeValid = routeState?.valid !== false && Boolean(route.project_ref);
  const [payload, setPayload] = useState(null);
  const [status, setStatus] = useState(routeValid ? "loading" : "invalid");
  const [error, setError] = useState(null);
  const [focusIndex, setFocusIndex] = useState(0);
  // W05-J1 §3②：timeViewport（全程/自选/聚焦）与detailDensity（精简/
  // 标准/详细）拆成两个独立state——视窗决定px/day与scale范围，密度只
  // 影响聚合阈值/collisionWidth/标签详略（A17：切密度scale四值不变）。
  const [timeViewport, setTimeViewport] = useState("fit");
  const [timeZoom, setTimeZoom] = useState(0);
  const [detailDensity, setDetailDensity] = useState("standard");
  const lastRouteKey = useRef("");
  const risks = payload?.projection?.currentRisks || [];
  const currentRouteRef = useRef(route);
  const currentRisksRef = useRef(risks);
  currentRouteRef.current = route;
  currentRisksRef.current = risks;

  useEffect(() => {
    if (isMonitoringProductRoute) {
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
        const nextRoute = normalizeMedicalMonitoringWorkspaceRouteState({
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
  }, [adapter, isMonitoringProductRoute, onRouteChange, routeValid, route.project_ref, route.run_ref, route.snapshot_ref, route.cutoff_ref, route.site_ref, route.subject_ref, route.risk_instance_ref, route.view, route.spine_ref, route.axis_mode, route.window_start, route.window_end, route.visit_ref, route.event_ref, route.risk_anchor_ref, route.source_locator_ref]);

  useEffect(() => {
    const handleKey = (event) => {
      if (event.target instanceof HTMLInputElement || event.target instanceof HTMLTextAreaElement || event.target instanceof HTMLSelectElement || event.target?.isContentEditable) return;
      // 焦点位于流向图、流向筛选或流向表格时，不触发文档级风险列表与缩放快捷键。
      if (event.target instanceof SVGElement) return;
      if (event.target instanceof Element && event.target.closest("[data-monitoring-flow-scope]")) return;
      if (event.key === "-" || event.key === "0" || event.key === "+" || (event.key === "=" && event.shiftKey)) {
        event.preventDefault();
        setTimeZoom((current) => event.key === "0" ? 0 : event.key === "-" ? Math.max(-1, current - 1) : Math.min(1, current + 1));
        setTimeViewport(event.key === "0" ? "fit" : "custom");
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
        onRouteChange?.(routeStateForMedicalMonitoringWorkspaceView(route, "journey", {
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

  const navigate = (view, patch = {}) => onRouteChange?.(routeStateForMedicalMonitoringWorkspaceView(route, view, patch));
  const selectRisk = useCallback((risk) => {
    const currentRoute = currentRouteRef.current;
    if (risk?.__view) {
      onRouteChange?.(routeStateForMedicalMonitoringWorkspaceView(currentRoute, risk.__view));
      return;
    }
    const next = { risk_ref: risk.riskRef, risk_instance_ref: risk.riskInstanceRef, event_ref: risk.eventRef, risk_anchor_ref: risk.riskAnchorRef, subject_ref: risk.subjectRef || currentRoute.subject_ref, site_ref: risk.siteRef || currentRoute.site_ref, spine_ref: risk.spineRef || currentRoute.spine_ref, visit_ref: risk.visit_ref || currentRoute.visit_ref };
    const nextView = currentRoute.view === "overview" || currentRoute.view === "site_overview" ? "journey" : currentRoute.view;
    onRouteChange?.(routeStateForMedicalMonitoringWorkspaceView(currentRoute, nextView, next));
  }, [onRouteChange]);
  const selectCenter = (center) => navigate("site_overview", { site_ref: center.siteRef });
  const selectSubject = (subject) => navigate("journey", { subject_ref: subject.subject_ref || subject.subject_id, site_ref: subject.site_ref || subject.site_id, spine_ref: subject.spine_ref || route.spine_ref, run_ref: route.run_ref, snapshot_ref: route.snapshot_ref, cutoff_ref: route.cutoff_ref, window_start: route.window_start, window_end: route.window_end });
  const selectEvent = useCallback((event) => {
    const currentRoute = currentRouteRef.current;
    const riskAnchorRef = event.riskAnchorRefs[0] || "";
    const linkedRisk = currentRisksRef.current.find((risk) => risk.riskAnchorRef === riskAnchorRef);
    startTransition(() => onRouteChange?.(routeStateForMedicalMonitoringWorkspaceView(currentRoute, currentRoute.view, {
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
    onRouteChange?.(monitoringJourneyDrawerClosePatch(currentRouteRef.current));
  }, [onRouteChange]);
  // 流向筛选统一写回路由（主选择互斥）；Journey 往返由路由层保留 flow 键。
  const selectFlowStage = useCallback((stageRef, metric) => {
    const currentRoute = currentRouteRef.current;
    startTransition(() => onRouteChange?.(routeStateForMedicalMonitoringWorkspaceView(currentRoute, currentRoute.view, {
      flow_stage_ref: stageRef,
      flow_node_metric: metric === "reached" ? "reached" : "current",
      flow_link_ref: "",
    })));
  }, [onRouteChange]);
  const selectFlowLink = useCallback((linkRef) => {
    const currentRoute = currentRouteRef.current;
    startTransition(() => onRouteChange?.(routeStateForMedicalMonitoringWorkspaceView(currentRoute, currentRoute.view, {
      flow_link_ref: linkRef,
      flow_stage_ref: "",
      flow_node_metric: "",
    })));
  }, [onRouteChange]);
  const selectFlowMetric = useCallback((metric) => {
    const currentRoute = currentRouteRef.current;
    startTransition(() => onRouteChange?.(routeStateForMedicalMonitoringWorkspaceView(currentRoute, currentRoute.view, {
      flow_node_metric: metric === "reached" ? "reached" : "current",
    })));
  }, [onRouteChange]);
  const toggleFlowRiskBand = useCallback(() => {
    const currentRoute = currentRouteRef.current;
    const next = flowText(currentRoute, ["flow_risk_band"]) === "mid_high" ? "" : "mid_high";
    startTransition(() => onRouteChange?.(routeStateForMedicalMonitoringWorkspaceView(currentRoute, currentRoute.view, {
      flow_risk_band: next,
    })));
  }, [onRouteChange]);
  const clearFlowSelection = useCallback(() => {
    const currentRoute = currentRouteRef.current;
    startTransition(() => onRouteChange?.(routeStateForMedicalMonitoringWorkspaceView(currentRoute, currentRoute.view, {
      flow_stage_ref: "",
      flow_node_metric: "",
      flow_link_ref: "",
      flow_risk_band: "",
    })));
  }, [onRouteChange]);
  const jumpFlowSubject = useCallback((row) => {
    if (!row?.spineRef || !row?.jumpStart || !row?.jumpEnd) return;
    const currentRoute = currentRouteRef.current;
    onRouteChange?.(routeStateForMedicalMonitoringWorkspaceView(currentRoute, "journey", {
      subject_ref: row.subjectRef,
      site_ref: row.siteRef || currentRoute.site_ref,
      spine_ref: row.spineRef,
      window_start: row.jumpStart,
      window_end: row.jumpEnd,
    }));
  }, [onRouteChange]);
  const availableViews = MEDICAL_MONITORING_WORKSPACE_VIEWS.filter((view) => {
    if (view === "overview") return true;
    if (view === "queries") return true;
    if (view === "site_overview") return Boolean(route.site_ref);
    if (SUBJECT_VIEW_KEYS.includes(view)) return Boolean(route.subject_ref);
    if (view === "evidence") return Boolean(route.risk_instance_ref && route.source_locator_ref);
    return false;
  });
  const openQueries = useCallback(() => {
    const currentRoute = currentRouteRef.current;
    onRouteChange?.(routeStateForMedicalMonitoringWorkspaceView(currentRoute, "queries", {
      site_ref: "",
      subject_ref: "",
      spine_ref: "",
      window_start: "",
      window_end: "",
    }));
  }, [onRouteChange]);

  if (isMonitoringProductRoute) {
    return (
      <MedicalMonitoringProductLoop
        projectId={route.project_ref}
        route={route}
        onRouteChange={onRouteChange}
        onReturn={onReturn}
        OverviewView={OverviewView}
        SubjectWorkspaceView={SubjectWorkspaceView}
        EvidenceView={EvidenceView}
        QueryWorkspaceView={QueryWorkspaceView}
        onOpenQueries={openQueries}
      />
    );
  }

  return (
    <main className="monitoring-page" data-monitoring-view={effectiveView || "invalid"} data-monitoring-status={status} data-monitoring-viewport={timeViewport} data-monitoring-density={detailDensity}>
      <header className="monitoring-page-header">
        <div><span className="monitoring-eyebrow">医学监查</span><h1>{VIEW_LABELS[effectiveView] || "项目风险概览"}</h1><p>从项目风险进入中心与受试者，沿时间轴查看事件、趋势和来源依据</p></div>
        <div className="monitoring-page-actions"><ZoomControls timeViewport={timeViewport} timeZoom={timeZoom} detailDensity={detailDensity} onViewportChange={(next, zoom = 0) => { setTimeViewport(next); setTimeZoom(zoom); }} onDensityChange={setDetailDensity} focusAvailable={Boolean(route.event_ref)} /><button type="button" className="monitoring-back-button" onClick={onReturn}>医学监查首页</button></div>
      </header>
      <IdentityStrip identity={route} project={payload?.projection?.project || {}} />
      <nav className="monitoring-route-tabs" aria-label="医学监查页面导航">
        {availableViews.map((view) => {
          const label = view === "overview" && route.return_context_key && route.view !== "overview" ? "返回项目风险概览" : VIEW_LABELS[view];
          return <button type="button" key={view} className={effectiveView === view ? "is-active" : ""} onClick={() => navigate(view)}>{label}</button>;
        })}
      </nav>
      <MedicalMonitoringProgressPanel routeCanonical={route} />
      {status === "invalid" && <section className="monitoring-state-panel" role="alert"><strong>当前定位无法确认</strong><span>请返回上一级并重新打开已绑定的项目范围。</span></section>}
      {status === "loading" && <section className="monitoring-state-panel" role="status"><strong>正在读取当前范围</strong><span>项目身份、数据截止与来源链路保持一致后展示。</span></section>}
      {status === "error" && <section className="monitoring-state-panel" role="alert"><strong>当前范围暂不可用</strong><span>{unavailableMessage(error)}</span><button type="button" onClick={() => onRouteChange?.({ ...route })}>重新读取</button></section>}
      {status === "ready" && payload && (
        <>
          {route.view === "overview" || route.view === "site_overview" ? <OverviewView payload={payload} route={route} selectedRiskInstanceRef={route.risk_instance_ref} onRiskSelect={selectRisk} onCenterSelect={selectCenter} onSubjectSelect={selectSubject} onSource={openSource} onFlowStageSelect={selectFlowStage} onFlowLinkSelect={selectFlowLink} onFlowMetricSelect={selectFlowMetric} onFlowRiskToggle={toggleFlowRiskBand} onFlowClear={clearFlowSelection} onFlowSubjectJump={jumpFlowSubject} /> : null}
          {SUBJECT_VIEW_KEYS.includes(route.view) ? <SubjectWorkspaceView payload={payload} route={route} view={route.view} timeViewport={timeViewport} detailDensity={detailDensity} timeZoom={timeZoom} onRiskSelect={selectRisk} onEventSelect={selectEvent} onSource={openSource} onDrawerClose={closeJourneyDrawer} /> : null}
          {route.view === "evidence" ? <EvidenceView payload={payload} route={route} onBack={backFromEvidence} /> : null}
        </>
      )}
    </main>
  );
}

export default MedicalMonitoringWorkspace;
