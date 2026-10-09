// W01-R26 A12/A13 render fixture. Bundled by
// medicalMonitoringFindingCardRender.test.mjs via esbuild (single React
// copy). Exports static markup strings only; the runner asserts the
// finding-card jump targets (finding → event anchor → source locator),
// claims分类与时间窗/状态字段，以及零发现显式空集与旧形态draft如实呈现。
import { renderToStaticMarkup } from "react-dom/server";
import { QueryWorkspaceView } from "./MedicalMonitoringWorkspace.jsx";
import { buildFindingCards } from "./MedicalMonitoringProductLoop.jsx";

const findingCard = {
  findingId: "finding-001",
  riskId: "risk-001",
  subjectRef: "s7-subject-06021",
  siteRef: "s7-site-006",
  scopeKind: "subject",
  eventRef: "s7-event-001",
  windowStart: "2026-01-01",
  windowEnd: "2026-03-31",
  findingState: "open",
  claims: [
    { kind: "basis", text: "依据：方案要求报告不良事件。" },
    { kind: "finding", text: "发现：受试者出现未记录的不良反应。" },
    { kind: "action", text: "行动项：请核实并补录。" },
  ],
  sourceRefs: [{ evidenceId: "ev-listing-001", path: "AE.AETERM", recordId: "rec-001", field: "AETERM" }],
  locator: { path: "AE.AETERM", recordId: "rec-001", field: "AETERM" },
  dataCutoff: "2026-03-31",
  sourceRevisionId: "rev-1",
};

const queryDraft = {
  queryDraftId: "qd-001",
  findingId: "finding-001",
  subjectRef: "s7-subject-06021",
  siteRef: "s7-site-006",
  displayText: "依据：x发现：y行动项：z",
  draftState: "draft",
};

const baseProjection = {
  subjects: [],
  currentRisks: [],
  aiQueryFindings: [],
  domains: [],
  temporalSpine: {},
  aggregation: null,
};

// R28-09回归夹具：走真实 buildFindingCards 管线的原始Finding DTO——
// claim源文本自带kind前缀、结构化事件/时间窗字段为空而依据段绑定具体
// 事件、来源路径为facts.<domain>内部形态、受试者为裸ref（带可用标签）。
const r28RawDto = {
  finding_id: "finding-r28-001",
  risk_instance_id: "riski-r28-001",
  subject_ref: "s7-subject-06021",
  site_ref: "s7-site-006",
  scope_kind: "subject",
  event_ref: "",
  window_start: "",
  window_end: "",
  finding_state: "open",
  claims: [
    { kind: "basis", text: "依据：2026-06-12「发热」事件与2026-06-10化验记录交叉提示需核实。" },
    { kind: "finding", text: "发现：受试者存在未记录的不良反应。" },
    { kind: "action", text: "行动项：请核实并补录。" },
  ],
  source_refs: [
    { evidence_id: "ev-r28-001", path: "facts.ae", record_id: "event-AE-000001", field: "AETERM" },
  ],
};

function viewWithSubjects(projection) {
  return renderToStaticMarkup(
    <QueryWorkspaceView
      payload={{
        publicResultContext: true,
        projection: {
          ...baseProjection,
          subjects: [{ subject_ref: "s7-subject-06021", subject_label: "021号受试者", site_ref: "s7-site-006" }],
          domains: [{ domain: "ae", shortLabel: "不良事件" }],
          ...projection,
        },
      }}
      route={{ view: "queries" }}
      onSubjectSelect={() => {}}
      onSource={() => {}}
      onFindingSelect={() => {}}
      onBack={() => {}}
    />,
  );
}

function view({ findingCards, queryDraftRows, queryFindingsMeta }) {
  return renderToStaticMarkup(
    <QueryWorkspaceView
      payload={{
        publicResultContext: true,
        projection: {
          ...baseProjection,
          findingCards,
          queryDraftRows,
          queryFindingsMeta,
        },
      }}
      route={{ view: "queries" }}
      onSubjectSelect={() => {}}
      onSource={() => {}}
      onFindingSelect={() => {}}
      onBack={() => {}}
    />,
  );
}

export const renders = {
  findingCard: view({
    findingCards: [findingCard],
    queryDraftRows: [queryDraft],
    queryFindingsMeta: {
      shape: "finding_dto_v1",
      state: "completed_with_findings",
      total: 1,
      gaps: 0,
      queryDrafts: [queryDraft],
    },
  }),
  empty: view({
    findingCards: [],
    queryDraftRows: [],
    queryFindingsMeta: {
      shape: "finding_dto_v1",
      state: "completed_no_findings",
      total: 0,
      gaps: 0,
      queryDrafts: [],
    },
  }),
  legacy: view({
    findingCards: [],
    queryDraftRows: [
      { queryDraftId: "qd-legacy-001", findingId: "finding-legacy", displayText: "旧载荷草稿", draftState: "draft" },
    ],
    queryFindingsMeta: {
      shape: "legacy_query_drafts",
      state: "completed_no_findings",
      total: 0,
      gaps: 0,
      queryDrafts: [
        { queryDraftId: "qd-legacy-001", findingId: "finding-legacy", displayText: "旧载荷草稿", draftState: "draft" },
      ],
    },
  }),
  // R28-09：真实管线（原始DTO→buildFindingCards→渲染）的发现卡。
  r28FindingCard: viewWithSubjects({
    findingCards: buildFindingCards({ query_findings: [r28RawDto] }),
    queryDraftRows: [],
    queryFindingsMeta: {
      shape: "finding_dto_v1",
      state: "completed_with_findings",
      total: 1,
      gaps: 0,
      queryDrafts: [],
    },
  }),
};
