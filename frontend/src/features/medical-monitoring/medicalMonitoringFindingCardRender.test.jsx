// W01-R26 A12/A13 render fixture. Bundled by
// medicalMonitoringFindingCardRender.test.mjs via esbuild (single React
// copy). Exports static markup strings only; the runner asserts the
// finding-card jump targets (finding → event anchor → source locator),
// claims分类与时间窗/状态字段，以及零发现显式空集与旧形态draft如实呈现。
import { renderToStaticMarkup } from "react-dom/server";
import { QueryWorkspaceView } from "./MedicalMonitoringWorkspace.jsx";

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
};
