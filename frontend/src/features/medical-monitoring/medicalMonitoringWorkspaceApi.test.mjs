import assert from "node:assert/strict";
import {
  createMedicalMonitoringWorkspaceApi,
  computeMedicalMonitoringWorkspaceResponseDigest,
  MedicalMonitoringWorkspaceApiError,
} from "./medicalMonitoringWorkspaceApi.mjs";
import {
  WORKSPACE_SYNTHETIC_IDENTITY_NEGATIVE,
  WORKSPACE_SYNTHETIC_OVERVIEW,
  WORKSPACE_SYNTHETIC_SITE_OVERVIEW,
  WORKSPACE_SYNTHETIC_SOURCE_EVIDENCE,
  WORKSPACE_SYNTHETIC_SUBJECT_WORKSPACE,
} from "./medicalMonitoringProductFixtures.mjs";

let passed = 0;
function check(condition, message) {
  assert.ok(condition, message);
  passed += 1;
}

function jsonResponse(body, status = 200) {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "content-type": "application/json" },
  });
}

async function rebindResponseDigest(payload) {
  const next = structuredClone(payload);
  next.response_snapshot_sha256 = "";
  next.identity.response_snapshot_sha256 = "";
  next.read_handoff.response_snapshot_sha256 = "";
  const digest = await computeMedicalMonitoringWorkspaceResponseDigest(next);
  next.response_snapshot_sha256 = digest;
  next.identity.response_snapshot_sha256 = digest;
  next.read_handoff.response_snapshot_sha256 = digest;
  return next;
}

const calls = [];
const adapter = createMedicalMonitoringWorkspaceApi({
  baseUrl: "http://workbench.test",
  fetchImpl: async (url, options) => {
    calls.push({ url, options });
    if (url.includes("source-evidence")) return jsonResponse(WORKSPACE_SYNTHETIC_SOURCE_EVIDENCE);
    if (url.includes("subject-workspaces")) return jsonResponse(WORKSPACE_SYNTHETIC_SUBJECT_WORKSPACE);
    return jsonResponse(WORKSPACE_SYNTHETIC_OVERVIEW);
  },
});

await adapter.getOverview({ projectId: "synthetic-project-r5-s7" });
await adapter.getSubjectWorkspace({
  projectId: "synthetic-project-r5-s7",
  subjectId: "synthetic-subject-001",
  runRef: "synthetic-run-r5-20260820",
  snapshotRef: "synthetic-snapshot-r5-20260820",
  cutoffRef: "2026-08-20",
  siteRef: "synthetic-site-01",
  spineRef: "synthetic-spine-001",
  windowStart: "2026-01-01",
  windowEnd: "2026-08-20",
  riskInstanceRef: "synthetic-risk-instance-ae-01",
  riskAnchorRef: "synthetic-anchor-ae-01",
  visitRef: "synthetic-visit-04",
  eventRef: "synthetic-event-ae-01",
});
await adapter.getSourceEvidence({
  projectId: "synthetic-project-r5-s7",
  runRef: "synthetic-run-r5-20260820",
  snapshotRef: "synthetic-snapshot-r5-20260820",
  cutoffRef: "2026-08-20",
  riskInstanceRef: "synthetic-risk-instance-ae-01",
  sourceLocatorRef: "synthetic-locator-ae-01",
});

check(calls.length === 3, "uses one request for each declared R5 read surface");
check(calls.every((call) => call.options.method === "GET"), "all 医学监查数据适配器 requests use GET");
check(calls.every((call) => call.options.body === undefined), "医学监查数据适配器 requests have no body");
check(calls.every((call) => call.options.headers.Accept === "application/json"), "医学监查数据适配器 requests accept JSON");
check(calls[0].url === "http://workbench.test/api/projects/synthetic-project-r5-s7/modules/medical-monitoring/r5/overview", "uses the declared overview path");
const subjectUrl = new URL(calls[1].url);
check(subjectUrl.pathname.endsWith("/subject-workspaces/synthetic-subject-001"), "uses the declared subject workspace path");
check(subjectUrl.searchParams.get("spine_ref") === "synthetic-spine-001", "passes the temporal spine identity");
check(subjectUrl.searchParams.get("window_start") === "2026-01-01" && subjectUrl.searchParams.get("window_end") === "2026-08-20", "passes the exact window");
const evidenceUrl = new URL(calls[2].url);
check(evidenceUrl.searchParams.get("source_locator_ref") === "synthetic-locator-ae-01", "passes the exact source locator");

const overview = await adapter.getOverview({ projectId: "synthetic-project-r5-s7" });
check(overview.publicIdentity.projectRef === "synthetic-project-r5-s7", "keeps the verified project identity");
check(overview.projection.currentRisks.length === 2, "preserves current high and medium risk entries");
check(overview.projection.centers.length === 2, "normalizes the canonical center_map.cells object");
check(overview.counts.currentRisk.high === 1 && overview.counts.currentRisk.medium === 1, "consumes authoritative separate risk counts");
check(overview.counts.changeBand === 2, "consumes the backend authoritative change-band count");
check(overview.projection.domains.length === 8, "preserves all eight domain encodings");
check(overview.projection.currentRisks[0].severityLabel === "紧急" || overview.projection.currentRisks[0].severityLabel === "高" || overview.projection.currentRisks[0].severityLabel === "中", "maps severity to the Chinese projection");
check(overview.projection.currentRisks[0].domainEncoding.shape, "maps an event shape without calculating a risk");

let derivedChangeBand = null;
try {
  const changedRows = await rebindResponseDigest({
    ...WORKSPACE_SYNTHETIC_OVERVIEW,
    projection: { ...WORKSPACE_SYNTHETIC_OVERVIEW.projection, change_bands: [] },
  });
  const changedRowsAdapter = createMedicalMonitoringWorkspaceApi({ fetchImpl: async () => jsonResponse(changedRows) });
  derivedChangeBand = await changedRowsAdapter.getOverview({ projectId: "synthetic-project-r5-s7" });
} catch (error) {
  derivedChangeBand = error;
}
check(derivedChangeBand?.counts?.changeBand === 2, "does not derive change-band count from projection rows");

const siteCalls = [];
const siteAdapter = createMedicalMonitoringWorkspaceApi({
  baseUrl: "http://workbench.test",
  fetchImpl: async (url, options) => {
    siteCalls.push({ url, options });
    return jsonResponse(WORKSPACE_SYNTHETIC_SITE_OVERVIEW);
  },
});
const siteOverview = await siteAdapter.getOverview({ projectId: "synthetic-project-r5-s7", siteRef: "synthetic-site-01" });
const siteUrl = new URL(siteCalls[0].url);
check(siteUrl.searchParams.get("site_ref") === "synthetic-site-01", "passes the exact site_ref through the overview GET query");
check(siteOverview.publicIdentity.siteRef === "synthetic-site-01", "binds site_overview to the expected response identity");

let siteIdentityError = null;
try {
  const mismatchedSite = await rebindResponseDigest({
    ...WORKSPACE_SYNTHETIC_SITE_OVERVIEW,
    identity: { ...WORKSPACE_SYNTHETIC_SITE_OVERVIEW.identity, site_ref: "synthetic-site-02" },
  });
  const mismatchedSiteAdapter = createMedicalMonitoringWorkspaceApi({ fetchImpl: async () => jsonResponse(mismatchedSite) });
  await mismatchedSiteAdapter.getOverview({ projectId: "synthetic-project-r5-s7", siteRef: "synthetic-site-01" });
} catch (error) {
  siteIdentityError = error;
}
check(siteIdentityError?.code === "IDENTITY_TARGET_MISMATCH", "fails closed when site_overview response identity mismatches site_ref");

let identityError = null;
try {
  const negative = createMedicalMonitoringWorkspaceApi({ fetchImpl: async () => jsonResponse(WORKSPACE_SYNTHETIC_IDENTITY_NEGATIVE) });
  await negative.getOverview({ projectId: "synthetic-project-r5-s7" });
} catch (error) {
  identityError = error;
}
check(identityError instanceof MedicalMonitoringWorkspaceApiError, "rejects an identity mismatch with a typed error");
check(identityError.code === "IDENTITY_PROJECT_MISMATCH", "distinguishes a project identity mismatch");

let digestError = null;
try {
  const broken = {
    ...WORKSPACE_SYNTHETIC_OVERVIEW,
    projection: {
      ...WORKSPACE_SYNTHETIC_OVERVIEW.projection,
      project: { ...WORKSPACE_SYNTHETIC_OVERVIEW.projection.project, project_label: "tampered" },
    },
  };
  const digestAdapter = createMedicalMonitoringWorkspaceApi({ fetchImpl: async () => jsonResponse(broken) });
  await digestAdapter.getOverview({ projectId: "synthetic-project-r5-s7" });
} catch (error) {
  digestError = error;
}
check(digestError?.code === "RESPONSE_DIGEST_MISMATCH", "rejects payload tamper against the backend canonical response digest");

let handoffDigestError = null;
try {
  const brokenHandoff = { ...WORKSPACE_SYNTHETIC_OVERVIEW, read_handoff: { ...WORKSPACE_SYNTHETIC_OVERVIEW.read_handoff, response_snapshot_sha256: "f".repeat(64) } };
  const handoffAdapter = createMedicalMonitoringWorkspaceApi({ fetchImpl: async () => jsonResponse(brokenHandoff) });
  await handoffAdapter.getOverview({ projectId: "synthetic-project-r5-s7" });
} catch (error) {
  handoffDigestError = error;
}
check(handoffDigestError?.code === "DIGEST_HANDOFF_MISMATCH", "rejects a handoff tamper before accepting the envelope");

let emptyRunError = null;
try {
  const emptyRun = await rebindResponseDigest({
    ...WORKSPACE_SYNTHETIC_OVERVIEW,
    identity: { ...WORKSPACE_SYNTHETIC_OVERVIEW.identity, run_ref: "" },
    authority_receipt: { ...WORKSPACE_SYNTHETIC_OVERVIEW.authority_receipt, run_ref: "" },
  });
  const emptyRunAdapter = createMedicalMonitoringWorkspaceApi({ fetchImpl: async () => jsonResponse(emptyRun) });
  await emptyRunAdapter.getOverview({ projectId: "synthetic-project-r5-s7" });
} catch (error) {
  emptyRunError = error;
}
check(emptyRunError?.code === "REQUIRED_STRING_MISSING", "rejects an empty required identity run_ref");

let domainEncodingError = null;
try {
  const missingEncoding = await rebindResponseDigest({
    ...WORKSPACE_SYNTHETIC_OVERVIEW,
    projection: {
      ...WORKSPACE_SYNTHETIC_OVERVIEW.projection,
      domain_encoding: WORKSPACE_SYNTHETIC_OVERVIEW.projection.domain_encoding.map((domain, index) => index === 0 ? { ...domain, event_shape: "" } : domain),
    },
  });
  const domainAdapter = createMedicalMonitoringWorkspaceApi({ fetchImpl: async () => jsonResponse(missingEncoding) });
  await domainAdapter.getOverview({ projectId: "synthetic-project-r5-s7" });
} catch (error) {
  domainEncodingError = error;
}
check(domainEncodingError?.code === "REQUIRED_STRING_MISSING", "rejects a missing required domain encoding field");

let riskDomainError = null;
try {
  const missingRiskDomain = await rebindResponseDigest({
    ...WORKSPACE_SYNTHETIC_SUBJECT_WORKSPACE,
    projection: {
      ...WORKSPACE_SYNTHETIC_SUBJECT_WORKSPACE.projection,
      risk_anchors: [{ ...WORKSPACE_SYNTHETIC_SUBJECT_WORKSPACE.projection.risk_anchors[0], domain: "" }],
    },
  });
  const riskDomainAdapter = createMedicalMonitoringWorkspaceApi({ fetchImpl: async () => jsonResponse(missingRiskDomain) });
  await riskDomainAdapter.getSubjectWorkspace({
    projectId: "synthetic-project-r5-s7",
    subjectId: "synthetic-subject-001",
    runRef: "synthetic-run-r5-20260820",
    snapshotRef: "synthetic-snapshot-r5-20260820",
    cutoffRef: "2026-08-20",
    siteRef: "synthetic-site-01",
    spineRef: "synthetic-spine-001",
    windowStart: "2026-01-01",
    windowEnd: "2026-08-20",
  });
} catch (error) {
  riskDomainError = error;
}
check(riskDomainError?.code === "REQUIRED_STRING_MISSING", "rejects a current-risk row with no domain reference");

let missingCurrentRisksError = null;
try {
  const missingCurrentRisks = structuredClone(WORKSPACE_SYNTHETIC_OVERVIEW);
  delete missingCurrentRisks.projection.current_risks;
  const missingCurrentRisksBound = await rebindResponseDigest(missingCurrentRisks);
  const missingCurrentRisksAdapter = createMedicalMonitoringWorkspaceApi({ fetchImpl: async () => jsonResponse(missingCurrentRisksBound) });
  await missingCurrentRisksAdapter.getOverview({ projectId: "synthetic-project-r5-s7" });
} catch (error) {
  missingCurrentRisksError = error;
}
check(missingCurrentRisksError?.code === "CURRENT_RISKS_REQUIRED", "rejects a missing authoritative current_risks projection after digest rebinding");

let emptyCurrentRisksError = null;
try {
  const emptyCurrentRisks = await rebindResponseDigest({
    ...WORKSPACE_SYNTHETIC_OVERVIEW,
    projection: { ...WORKSPACE_SYNTHETIC_OVERVIEW.projection, current_risks: [] },
  });
  const emptyCurrentRisksAdapter = createMedicalMonitoringWorkspaceApi({ fetchImpl: async () => jsonResponse(emptyCurrentRisks) });
  await emptyCurrentRisksAdapter.getOverview({ projectId: "synthetic-project-r5-s7" });
} catch (error) {
  emptyCurrentRisksError = error;
}
check(emptyCurrentRisksError?.code === "CURRENT_RISKS_REQUIRED", "rejects an empty authoritative current_risks projection after digest rebinding");

let subjectCurrentRisksError = null;
try {
  const emptySubjectRisks = await rebindResponseDigest({
    ...WORKSPACE_SYNTHETIC_SUBJECT_WORKSPACE,
    projection: { ...WORKSPACE_SYNTHETIC_SUBJECT_WORKSPACE.projection, current_risks: [] },
  });
  const emptySubjectRisksAdapter = createMedicalMonitoringWorkspaceApi({ fetchImpl: async () => jsonResponse(emptySubjectRisks) });
  await emptySubjectRisksAdapter.getSubjectWorkspace({
    projectId: "synthetic-project-r5-s7",
    subjectId: "synthetic-subject-001",
    runRef: "synthetic-run-r5-20260820",
    snapshotRef: "synthetic-snapshot-r5-20260820",
    cutoffRef: "2026-08-20",
    siteRef: "synthetic-site-01",
    spineRef: "synthetic-spine-001",
    windowStart: "2026-01-01",
    windowEnd: "2026-08-20",
  });
} catch (error) {
  subjectCurrentRisksError = error;
}
check(subjectCurrentRisksError?.code === "CURRENT_RISKS_REQUIRED", "rejects an empty subject current_risks projection after digest rebinding");

const subject = await adapter.getSubjectWorkspace({
  projectId: "synthetic-project-r5-s7",
  subjectId: "synthetic-subject-001",
  runRef: "synthetic-run-r5-20260820",
  snapshotRef: "synthetic-snapshot-r5-20260820",
  cutoffRef: "2026-08-20",
  siteRef: "synthetic-site-01",
  spineRef: "synthetic-spine-001",
  windowStart: "2026-01-01",
  windowEnd: "2026-08-20",
});
check(subject.projection.currentRisks.length === 2, "maps subject risk_anchors into current-risk rows");
check(subject.projection.riskAnchors.length === 2 && subject.projection.currentRisks[0].riskInstanceRef, "keeps the selected risk anchor in the canonical inspector model");
check(subject.projection.indicators.length === 2, "consumes authoritative indicator trends when present");

const noIndicatorEnvelope = structuredClone(WORKSPACE_SYNTHETIC_SUBJECT_WORKSPACE);
delete noIndicatorEnvelope.projection.indicators;
const noIndicatorBound = await rebindResponseDigest(noIndicatorEnvelope);
const noIndicatorAdapter = createMedicalMonitoringWorkspaceApi({ fetchImpl: async () => jsonResponse(noIndicatorBound) });
const unavailableIndicators = await noIndicatorAdapter.getSubjectWorkspace({
  projectId: "synthetic-project-r5-s7",
  subjectId: "synthetic-subject-001",
  runRef: "synthetic-run-r5-20260820",
  snapshotRef: "synthetic-snapshot-r5-20260820",
  cutoffRef: "2026-08-20",
  siteRef: "synthetic-site-01",
  spineRef: "synthetic-spine-001",
  windowStart: "2026-01-01",
  windowEnd: "2026-08-20",
});
check(unavailableIndicators.projection.indicators === null, "keeps an absent backend indicator surface explicitly unavailable");

const evidence = await adapter.getSourceEvidence({
  projectId: "synthetic-project-r5-s7",
  runRef: "synthetic-run-r5-20260820",
  snapshotRef: "synthetic-snapshot-r5-20260820",
  cutoffRef: "2026-08-20",
  riskInstanceRef: "synthetic-risk-instance-ae-01",
  sourceLocatorRef: "synthetic-locator-ae-01",
});
check(evidence.projection.domains.length === 0, "does not require an irrelevant eight-domain registry for source evidence");
check(evidence.projection.sourceEvidence.excerpt && evidence.projection.sourceEvidence.riskInstanceRef === "synthetic-risk-instance-ae-01", "validates and exposes exact backend source-evidence fields");

let sourceEvidenceTamperError = null;
try {
  const tamperedEvidence = await rebindResponseDigest({
    ...WORKSPACE_SYNTHETIC_SOURCE_EVIDENCE,
    projection: {
      ...WORKSPACE_SYNTHETIC_SOURCE_EVIDENCE.projection,
      evidence: { ...WORKSPACE_SYNTHETIC_SOURCE_EVIDENCE.projection.evidence, excerpt: "tampered" },
    },
  });
  const tamperedEvidenceAdapter = createMedicalMonitoringWorkspaceApi({ fetchImpl: async () => jsonResponse(tamperedEvidence) });
  await tamperedEvidenceAdapter.getSourceEvidence({
    projectId: "synthetic-project-r5-s7",
    runRef: "synthetic-run-r5-20260820",
    snapshotRef: "synthetic-snapshot-r5-20260820",
    cutoffRef: "2026-08-20",
    riskInstanceRef: "synthetic-risk-instance-ae-01",
    sourceLocatorRef: "synthetic-locator-ae-01",
  });
} catch (error) {
  sourceEvidenceTamperError = error;
}
check(sourceEvidenceTamperError?.code === "SOURCE_EVIDENCE_SOURCE_MISMATCH", "rejects source-evidence field tamper even after response digest rebinding");

let unknownOptionError = null;
try {
  await adapter.getOverview({ projectId: "synthetic-project-r5-s7", debug: "1" });
} catch (error) {
  unknownOptionError = error;
}
check(unknownOptionError?.code === "QUERY_OPTION_INVALID", "rejects unknown adapter options");

let noFallbackError = null;
const failedCalls = [];
try {
  const failedAdapter = createMedicalMonitoringWorkspaceApi({ fetchImpl: async (url) => { failedCalls.push(url); return jsonResponse({ detail: "unavailable" }, 503); } });
  await failedAdapter.getOverview({ projectId: "synthetic-project-r5-s7" });
} catch (error) {
  noFallbackError = error;
}
check(noFallbackError?.code === "HTTP_READ_FAILED", "surfaces a failed R5 read instead of degrading");
check(failedCalls.length === 1, "does not call a legacy fallback after a failed R5 read");

const flowStageEntry = (stageRef, label, columnOrder, rowOrder, stageKind, isEntry, isTerminal, reached, current, risk) => ({
  stage_ref: stageRef,
  stage_label_zh: label,
  column_order: columnOrder,
  row_order: rowOrder,
  stage_kind: stageKind,
  is_entry: isEntry,
  is_terminal: isTerminal,
  source_locator_refs: [],
  reached_count: reached,
  current_count: current,
  current_mid_high_risk_count: risk,
});

const flowLinkEntry = (linkRef, from, to, count, risk) => ({
  link_ref: linkRef,
  from_stage_ref: from,
  to_stage_ref: to,
  count,
  current_mid_high_risk_count: risk,
});

function subjectFlowFixture({ siteRef = "", scopeProjectRef = "synthetic-project-r5-s7", ...overrides } = {}) {
  const rowSite = (site) => siteRef || site;
  const stage = flowStageEntry;
  const link = flowLinkEntry;
  const row = (subjectRef, site, currentStage, priorStage, fields = {}) => ({
    subject_ref: subjectRef,
    site_ref: rowSite(site),
    subject_label: `受试者 ${subjectRef.slice(-2)}`,
    site_label: "示范中心",
    spine_ref: fields.noSpine ? "" : `spine-${subjectRef}`,
    current_stage_ref: currentStage,
    prior_stage_ref: priorStage,
    entered_date: fields.partialPath ? "" : "2026-02-01",
    basis_date: fields.partialPath ? "" : "2026-02-01",
    date_state: fields.partialPath ? "missing" : "exact",
    transition_reason_zh: fields.partialPath ? "既往阶段数据未提供" : "本次监查确认",
    stage_change_kind: fields.stageChange || "initial",
    risk_change_kind: fields.riskChange || "",
    risk_summary_zh: fields.risk ? "高风险 1 项：不良事件记录需核对" : "",
    current_mid_high_risk: Boolean(fields.risk),
    path_state: fields.partialPath ? "partial" : "complete",
    jump_window_start: fields.noWindow ? "" : "2026-01-05",
    jump_window_end: fields.noWindow ? "" : "2026-08-18",
  });
  return {
    availability: "available",
    visual_kind: "path_throughput_sankey",
    scope: {
      project_ref: scopeProjectRef,
      run_ref: "synthetic-run-r5-20260820",
      snapshot_ref: "synthetic-snapshot-r5-20260820",
      cutoff_ref: "2026-08-20",
      site_ref: siteRef,
    },
    stages: [
      stage("flow-stage-consent", "已签署知情同意", 0, 0, "main", true, false, 12, 0, 0),
      stage("flow-stage-screening", "筛选", 1, 0, "main", false, false, 12, 0, 0),
      stage("flow-stage-treatment", "治疗中", 2, 0, "main", false, false, 10, 5, 2),
      stage("flow-stage-screen-failed", "筛选失败", 2, 1, "branch_terminal", false, true, 2, 2, 1),
      stage("flow-stage-completed", "完成研究", 3, 0, "branch_terminal", false, true, 3, 3, 0),
      stage("flow-stage-discontinued", "永久停药", 3, 1, "branch_terminal", false, true, 2, 2, 0),
    ],
    links: [
      link("flow-link-consent-screening", "flow-stage-consent", "flow-stage-screening", 12, 0),
      link("flow-link-screening-treatment", "flow-stage-screening", "flow-stage-treatment", 10, 1),
      link("flow-link-screening-failed", "flow-stage-screening", "flow-stage-screen-failed", 2, 0),
      link("flow-link-treatment-completed", "flow-stage-treatment", "flow-stage-completed", 3, 0),
      link("flow-link-treatment-discontinued", "flow-stage-treatment", "flow-stage-discontinued", 2, 0),
    ],
    subjects: [
      row("synthetic-subject-101", "synthetic-site-01", "flow-stage-screen-failed", "flow-stage-screening", { risk: true, riskChange: "new" }),
      row("synthetic-subject-102", "synthetic-site-02", "flow-stage-screen-failed", "flow-stage-screening"),
      row("synthetic-subject-103", "synthetic-site-01", "flow-stage-treatment", "flow-stage-screening", { risk: true, riskChange: "upgraded", stageChange: "returned" }),
      row("synthetic-subject-104", "synthetic-site-01", "flow-stage-treatment", "flow-stage-screening", { stageChange: "advanced" }),
      row("synthetic-subject-105", "synthetic-site-02", "flow-stage-treatment", "flow-stage-screening", { risk: true, riskChange: "continued" }),
      row("synthetic-subject-106", "synthetic-site-02", "flow-stage-treatment", "flow-stage-screening", { partialPath: true }),
      row("synthetic-subject-107", "synthetic-site-02", "flow-stage-treatment", "flow-stage-screening"),
      row("synthetic-subject-108", "synthetic-site-01", "flow-stage-completed", "flow-stage-treatment", { stageChange: "advanced" }),
      row("synthetic-subject-109", "synthetic-site-02", "flow-stage-completed", "flow-stage-treatment", { stageChange: "advanced" }),
      row("synthetic-subject-110", "synthetic-site-02", "flow-stage-completed", "flow-stage-treatment", { stageChange: "advanced" }),
      row("synthetic-subject-111", "synthetic-site-01", "flow-stage-discontinued", "flow-stage-treatment", { noWindow: true, stageChange: "returned" }),
      row("synthetic-subject-112", "synthetic-site-01", "flow-stage-discontinued", "flow-stage-treatment", { noWindow: true, noSpine: true, stageChange: "returned" }),
    ],
    coverage: { complete: 11, partial: 1, conflicted: 0, not_provided: 0, not_applicable: 0 },
    reconciliation: {
      state: "matched",
      total_subject_count: 12,
      entry_count: 12,
      current_stay_count: 12,
      detail_count: 12,
      node_conservation_matched: true,
      link_conservation_matched: true,
    },
    ...overrides,
  };
}

async function overviewWithSubjectFlow(subjectFlow, { siteScope = false, identityOverrides = {} } = {}) {
  const base = siteScope ? WORKSPACE_SYNTHETIC_SITE_OVERVIEW : WORKSPACE_SYNTHETIC_OVERVIEW;
  const bound = await rebindResponseDigest({
    ...base,
    identity: { ...base.identity, ...identityOverrides },
    projection: { ...base.projection, subject_flow: subjectFlow },
  });
  const flowAdapter = createMedicalMonitoringWorkspaceApi({ fetchImpl: async () => jsonResponse(bound) });
  return flowAdapter.getOverview({
    projectId: "synthetic-project-r5-s7",
    ...(siteScope ? { siteRef: "synthetic-site-01" } : {}),
  });
}

check(overview.projection.subjectFlow === null, "keeps an overview without subject_flow explicitly flow-free");
check(subject.projection.subjectFlow === null, "keeps the subject workspace free of a subject_flow projection");

const flowOverview = await overviewWithSubjectFlow(subjectFlowFixture());
check(flowOverview.projection.subjectFlow.availability === "available", "normalizes the matched subject_flow form");
check(flowOverview.projection.subjectFlow.visualKind === "path_throughput_sankey", "freezes the path-throughput visual surface");
check(flowOverview.projection.subjectFlow.scope.projectRef === "synthetic-project-r5-s7" && flowOverview.projection.subjectFlow.scope.siteRef === "", "binds the project scope to the response identity");
check(flowOverview.projection.subjectFlow.stages.length === 6 && flowOverview.projection.subjectFlow.links.length === 5, "carries the declared stage catalog and canonical links");
check(flowOverview.projection.subjectFlow.subjects.length === 12, "carries one detail row per scoped subject");
const flowTreatment = flowOverview.projection.subjectFlow.stages.find((stage) => stage.stageRef === "flow-stage-treatment");
check(flowTreatment.stageLabelZh === "治疗中" && flowTreatment.reachedCount === 10 && flowTreatment.currentCount === 5 && flowTreatment.currentMidHighRiskCount === 2, "exposes node reached/current/risk counts with the Chinese stage label");
const flowSubjects = flowOverview.projection.subjectFlow.subjects;
check(flowSubjects[0].stageChangeLabel === "首次记录" && flowSubjects[2].stageChangeLabel === "阶段退回", "maps stage change kinds to the frozen Chinese labels");
check(flowSubjects[2].riskChangeLabel === "升级" && flowSubjects[4].riskChangeLabel === "持续", "maps risk change kinds through the existing change registry");
check(flowSubjects.filter((row) => row.jumpWindowAvailable).length === 10, "enables the journey jump only for rows with a closed non-empty window");
check(flowSubjects[10].jumpWindowAvailable === false && flowSubjects[11].spineRef === "", "keeps date-less rows present with the jump disabled");

const siteFlowOverview = await overviewWithSubjectFlow(subjectFlowFixture({ siteRef: "synthetic-site-01" }), { siteScope: true });
check(siteFlowOverview.projection.subjectFlow.scope.siteRef === "synthetic-site-01", "binds the center scope to the site identity");

const notProvidedFlow = await overviewWithSubjectFlow({ availability: "not_provided", reason_zh: "本次数据未提供研究状态" });
check(notProvidedFlow.projection.subjectFlow.availability === "not_provided" && notProvidedFlow.projection.subjectFlow.reasonZh === "本次数据未提供研究状态", "normalizes the not-provided form with its Chinese reason");
check(notProvidedFlow.projection.subjectFlow.stages.length === 0 && notProvidedFlow.projection.subjectFlow.subjects.length === 0, "keeps the not-provided form free of nodes and rows");

const blockedFlow = await overviewWithSubjectFlow(subjectFlowFixture({
  reconciliation: { state: "blocked", gap_zh: "阶段人数与受试者明细不一致，请检查本次数据范围。" },
}));
check(blockedFlow.projection.subjectFlow.reconciliation.state === "blocked" && blockedFlow.projection.subjectFlow.blockedReasonZh.includes("不一致"), "normalizes the blocked form with its Chinese gap");
check(blockedFlow.projection.subjectFlow.stages.length === 0 && blockedFlow.projection.subjectFlow.links.length === 0, "keeps the blocked form free of a contradictory chart");

async function subjectFlowError(subjectFlow, expectedCode, label, identityOverrides = {}) {
  let error = null;
  try {
    await overviewWithSubjectFlow(subjectFlow, { identityOverrides });
  } catch (caught) {
    error = caught;
  }
  check(error?.code === expectedCode, label);
  return error;
}

await subjectFlowError({ availability: "partially_available" }, "SUBJECT_FLOW_AVAILABILITY_INVALID", "rejects a subject_flow availability outside the closed registry");
await subjectFlowError({ availability: "not_provided" }, "SUBJECT_FLOW_REASON_MISSING", "rejects a not-provided form without its Chinese reason");
await subjectFlowError(subjectFlowFixture({ scopeProjectRef: "synthetic-project-other" }), "SUBJECT_FLOW_IDENTITY_MISMATCH", "rejects a subject_flow scope outside the response identity");
await subjectFlowError(subjectFlowFixture({ reconciliation: { state: "blocked" } }), "SUBJECT_FLOW_GAP_MISSING", "rejects a blocked form without a Chinese gap explanation");
await subjectFlowError({ ...subjectFlowFixture(), visual_kind: "state_count_bars" }, "SUBJECT_FLOW_FIELD_INVALID", "rejects a visual kind outside the frozen surface");
await subjectFlowError(subjectFlowFixture({
  stages: [
    flowStageEntry("flow-stage-consent", "已签署知情同意", 0, 0, "main", true, false, 12, 0, 0),
    flowStageEntry("flow-stage-consent", "已签署知情同意", 0, 1, "main", true, false, 12, 0, 0),
  ],
}), "SUBJECT_FLOW_REF_DUPLICATE", "rejects a duplicated stage ref");
await subjectFlowError({
  ...subjectFlowFixture(),
  links: [flowLinkEntry("flow-link-ghost", "flow-stage-consent", "flow-stage-ghost", 12, 0)],
}, "SUBJECT_FLOW_REF_UNRESOLVED", "rejects a link that references an undeclared stage");
await subjectFlowError(subjectFlowFixture({
  stages: [...subjectFlowFixture().stages.map((item) => item.stage_ref === "flow-stage-treatment" ? { ...item, current_count: 6 } : item)],
}), "SUBJECT_FLOW_RECONCILIATION_MISMATCH", "rejects node counts that do not reconcile with the detail rows");
await subjectFlowError(subjectFlowFixture({
  stages: [...subjectFlowFixture().stages.map((item) => item.stage_ref === "flow-stage-treatment" ? { ...item, current_mid_high_risk_count: 3 } : item)],
}), "SUBJECT_FLOW_RECONCILIATION_MISMATCH", "rejects node risk counts that do not reconcile with the mid-high rows");
await subjectFlowError({
  ...subjectFlowFixture(),
  subjects: subjectFlowFixture().subjects.map((item) => item.subject_ref === "synthetic-subject-101" ? { ...item, jump_window_end: "" } : item),
}, "SUBJECT_FLOW_WINDOW_INVALID", "rejects a half-open journey window");

console.log(`medicalMonitoringWorkspaceApi: ${passed} checks passed`);
