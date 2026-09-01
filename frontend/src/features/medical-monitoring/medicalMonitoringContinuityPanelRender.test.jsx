// R7 Slice-08C-2 panel render fixture. Bundled by
// medicalMonitoringContinuityPanelRender.test.mjs via esbuild so the
// component, its imports and react-dom/server share one React copy (the
// panel uses useState/useMemo, so an outer react-dom/server would hit the
// "Invalid hook call" split-copy problem). Exports static markup strings
// only; the runner asserts against them. No DOM, no browser, no server.

import { renderToStaticMarkup } from "react-dom/server";
import { MedicalMonitoringContinuityPanel } from "./MedicalMonitoringContinuityPanel.jsx";
import {
  MONITORING_CONTINUITY_COMPARED_TEXT,
  MONITORING_CONTINUITY_FIRST_ANALYSIS_TEXT,
  MONITORING_CONTINUITY_ROW_LIMIT,
  MONITORING_CONTINUITY_UNAVAILABLE_TEXT,
  normalizeMonitoringContinuityEnvelope,
  rebuildMonitoringContinuityChangeCounts,
} from "./medicalMonitoringContinuityProjection.mjs";

function row(overrides = {}) {
  return {
    row_ref: "continuity-row-1",
    object_type: "risk",
    object_type_text: "风险",
    ordinal: 1,
    change_kind: "new",
    change_text: "新增",
    disposition: "reuse_unchanged",
    disposition_text: "沿用不变",
    data_change_kind: "added",
    data_change_text: "新增数据",
    severity_before_text: "",
    severity_after_text: "高",
    title: "不良事件与记录一致性",
    reason_text: "",
    attention_text: "",
    site_ref: "site/01",
    site_label: "中心一",
    subject_ref: "S/01",
    subject_label: "受试者 001",
    date_label: "2026-02-14",
    window_start: "2026-01-01",
    window_end: "2026-03-31",
    risk_ref: "s7-risk-1",
    risk_instance_ref: "s7-risk-1",
    risk_anchor_ref: "s7-anchor-1",
    event_ref: "s7-event-1",
    source_locator_ref: "s7-source-1",
    source_count: 1,
    ...overrides,
  };
}

function riskRow(ordinal, kind, before, after, subject, overrides = {}) {
  const kindTexts = {
    new: "新增",
    upgraded: "升级",
    continued: "持续",
    downgraded: "降级",
    closed: "关闭",
    reopened: "重开",
    needs_rejudgment: "需重新判断",
  };
  const disposition = kind === "closed" ? "close_with_evidence" : kind === "needs_rejudgment" ? "re_evaluate_prior_uncertain" : "reuse_unchanged";
  const dispositionText = kind === "closed" ? "已有证据支持关闭" : kind === "needs_rejudgment" ? "上轮依据不足，本轮重新分析" : "沿用不变";
  const dataChange = kind === "continued" ? "unchanged" : kind === "needs_rejudgment" ? "cannot_compare" : kind === "closed" ? "missing" : "added";
  const dataText = kind === "continued" ? "无变化" : kind === "needs_rejudgment" ? "无法直接比较" : kind === "closed" ? "本轮未见对应记录" : "新增数据";
  const site = subject === "S/03" ? "site/03" : subject === "S/07" ? "site/07" : "site/01";
  return row({
    row_ref: `continuity-row-${ordinal}`,
    ordinal,
    change_kind: kind,
    change_text: kindTexts[kind],
    disposition,
    disposition_text: dispositionText,
    data_change_kind: dataChange,
    data_change_text: dataText,
    severity_before_text: before,
    severity_after_text: after,
    subject_ref: subject,
    subject_label: `受试者 ${subject}`,
    site_ref: site,
    site_label: subject === "S/03" ? "中心三" : subject === "S/07" ? "中心七" : "中心一",
    risk_ref: `s7-risk-${ordinal}`,
    risk_instance_ref: `s7-risk-${ordinal}`,
    risk_anchor_ref: `s7-anchor-${ordinal}`,
    event_ref: `s7-event-${ordinal}`,
    source_locator_ref: `s7-source-${ordinal}`,
    source_count: 1,
    ...overrides,
  });
}

function queryRow(ordinal) {
  return row({
    row_ref: `continuity-row-${ordinal}`,
    object_type: "query_draft",
    object_type_text: "Query 草稿",
    ordinal,
    change_kind: "new",
    change_text: "新增",
    severity_before_text: "",
    severity_after_text: "",
    title: "实验室复查 Query 草稿",
    subject_ref: "S/05",
    subject_label: "受试者 005",
    risk_ref: "",
    risk_instance_ref: "",
    risk_anchor_ref: "",
    event_ref: `s7-event-q-${ordinal}`,
    source_locator_ref: "",
    source_count: 0,
  });
}

function outputRow(ordinal) {
  return row({
    row_ref: `continuity-row-${ordinal}`,
    object_type: "monitoring_output",
    object_type_text: "监查结果项",
    ordinal,
    change_kind: "continued",
    change_text: "持续",
    severity_before_text: "",
    severity_after_text: "",
    title: "监查发现跟踪项",
    subject_ref: "S/06",
    subject_label: "受试者 006",
    risk_ref: "",
    risk_instance_ref: "",
    risk_anchor_ref: "",
    event_ref: `s7-event-o-${ordinal}`,
    source_locator_ref: `s7-source-o-${ordinal}`,
    source_count: 1,
  });
}

function envelope(rows, { totalCount, truncated, comparisonText = MONITORING_CONTINUITY_COMPARED_TEXT, sourceRunText = "2026-03-01 监查批次" } = {}) {
  return {
    result_context_token: "result-context:01",
    identity: {
      project_ref: "project-a",
      public_run_token: "run:09",
      snapshot_token: "snapshot:09",
      data_cutoff_text: "2026-03-31",
      mode_text: "日常监查",
      site_scope_text: "中心一、中心二",
    },
    comparison: {
      available: true,
      basis_text: "增量分析",
      comparison_text: comparisonText,
      source_run_text: sourceRunText,
      change_counts: rebuildMonitoringContinuityChangeCounts(rows),
      rows,
      shown_count: rows.length,
      total_count: totalCount ?? rows.length,
      truncated: truncated ?? false,
    },
    response_digest: "0".repeat(64),
  };
}

function normalized(rows, options) {
  return normalizeMonitoringContinuityEnvelope(envelope(rows, options), {
    projectId: "project-a",
    resultContextToken: "result-context:01",
  });
}

// Server sort order (monitoringContinuityRowSortKey): group 0 (high priority changes),
// group 1 (mid priority changes), group 2 (closed), group 3 (low continued),
// group 4 (query drafts), group 5 (monitoring outputs).
const READY_ROWS = [
  riskRow(1, "new", "", "高", "S/01", {
    title: "不良事件与记录一致性",
    reason_text: "本轮记录与上轮不一致，已重新分析。",
  }),
  riskRow(2, "upgraded", "中", "高", "S/01"),
  riskRow(6, "needs_rejudgment", "", "高", "S/07"),
  riskRow(3, "needs_rejudgment", "", "中", "S/03", {
    source_locator_ref: "",
    source_count: 0,
    attention_text: "身份或数据不完整，需重新判断",
  }),
  riskRow(4, "closed", "中", "", "S/02", {
    attention_text: "未见记录不代表风险已解除",
  }),
  riskRow(5, "continued", "低", "低", "S/02"),
  queryRow(8),
  outputRow(9),
];

// Projection subjects: S/01/S/03 resolvable (spine variants exercised), the
// visible needs_rejudgment row S/07 intentionally absent so its Journey
// button stays gated closed.
const RESULT_PAYLOAD = {
  projection: {
    subjects: [
      { subject_ref: "S/01", site_ref: "site/01", spine_ref: "spine/01" },
      { subject_id: "S/03", site_id: "site/03", spineRef: "spine/03" },
    ],
    subjectFlow: {
      availability: "available",
      reconciliation: { state: "matched" },
      subjects: [
        { subject_ref: "S/01", site_ref: "site/01", spine_ref: "spine/01", journey_jump_enabled: true, jump_window_start: "2025-12-01", jump_window_end: "2026-04-30" },
        { subject_ref: "S/03", site_ref: "site/03", spine_ref: "spine/03", journey_jump_enabled: true, jump_window_start: "2025-12-01", jump_window_end: "2026-04-30" },
      ],
    },
  },
};

const readyContinuity = normalized(READY_ROWS);

const EMPTY_ROWS = [];
const emptyContinuity = normalized(EMPTY_ROWS);

const TRUNCATED_ROWS = Array.from(
  { length: MONITORING_CONTINUITY_ROW_LIMIT },
  (_, index) => riskRow(index + 1, "continued", "低", "低", `S/${index + 1}`, { title: `持续观察项 ${index + 1}` }),
);
const truncatedContinuity = normalized(TRUNCATED_ROWS, {
  totalCount: MONITORING_CONTINUITY_ROW_LIMIT + 1,
  truncated: true,
});

const readyFirstAnalysis = normalized(
  [riskRow(1, "new", "", "高", "S/01")],
  { comparisonText: MONITORING_CONTINUITY_FIRST_ANALYSIS_TEXT, sourceRunText: "" },
);

export const renders = {
  loading: renderToStaticMarkup(
    <MedicalMonitoringContinuityPanel loading continuity={null} />,
  ),
  unavailableDefault: renderToStaticMarkup(
    <MedicalMonitoringContinuityPanel continuity={null} />,
  ),
  unavailableCustom: renderToStaticMarkup(
    <MedicalMonitoringContinuityPanel continuity={null} unavailable="自定义错误提示" />,
  ),
  unavailableWins: renderToStaticMarkup(
    <MedicalMonitoringContinuityPanel continuity={readyContinuity} unavailable="自定义错误提示" resultPayload={RESULT_PAYLOAD} />,
  ),
  ready: renderToStaticMarkup(
    <MedicalMonitoringContinuityPanel continuity={readyContinuity} resultPayload={RESULT_PAYLOAD} onJourney={() => {}} onSource={() => {}} />,
  ),
  readyFirstAnalysis: renderToStaticMarkup(
    <MedicalMonitoringContinuityPanel continuity={readyFirstAnalysis} resultPayload={RESULT_PAYLOAD} />,
  ),
  empty: renderToStaticMarkup(
    <MedicalMonitoringContinuityPanel continuity={emptyContinuity} resultPayload={RESULT_PAYLOAD} />,
  ),
  truncated: renderToStaticMarkup(
    <MedicalMonitoringContinuityPanel continuity={truncatedContinuity} resultPayload={RESULT_PAYLOAD} />,
  ),
};

export const expectedCounts = rebuildMonitoringContinuityChangeCounts(READY_ROWS);
export const expectedTruncationText =
  `变化较多，共 ${MONITORING_CONTINUITY_ROW_LIMIT + 1} 条，当前显示前 ${MONITORING_CONTINUITY_ROW_LIMIT} 条（服务端最多返回 ${MONITORING_CONTINUITY_ROW_LIMIT} 条）。`;
export const unavailableText = MONITORING_CONTINUITY_UNAVAILABLE_TEXT;
