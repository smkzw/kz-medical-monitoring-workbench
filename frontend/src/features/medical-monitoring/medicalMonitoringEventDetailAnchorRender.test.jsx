// R29-06 regression fixture. 带风险锚点（URL risk_anchor_ref）进入
// 受试者工作区「事件明细」（view=timeline）必须正常渲染选中事件行与
// 诚实等级徽章，不得落入错误边界。R29-06根因：R24V2-B02把
// riskSeverityLabel重命名为riskSeverityInfo时漏改EventRow/待确认区两处
// 调用，锚点渲染即抛ReferenceError。Bundled by
// medicalMonitoringEventDetailAnchorRender.test.mjs via esbuild。
import { renderToStaticMarkup } from "react-dom/server";
import { SubjectWorkspaceView } from "./MedicalMonitoringWorkspace.jsx";

const domains = [
  { domain: "ae", shape: "rounded_rect", lineStyle: "solid", shortLabel: "AE" },
  { domain: "mh", shape: "bookmark", lineStyle: "dot_dash", shortLabel: "MH" },
  { domain: "ip", shape: "hexagon", lineStyle: "step", shortLabel: "试验药" },
  { domain: "lab_exam", shape: "square", lineStyle: "trend", shortLabel: "检验/检查" },
  { domain: "cm", shape: "capsule", lineStyle: "solid", shortLabel: "合并用药" },
  { domain: "hospital_procedure", shape: "doorframe", lineStyle: "solid", shortLabel: "住院/操作" },
  { domain: "symptom_efficacy", shape: "circle", lineStyle: "trend", shortLabel: "症状/疗效" },
  { domain: "protocol_compliance", shape: "single_flag", lineStyle: "bracket", shortLabel: "方案符合" },
];

const svRisk = {
  riskRef: "risk-sv-1",
  riskInstanceRef: "inst-sv-1",
  riskAnchorRef: "event-SV-000053",
  severity: "high",
  riskType: "访视超窗",
  dateState: "exact",
  dateLabel: "精确日期",
  changeLabel: "新增",
  domain: "protocol_compliance",
  domainEncoding: domains[7],
  sourceLocatorRef: "loc-sv-1",
  evidenceSummary: { query_draft: "请核实访视日期与方案要求是否一致。" },
};

const svEvent = {
  eventRef: "event-SV-000053",
  domain: "protocol_compliance",
  domainEncoding: domains[7],
  subtype: "visit",
  start: "2026-06-10",
  end: "2026-06-10",
  dateState: "exact",
  dateLabel: "精确日期",
  eventLabel: "V2 访视",
  riskAnchorRefs: ["event-SV-000053"],
  sourceLocatorRefs: ["loc-sv-1"],
};

function projectionWith(events, risks) {
  return {
    currentRisks: risks,
    subjects: [],
    domains,
    raw: { subject: { subject_label: "24008", site_ref: "s7-site-small-01" } },
    temporalSpine: {
      axisMode: "calendar",
      windowStart: "2026-06-01",
      windowEnd: "2026-08-20",
      visits: [],
      pendingDates: [],
    },
    events,
    indicators: null,
    aemhHistory: [],
  };
}

const anchorPayload = { projection: projectionWith([svEvent], [svRisk]), publicResultContext: false, source_refs: [] };

function renderSubjectView(payload, route, view) {
  return renderToStaticMarkup(
    <SubjectWorkspaceView payload={payload} route={route} view={view} />,
  );
}

export const renders = {
  // 对照组：无锚点 view=timeline（R29报告的对照，须保持正常）
  timelineWithoutAnchor: (() => {
    try {
      return { ok: true, html: renderSubjectView(
        anchorPayload,
        { subject_ref: "24008", view: "timeline", risk_anchor_ref: "", event_ref: "", risk_instance_ref: "" },
        "timeline",
      ) };
    } catch (error) {
      return { ok: false, error: String((error && error.stack) || error) };
    }
  })(),
  // 崩溃组：带锚点 view=timeline（R29-06必现路径）
  timelineWithAnchor: (() => {
    try {
      return { ok: true, html: renderSubjectView(
        anchorPayload,
        { subject_ref: "24008", view: "timeline", risk_anchor_ref: "event-SV-000053", event_ref: "", risk_instance_ref: "" },
        "timeline",
      ) };
    } catch (error) {
      return { ok: false, error: String((error && error.stack) || error) };
    }
  })(),
  // 对照组：带锚点 view=journey（R29报告的对照，须保持正常）
  journeyWithAnchor: (() => {
    try {
      return { ok: true, html: renderSubjectView(
        anchorPayload,
        { subject_ref: "24008", view: "journey", risk_anchor_ref: "event-SV-000053", event_ref: "", risk_instance_ref: "" },
        "journey",
      ) };
    } catch (error) {
      return { ok: false, error: String((error && error.stack) || error) };
    }
  })(),
  // 待确认区带risk事件的pending渲染（1051同类隐患回归）
  timelineWithPendingRisk: (() => {
    try {
      const pendingEvent = {
        ...svEvent,
        eventRef: "event-AE-000039",
        domain: "ae",
        domainEncoding: domains[0],
        start: null,
        end: null,
        dateState: "missing",
        eventLabel: "日期缺失不良事件",
        riskAnchorRefs: [],
        sourceLocatorRefs: [],
        risk: svRisk,
      };
      return { ok: true, html: renderSubjectView(
        { projection: projectionWith([svEvent, pendingEvent], [svRisk]), publicResultContext: false, source_refs: [] },
        { subject_ref: "24008", view: "timeline", risk_anchor_ref: "", event_ref: "", risk_instance_ref: "" },
        "timeline",
      ) };
    } catch (error) {
      return { ok: false, error: String((error && error.stack) || error) };
    }
  })(),
};
