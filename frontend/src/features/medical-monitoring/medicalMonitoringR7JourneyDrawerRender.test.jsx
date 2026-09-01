// R7 Slice-08C-3 render fixture. Bundled by
// medicalMonitoringR7JourneyDrawerRender.test.mjs via esbuild so the page,
// the drawer and react-dom/server share one React copy. Exports static markup
// strings only; the runner asserts against them. No DOM, no browser, no server.
//
// Covers (contract §7.2/§7.3): the single shared horizontal axis with the
// eight domain lanes, the R7-only change markers (icon + Chinese word + tone),
// explicit risk levels, pending-date sinking, the fixed drawer section order,
// overlay/push markup, stable accessible ids, fallback texts, the truncation
// prompt and the legacy-R5 untouched render.

import { renderToStaticMarkup } from "react-dom/server";
import { DomainTracks, RiskRow } from "./MedicalMonitoringR5Page.jsx";
import {
  MedicalMonitoringR7JourneyDrawer,
  R7JourneyChangeMarker,
  r7JourneyDrawerSections,
} from "./MedicalMonitoringR7JourneyDrawer.jsx";
import {
  bindR7ContinuityRowsToJourney,
  r7EventChangeMarker,
} from "./medicalMonitoringR7JourneyChanges.mjs";
import {
  R7_CONTINUITY_CHANGE_KIND_TEXTS,
  R7_CONTINUITY_CHANGE_KINDS,
  R7_CONTINUITY_FIRST_ANALYSIS_TEXT,
} from "./medicalMonitoringR7ContinuityProjection.mjs";
import { R7_JOURNEY_CHANGE_KIND_VISUAL } from "./medicalMonitoringR7JourneyChanges.mjs";

const DOMAIN_KEYS = [
  "ae",
  "mh",
  "cm",
  "ip",
  "lab_exam",
  "hospital_procedure",
  "symptom_efficacy",
  "protocol_compliance",
];
const DOMAIN_SHORT = {
  ae: "AE",
  mh: "MH",
  cm: "CM",
  ip: "IP",
  lab_exam: "检验",
  hospital_procedure: "住院",
  symptom_efficacy: "疗效",
  protocol_compliance: "方案",
};

function journeyProjection() {
  const domains = DOMAIN_KEYS.map((domain) => ({ domain, shortLabel: DOMAIN_SHORT[domain] }));
  const domainEncoding = (domain) => ({ domain, shortLabel: DOMAIN_SHORT[domain] });
  const events = [
    {
      eventRef: "evt-ae-1",
      domain: "ae",
      domainEncoding: domainEncoding("ae"),
      eventLabel: "发热伴感染",
      start: "2026-02-01",
      end: "2026-02-05",
      dateState: "exact",
      dateLabel: "精确日期",
      riskAnchorRefs: ["anchor-ae-1"],
      sourceLocatorRefs: ["src-1"],
    },
    {
      eventRef: "evt-mh-1",
      domain: "mh",
      domainEncoding: domainEncoding("mh"),
      eventLabel: "高血压病史",
      start: "2026-01-15",
      dateState: "exact",
      dateLabel: "精确日期",
      riskAnchorRefs: [],
      sourceLocatorRefs: [],
    },
    {
      eventRef: "evt-cm-1",
      domain: "cm",
      domainEncoding: domainEncoding("cm"),
      eventLabel: "合并用药调整",
      start: "2026-03-10",
      dateState: "exact",
      dateLabel: "精确日期",
      riskAnchorRefs: [],
      sourceLocatorRefs: [],
    },
    {
      eventRef: "evt-ip-1",
      domain: "ip",
      domainEncoding: domainEncoding("ip"),
      eventLabel: "试验药暂停",
      start: "2026-02-20",
      end: "2026-03-01",
      dateState: "exact",
      dateLabel: "精确日期",
      riskAnchorRefs: [],
      sourceLocatorRefs: [],
    },
    {
      eventRef: "evt-lab-1",
      domain: "lab_exam",
      domainEncoding: domainEncoding("lab_exam"),
      eventLabel: "血常规复查",
      start: "2026-03-15",
      dateState: "exact",
      dateLabel: "精确日期",
      riskAnchorRefs: [],
      sourceLocatorRefs: [],
    },
    {
      eventRef: "evt-proc-1",
      domain: "hospital_procedure",
      domainEncoding: domainEncoding("hospital_procedure"),
      eventLabel: "住院观察",
      start: "2026-02-08",
      dateState: "exact",
      dateLabel: "精确日期",
      riskAnchorRefs: [],
      sourceLocatorRefs: [],
    },
    {
      eventRef: "evt-sym-1",
      domain: "symptom_efficacy",
      domainEncoding: domainEncoding("symptom_efficacy"),
      eventLabel: "症状好转",
      start: "2026-03-05",
      dateState: "exact",
      dateLabel: "精确日期",
      riskAnchorRefs: [],
      sourceLocatorRefs: [],
    },
    {
      eventRef: "evt-pc-1",
      domain: "protocol_compliance",
      domainEncoding: domainEncoding("protocol_compliance"),
      eventLabel: "方案执行核查",
      start: "2026-02-12",
      dateState: "exact",
      dateLabel: "精确日期",
      riskAnchorRefs: [],
      sourceLocatorRefs: [],
    },
    // pending: missing date must sink to the pending zone, never the axis.
    {
      eventRef: "evt-pending",
      domain: "cm",
      domainEncoding: domainEncoding("cm"),
      eventLabel: "合并用药日期待确认",
      start: null,
      dateState: "missing",
      dateLabel: "日期待确认",
      riskAnchorRefs: [],
      sourceLocatorRefs: [],
    },
  ];
  const visits = [
    { visit_ref: "visit-1", actual_date: "2026-01-10", visit_label: "筛选访视" },
    { visit_ref: "visit-2", actual_date: "2026-02-14", visit_label: "第 2 次访视" },
  ];
  const currentRisks = [
    {
      riskInstanceRef: "risk-i-ae-1",
      riskAnchorRef: "anchor-ae-1",
      riskRef: "risk-ae-1",
      severity: "high",
      severityLabel: "高",
      riskType: "发热与感染记录一致性",
      dateLabel: "2026-02-01",
      sourceLocatorRef: "src-1",
      sourceLocatorRefs: ["src-1"],
      domainEncoding: domainEncoding("ae"),
      subjectLabel: "受试者 001",
      siteLabel: "中心一",
      riskStatus: "confirmed",
      changeLabel: "升级",
      changeCauseLabel: "数据修订",
      evidenceSummary: { query_draft: "请核实发热记录与检验结果的一致性。" },
    },
    {
      riskInstanceRef: "risk-i-ae-2",
      riskAnchorRef: "anchor-ae-2",
      riskRef: "risk-ae-2",
      severity: "medium",
      severityLabel: "中",
      riskType: "合并感染风险",
      dateLabel: "2026-02-01",
      sourceLocatorRef: "",
      sourceLocatorRefs: [],
      domainEncoding: domainEncoding("ae"),
      subjectLabel: "受试者 001",
      siteLabel: "中心一",
      riskStatus: "confirmed",
      changeLabel: "新增",
      changeCauseLabel: "新增数据",
    },
    {
      riskInstanceRef: "risk-i-mh-1",
      riskAnchorRef: "anchor-mh-1",
      riskRef: "risk-mh-1",
      severity: "high",
      severityLabel: "高",
      riskType: "高血压病史记录完整性",
      dateLabel: "2026-01-15",
      sourceLocatorRef: "src-2",
      sourceLocatorRefs: ["src-2"],
      domainEncoding: domainEncoding("mh"),
      subjectLabel: "受试者 001",
      siteLabel: "中心一",
      riskStatus: "confirmed",
      changeLabel: "持续",
      changeCauseLabel: "覆盖范围不变",
      evidenceSummary: { query_draft: "请补充既往史记录来源。" },
    },
    // risk-only bound row target: no event, no anchor, exists in currentRisks.
    {
      riskInstanceRef: "risk-i-mh-2",
      riskAnchorRef: "anchor-mh-2",
      riskRef: "risk-mh-2",
      severity: "medium",
      severityLabel: "中",
      riskType: "既往史补录核查",
      dateLabel: "2026-02-10",
      sourceLocatorRef: "src-3",
      sourceLocatorRefs: ["src-3"],
      domainEncoding: domainEncoding("mh"),
      subjectLabel: "受试者 001",
      siteLabel: "中心一",
      riskStatus: "confirmed",
      changeLabel: "新增",
      changeCauseLabel: "补录核查",
    },
  ];
  return {
    domains,
    events,
    currentRisks,
    temporalSpine: {
      visits,
      pendingDates: [],
      windowStart: "2026-01-01",
      windowEnd: "2026-03-31",
      axisMode: "calendar",
    },
    raw: { subject: { site_ref: "site/01", subject_label: "受试者 001" } },
  };
}

// Same-identity same-window journey rows (site/01, S/01, axis window).
function journeyRow(overrides = {}) {
  return {
    row_ref: "journey-row-1",
    object_type: "risk",
    object_type_text: "风险",
    ordinal: 1,
    change_kind: "upgraded",
    change_text: "升级",
    disposition: "reuse_unchanged",
    disposition_text: "沿用不变",
    data_change_kind: "revised",
    data_change_text: "数据修订",
    severity_before_text: "中",
    severity_after_text: "高",
    title: "发热与感染记录一致性",
    reason_text: "本轮体温记录修订，等级升高。",
    attention_text: "",
    site_ref: "site/01",
    site_label: "中心一",
    subject_ref: "S/01",
    subject_label: "受试者 001",
    date_label: "2026-02-01",
    window_start: "2026-02-01",
    window_end: "2026-02-05",
    risk_ref: "risk-ae-1",
    risk_instance_ref: "risk-i-ae-1",
    risk_anchor_ref: "anchor-ae-1",
    event_ref: "evt-ae-1",
    source_locator_ref: "src-1",
    source_count: 1,
    ...overrides,
  };
}

const JOURNEY_ROWS = [
  journeyRow({
    row_ref: "journey-row-1",
    ordinal: 1,
    change_kind: "upgraded",
    change_text: "升级",
    severity_before_text: "中",
    severity_after_text: "高",
    title: "发热与感染记录一致性",
    reason_text: "本轮体温记录修订，等级升高。",
  }),
  journeyRow({
    row_ref: "journey-row-2",
    ordinal: 2,
    change_kind: "new",
    change_text: "新增",
    severity_before_text: "",
    severity_after_text: "中",
    title: "合并感染风险",
    risk_instance_ref: "risk-i-ae-2",
    risk_anchor_ref: "anchor-ae-2",
    event_ref: "evt-ae-1",
    source_locator_ref: "",
    source_count: 0,
  }),
  journeyRow({
    row_ref: "journey-row-3",
    ordinal: 3,
    change_kind: "continued",
    change_text: "持续",
    severity_before_text: "低",
    severity_after_text: "低",
    title: "高血压病史持续观察",
    risk_instance_ref: "risk-i-mh-1",
    risk_anchor_ref: "anchor-mh-1",
    event_ref: "evt-mh-1",
    date_label: "2026-01-15",
    window_start: "2026-01-15",
    window_end: "2026-01-15",
  }),
  journeyRow({
    row_ref: "journey-row-4",
    ordinal: 4,
    change_kind: "new",
    change_text: "新增",
    severity_before_text: "",
    severity_after_text: "中",
    title: "既往史补录核查",
    risk_instance_ref: "risk-i-mh-2",
    risk_anchor_ref: "anchor-mh-2",
    event_ref: "",
    source_locator_ref: "src-3",
    source_count: 1,
  }),
  // closed row used by the drawer model renders (not bound to the axis).
  journeyRow({
    row_ref: "journey-row-5",
    ordinal: 5,
    change_kind: "closed",
    change_text: "关闭",
    severity_before_text: "高",
    severity_after_text: "",
    title: "已关闭风险核查",
    risk_instance_ref: "risk-i-closed-1",
    risk_anchor_ref: "anchor-closed-1",
    event_ref: "",
    source_locator_ref: "",
    source_count: 0,
  }),
];

const projection = journeyProjection();
const binding = bindR7ContinuityRowsToJourney(
  JOURNEY_ROWS,
  projection.events,
  projection.currentRisks,
);
const markersByEvent = new Map(
  binding.events.map((group) => [group.eventRef, r7EventChangeMarker(group.rows)]),
);
// Mirrors the page: the right-side risk list aggregates every journey row of
// one risk_instance_ref, whether bound to an event or by risk_instance_ref.
const rowsByRiskInstance = new Map();
for (const group of binding.events) {
  for (const row of group.rows) {
    const instance = row.risk_instance_ref;
    if (!instance) continue;
    if (!rowsByRiskInstance.has(instance)) rowsByRiskInstance.set(instance, []);
    rowsByRiskInstance.get(instance).push(row);
  }
}
for (const group of binding.risks) {
  if (!rowsByRiskInstance.has(group.riskInstanceRef)) rowsByRiskInstance.set(group.riskInstanceRef, []);
  rowsByRiskInstance.get(group.riskInstanceRef).push(...group.rows);
}
const markersByRisk = new Map(
  [...rowsByRiskInstance.entries()].map(([instance, rows]) => [instance, r7EventChangeMarker(rows)]),
);

const axis = renderToStaticMarkup(
  <DomainTracks
    projection={projection}
    zoomLevel={0}
    selectedEventRef=""
    selectedRiskAnchorRef=""
    onEventSelect={() => {}}
    journeyEnabled
    journeyMarkerByEventRef={Object.fromEntries(markersByEvent.entries())}
    journeyTruncationText="本轮变化较多，当前仅显示服务端已返回的前 3 条；请返回项目或中心概览查看完整范围说明。"
  />,
);

const legacyAxis = renderToStaticMarkup(
  <DomainTracks projection={projection} zoomLevel={0} selectedEventRef="" selectedRiskAnchorRef="" onEventSelect={() => {}} />,
);

const riskRowWithMarker = renderToStaticMarkup(
  <RiskRow risk={projection.currentRisks[2]} onSelect={() => {}} marker={markersByRisk.get("risk-i-mh-1") || null} />,
);

const comparison = { comparison_text: "已与上次监查结果比较" };
const firstAnalysisComparison = { comparison_text: R7_CONTINUITY_FIRST_ANALYSIS_TEXT };

const aeEvent = {
  ...projection.events[0],
  risk: projection.currentRisks[0],
  visitLabel: "第 2 次访视",
};

const eventSections = r7JourneyDrawerSections({
  event: aeEvent,
  risk: projection.currentRisks[0],
  currentRow: JOURNEY_ROWS[0],
  comparison,
});
const closedSections = r7JourneyDrawerSections({
  event: null,
  risk: null,
  currentRow: JOURNEY_ROWS[4],
  comparison,
});
const riskOnlySections = r7JourneyDrawerSections({
  event: null,
  risk: projection.currentRisks[3],
  currentRow: JOURNEY_ROWS[3],
  comparison,
});
const fallbackSections = r7JourneyDrawerSections({
  event: null,
  risk: null,
  currentRow: null,
  comparison: null,
});
const firstAnalysisSections = r7JourneyDrawerSections({
  event: null,
  risk: projection.currentRisks[0],
  currentRow: JOURNEY_ROWS[0],
  comparison: firstAnalysisComparison,
});

const overlayDrawer = renderToStaticMarkup(
  <MedicalMonitoringR7JourneyDrawer
    mode="overlay"
    sections={eventSections}
    changeRows={[JOURNEY_ROWS[0], JOURNEY_ROWS[1]]}
    currentRowIndex={0}
    onSelectRow={() => {}}
    onClose={() => {}}
    onSource={() => {}}
  />,
);

const pushDrawer = renderToStaticMarkup(
  <MedicalMonitoringR7JourneyDrawer
    mode="push"
    sections={riskOnlySections}
    changeRows={[JOURNEY_ROWS[3]]}
    currentRowIndex={0}
    onSelectRow={() => {}}
    onClose={() => {}}
    onSource={() => {}}
  />,
);

const closedDrawer = renderToStaticMarkup(
  <MedicalMonitoringR7JourneyDrawer
    mode="overlay"
    sections={closedSections}
    changeRows={[JOURNEY_ROWS[4]]}
    currentRowIndex={0}
    onSelectRow={() => {}}
    onClose={() => {}}
    onSource={() => {}}
  />,
);

const fallbackDrawer = renderToStaticMarkup(
  <MedicalMonitoringR7JourneyDrawer
    mode="overlay"
    sections={fallbackSections}
    changeRows={[]}
    currentRowIndex={-1}
    onSelectRow={() => {}}
    onClose={() => {}}
    onSource={() => {}}
  />,
);

const firstAnalysisDrawer = renderToStaticMarkup(
  <MedicalMonitoringR7JourneyDrawer
    mode="push"
    sections={firstAnalysisSections}
    changeRows={[]}
    currentRowIndex={-1}
    onSelectRow={() => {}}
    onClose={() => {}}
    onSource={() => {}}
  />,
);

const sevenMarkers = renderToStaticMarkup(
  <>
    {R7_CONTINUITY_CHANGE_KINDS.map((kind) => (
      <R7JourneyChangeMarker
        key={kind}
        marker={{
          changeKind: kind,
          changeText: R7_JOURNEY_CHANGE_KIND_VISUAL[kind].label,
          icon: R7_JOURNEY_CHANGE_KIND_VISUAL[kind].icon,
          tone: R7_JOURNEY_CHANGE_KIND_VISUAL[kind].tone,
          total: 1,
          countSuffix: "",
        }}
      />
    ))}
  </>,
);

export const renders = {
  axis,
  legacyAxis,
  riskRowWithMarker,
  overlayDrawer,
  pushDrawer,
  closedDrawer,
  fallbackDrawer,
  firstAnalysisDrawer,
  sevenMarkers,
};

export const expected = {
  changeKindTexts: R7_CONTINUITY_CHANGE_KIND_TEXTS,
  changeKinds: R7_CONTINUITY_CHANGE_KINDS,
  eventSections,
  closedSections,
  riskOnlySections,
  fallbackSections,
  firstAnalysisSections,
  truncationText: "本轮变化较多，当前仅显示服务端已返回的前 3 条；请返回项目或中心概览查看完整范围说明。",
  markersByEvent: Object.fromEntries(markersByEvent.entries()),
  markersByRisk: Object.fromEntries(markersByRisk.entries()),
};
