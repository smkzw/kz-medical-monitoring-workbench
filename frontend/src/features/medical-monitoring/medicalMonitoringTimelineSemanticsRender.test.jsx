// W05-J2 render fixture (A19/A21/A22/A23). Bundled by
// medicalMonitoringTimelineSemanticsRender.test.mjs via esbuild (single
// React copy). Exports static markup strings only; the runner asserts:
// 窗外继续符号与方向读屏文案、partial/待确认区、ongoing/end_unknown开-end
// 视觉、月精度标注，以及全无日期时的明确空态（无月份刻度/无假窗文案）。
import { renderToStaticMarkup } from "react-dom/server";
import { DomainTracks } from "./MedicalMonitoringWorkspace.jsx";

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

const baseProjection = {
  currentRisks: [],
  subjects: [],
  domains,
  temporalSpine: {
    axisMode: "calendar",
    windowStart: "2026-06-01",
    windowEnd: "2026-08-20",
    visits: [],
    pendingDates: [],
  },
  events: [
    {
      eventRef: "ev-beyond-before",
      domain: "ae",
      domainEncoding: domains[0],
      start: "2026-01-05",
      end: null,
      dateState: "exact",
      eventLabel: "窗前不良事件",
      riskAnchorRefs: [],
      sourceLocatorRefs: ["loc-beyond"],
    },
    {
      eventRef: "ev-ongoing",
      domain: "cm",
      domainEncoding: domains[4],
      start: "2026-06-10",
      end: null,
      dateState: "exact",
      ongoing: true,
      eventLabel: "持续用药中",
      riskAnchorRefs: [],
      sourceLocatorRefs: ["loc-ongoing"],
    },
    {
      eventRef: "ev-monthly",
      domain: "lab_exam",
      domainEncoding: domains[3],
      start: "2026-07",
      end: null,
      dateState: "exact",
      eventLabel: "月精度检验",
      riskAnchorRefs: [],
      sourceLocatorRefs: ["loc-monthly"],
    },
  ],
};

function tracks(projection) {
  return renderToStaticMarkup(
    <DomainTracks
      projection={projection}
      timeViewport="fit"
      detailDensity="detailed"
      timeZoom={0}
      selectedEventRef=""
      onEventSelect={() => {}}
    />,
  );
}

export const renders = {
  semantics: tracks(baseProjection),
  empty: tracks({
    currentRisks: [],
    subjects: [],
    domains,
    temporalSpine: {
      axisMode: "calendar",
      windowStart: null,
      windowEnd: null,
      visits: [],
      pendingDates: [],
    },
    events: [
      {
        eventRef: "ev-undated",
        domain: "mh",
        domainEncoding: domains[1],
        start: null,
        end: null,
        dateState: "missing",
        eventLabel: "无日期既往史",
        riskAnchorRefs: [],
        sourceLocatorRefs: [],
      },
    ],
  }),
};
