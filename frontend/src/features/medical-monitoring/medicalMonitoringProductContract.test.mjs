import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const here = path.dirname(fileURLToPath(import.meta.url));
const root = path.resolve(here, "../../../..");
const files = [
  "frontend/src/features/medical-monitoring/MedicalMonitoringWorkspace.jsx",
  "frontend/src/features/medical-monitoring/medicalMonitoringWorkspaceApi.mjs",
  "frontend/src/features/medical-monitoring/medicalMonitoringWorkspaceRouteState.mjs",
  "frontend/src/features/medical-monitoring/medicalMonitoringWorkspace.css",
  "frontend/src/features/medical-monitoring/medicalMonitoringProductFixtures.mjs",
  "frontend/src/features/medical-monitoring/medicalMonitoringJourneyTimeline.mjs",
];
const content = files.map((file) => fs.readFileSync(path.join(root, file), "utf8")).join("\n");
const pageSource = fs.readFileSync(path.join(root, files[0]), "utf8");
const styleSource = fs.readFileSync(path.join(root, files[3]), "utf8");
const contentWithoutSchemaName = content.replaceAll("read-model", "");
const appContent = fs.readFileSync(path.join(root, "frontend/src/App.jsx"), "utf8");
const outletContent = fs.readFileSync(path.join(root, "frontend/src/features/medical-monitoring/MedicalMonitoringRouteOutlet.jsx"), "utf8");
const pageMountCount = outletContent.split("<MedicalMonitoringPage").length - 1;
assert.equal(pageMountCount, 1, "feature outlet mounts one canonical medical-monitoring page");
assert.equal(appContent.includes("<MedicalMonitoringRouteOutlet"), true, "App delegates medical-monitoring rendering to one feature outlet");
const forbiddenProductionTerms = [
  "正式事实",
  "候选信号",
  "已记录事项",
  "通用风险点",
  "待行动",
  "未读",
  "Checklist",
  "medicalMonitoringApi",
  "FormData",
  "provider",
  "model",
  "AI gateway",
];
for (const term of forbiddenProductionTerms) assert.equal(contentWithoutSchemaName.includes(term), false, `production R5 source excludes ${term}`);
for (const term of forbiddenProductionTerms) assert.equal(outletContent.includes(term), false, `product outlet excludes ${term}`);
assert.equal(content.includes('method: "GET"'), true, "adapter declares GET transport");
for (const method of ["POST", "PUT", "PATCH", "DELETE"]) assert.equal(content.includes(`method: "${method}"`), false, `adapter excludes ${method} transport`);
assert.equal(content.includes("fallback"), false, "R5 production source excludes fallback paths");
assert.equal(content.includes("subject-workspaces"), true, "R5 source contains the subject read surface");
assert.equal(content.includes("source-evidence"), true, "R5 source contains the evidence read surface");
assert.equal(content.includes("synthetic-project-r5"), true, "fixtures carry an unmistakable synthetic project identity");
assert.equal(outletContent.includes("WorkspaceComponent"), false, "outlet has no legacy workspace injection path");
assert.equal(outletContent.includes("PatientProfilePage"), false, "outlet has no legacy profile branch");
assert.equal(outletContent.includes("SubjectTimelinePage"), false, "outlet has no legacy timeline branch");
assert.equal(outletContent.includes("fetch("), false, "product outlet has no direct read transport");
assert.equal(content.includes("currentRisksRef.current.find((risk) => risk.riskAnchorRef === riskAnchorRef)"), true, "event selection resolves the risk bound to the selected anchor");
assert.equal(content.includes('risk_instance_ref: linkedRisk?.riskInstanceRef || ""'), true, "event selection clears a stale risk instance when the event has no bound risk");
assert.equal(pageSource.includes("DomainTracks"), true, "subject workspace renders the eight-domain track surface");
assert.equal(pageSource.includes('data-timeline-mode="shared-horizontal"'), true, "patient journey uses a shared horizontal timeline surface");
assert.equal(pageSource.includes("layoutJourneyTimeline"), true, "patient journey lays out events on the shared timeline scale");
assert.equal(pageSource.includes('data-timeline-geometry'), true, "events expose point/interval/pending geometry on the timeline");
assert.equal(pageSource.includes("日期待确认记录"), true, "missing dates are isolated from the dated axis with user-facing copy");
assert.equal(pageSource.includes("EventDetailPanel"), true, "clicking an event opens inspector detail");
assert.equal(pageSource.includes("eventVisitContext"), true, "event detail derives visit context from actual event and visit dates");
// R24V2-U06：泳道概览保留八域chip（零事件域折叠为“无记录”chip仍可见），
// 可访问名同步更新——“首屏八域可见”语义不变。
assert.equal(pageSource.includes("医学事件泳道概览"), true, "all eight lanes are visible in the first-screen journey summary");
assert.equal(pageSource.includes('className={empty ? "monitoring-lane-chip is-empty" : "monitoring-lane-chip"}'), true, "zero-event lanes collapse to an explicit empty chip, not a blank box");
assert.equal(pageSource.includes('sourceLocatorRefs.join("、")'), false, "timeline detail does not expose internal source locator ids");
assert.equal(pageSource.includes('data-monitoring-zoom={zoomLevel}'), true, "page exposes the semantic zoom state to the presentation layer");
assert.equal(pageSource.includes('event.key === "-"'), true, "semantic zoom accepts the minus keyboard shortcut");
assert.equal(pageSource.includes('event.key === "0"'), true, "semantic zoom accepts the reset keyboard shortcut");
assert.equal(pageSource.includes('event.key === "+"'), true, "semantic zoom accepts the plus keyboard shortcut");
assert.equal(pageSource.includes('identity.run_ref || identity.runRef'), true, "identity strip reads the canonical batch reference");
assert.equal(pageSource.includes('identity.snapshot_ref || identity.snapshotRef'), true, "identity strip reads the canonical version reference");
assert.equal(pageSource.includes('data-monitoring-evidence-field="record_ref"'), true, "source evidence visibly exposes the exact record reference");
assert.equal(pageSource.includes('data-monitoring-evidence-field="canonical_location"'), true, "source evidence visibly exposes the exact canonical location");
assert.equal(pageSource.includes('data-monitoring-evidence-field="excerpt"'), true, "source evidence visibly exposes the exact citation excerpt");
assert.equal(pageSource.includes("中高风险逐项显示"), true, "density journey makes the medium/high risk prioritization visible");
assert.equal(pageSource.includes("低风险与常规记录") && pageSource.includes("按缩放级别聚合"), true, "density journey states the low-risk aggregation rule");
assert.equal(pageSource.includes("monitoring-phrase-keep"), true, "density journey keeps 按缩放级别聚合 as an unbreakable phrase");
assert.equal(pageSource.includes("laneChipLabel"), true, "lane chips use balanced soft-break helper to avoid 3+1 orphans");
assert.equal(pageSource.includes("DATE_STATE_CHIPS"), true, "date edge states use short visible chips");
assert.equal(pageSource.includes("共享时间轴</span>"), true, "indicator trend retains the shared temporal window heading");
assert.equal(pageSource.includes("synthetic://"), false, "ordinary source view does not expose synthetic URI text");
assert.equal(styleSource.includes('.monitoring-page[data-monitoring-zoom="-1"]'), true, "compact semantic zoom changes track detail density");
assert.equal(styleSource.includes('.monitoring-page[data-monitoring-zoom="1"] .monitoring-track-event-source'), true, "detailed semantic zoom reveals source locator detail");
assert.equal(styleSource.includes(".monitoring-timeline-canvas"), true, "styles define the shared timeline canvas");
assert.equal(styleSource.includes(".monitoring-pending-date-zone"), true, "styles isolate the pending-date surface");
console.log("medicalMonitoringProductContract: production source checks passed");
