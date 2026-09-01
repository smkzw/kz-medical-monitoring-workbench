import assert from "node:assert/strict";
import {
  MEDICAL_MONITORING_WORKSPACE_CANONICAL_KEYS,
  MEDICAL_MONITORING_WORKSPACE_EPHEMERAL_KEYS,
  normalizeMedicalMonitoringWorkspaceRouteState,
  parseMedicalMonitoringWorkspaceRouteState,
  routeStateForMedicalMonitoringWorkspaceView,
  serializeMedicalMonitoringWorkspaceRouteState,
  splitMedicalMonitoringWorkspaceState,
  validateMedicalMonitoringWorkspaceTarget,
} from "./medicalMonitoringWorkspaceRouteState.mjs";

let passed = 0;
function check(condition, message) {
  assert.ok(condition, message);
  passed += 1;
}

const validSubject = parseMedicalMonitoringWorkspaceRouteState(
  "?project_id=synthetic-project-r5-s7&run_id=synthetic-run-r5-20260820"
    + "&snapshot_id=synthetic-snapshot-r5-20260820&cutoff=2026-08-20"
    + "&scope=subject&site_id=synthetic-site-01&subject_id=synthetic-subject-001"
    + "&view=journey&spine_id=synthetic-spine-001&axis_mode=calendar"
    + "&start=2026-01-01&end=2026-08-20&risk_key=risk-1&risk_instance_id=instance-1"
    + "&risk_anchor_ref=anchor-1&return_context_key=return-1",
);
check(validSubject.isWorkspace && validSubject.valid, "accepts a complete subject deep link");
check(validSubject.canonical.project_ref === "synthetic-project-r5-s7", "maps public project identity");
check(validSubject.canonical.subject_ref === "synthetic-subject-001", "maps public subject identity");
check(validSubject.canonical.cutoff_state === "present", "derives cutoff state only from a present cutoff ref");
check(validSubject.canonical.scope === undefined, "keeps scope out of authority canonical identity");

const serialized = serializeMedicalMonitoringWorkspaceRouteState(validSubject.canonical);
const serializedParams = new URLSearchParams(serialized.slice(1));
check(serializedParams.get("project_id") === "synthetic-project-r5-s7", "serializes project identity");
check(serializedParams.get("subject_id") === "synthetic-subject-001", "serializes subject identity");
check(serializedParams.get("spine_id") === "synthetic-spine-001", "serializes temporal spine identity");
check(serializedParams.get("start") === "2026-01-01" && serializedParams.get("end") === "2026-08-20", "serializes a closed date window");

const unknownQuery = parseMedicalMonitoringWorkspaceRouteState(
  "?project_id=synthetic-project-r5-s7&view=overview&debug=1",
);
check(unknownQuery.isWorkspace && !unknownQuery.valid, "rejects an unknown R5 query key");
check(unknownQuery.errorCode === "UNKNOWN_QUERY_KEY", "returns a distinguished unknown-key failure");

const partialOverview = parseMedicalMonitoringWorkspaceRouteState(
  "?project_id=synthetic-project-r5-s7&view=overview&run_id=run-only",
);
check(!partialOverview.valid && partialOverview.errorCode === "WORKSPACE_IDENTITY_INCOMPLETE", "rejects a partial overview authority identity");

const missingIdentity = parseMedicalMonitoringWorkspaceRouteState(
  "?project_id=synthetic-project-r5-s7&view=journey",
);
check(missingIdentity.isWorkspace && !missingIdentity.valid, "does not enter a subject view without target identity");
check(missingIdentity.errorCode === "WORKSPACE_IDENTITY_INCOMPLETE", "returns a distinguished incomplete-identity failure");

const subjectWithoutReturnContext = parseMedicalMonitoringWorkspaceRouteState(
  "?project_id=synthetic-project-r5-s7&run_id=synthetic-run-r5-20260820"
    + "&snapshot_id=synthetic-snapshot-r5-20260820&cutoff=2026-08-20"
    + "&scope=subject&site_id=synthetic-site-01&subject_id=synthetic-subject-001"
    + "&view=journey&spine_id=synthetic-spine-001&axis_mode=calendar"
    + "&start=2026-01-01&end=2026-08-20",
);
check(subjectWithoutReturnContext.valid, "accepts an exact subject deep link when optional return context is absent");

const legacy = parseMedicalMonitoringWorkspaceRouteState("?project_id=p1&view=checklist");
check(!legacy.isWorkspace && legacy.status === "legacy", "leaves the legacy view outside R5 route handling");

const switched = routeStateForMedicalMonitoringWorkspaceView(validSubject.canonical, "profile");
check(switched.view === "profile" && switched.subject_ref === validSubject.canonical.subject_ref, "keeps subject identity across workspace views");
const evidence = routeStateForMedicalMonitoringWorkspaceView(switched, "evidence", {
  source_locator_ref: "synthetic-locator-ae-01",
});
check(evidence.view === "evidence" && evidence.source_locator_ref === "synthetic-locator-ae-01", "adds an exact source target without changing project identity");
check(evidence.subject_ref === validSubject.canonical.subject_ref && evidence.spine_ref === validSubject.canonical.spine_ref, "keeps subject return context while evidence query remains separately scoped");
const returnedOverview = routeStateForMedicalMonitoringWorkspaceView(validSubject.canonical, "overview");
check(!returnedOverview.site_ref && !returnedOverview.subject_ref && !returnedOverview.spine_ref, "returns to project scope without leaking subject or center identity");
check(returnedOverview.risk_ref === "risk-1" && returnedOverview.risk_instance_ref === "instance-1", "restores the selected risk when an explicit return context exists");
check(returnedOverview.window_start === "2026-01-01" && returnedOverview.window_end === "2026-08-20", "restores the explicit analysis window when returning to project scope");

const split = splitMedicalMonitoringWorkspaceState({ ...validSubject.canonical, inspector_width: 360, focus_ref: "risk-1", scroll_refs: ["risk-list"] });
check(MEDICAL_MONITORING_WORKSPACE_CANONICAL_KEYS.includes("project_ref"), "declares the frozen project identity key");
check(MEDICAL_MONITORING_WORKSPACE_EPHEMERAL_KEYS.includes("inspector_width"), "declares inspector width as ephemeral state");
check(split.ephemeral.inspector_width === 360 && split.ephemeral.focus_ref === "risk-1", "separates ephemeral state from canonical state");
check(!Object.prototype.hasOwnProperty.call(split.canonical, "inspector_width"), "does not put inspector width into canonical state");

const targetCheck = validateMedicalMonitoringWorkspaceTarget(validSubject.canonical);
check(targetCheck.valid, "validates an exact target without nearest substitution");
const invalidTarget = validateMedicalMonitoringWorkspaceTarget({ ...validSubject.canonical, risk_instance_ref: "" });
check(!invalidTarget.valid, "rejects a risk target with an incomplete identity pair");

check(MEDICAL_MONITORING_WORKSPACE_CANONICAL_KEYS.includes("flow_stage_ref")
  && MEDICAL_MONITORING_WORKSPACE_CANONICAL_KEYS.includes("flow_node_metric")
  && MEDICAL_MONITORING_WORKSPACE_CANONICAL_KEYS.includes("flow_link_ref")
  && MEDICAL_MONITORING_WORKSPACE_CANONICAL_KEYS.includes("flow_risk_band"), "declares the frozen flow route keys as canonical identity");

const flowStageQuery = parseMedicalMonitoringWorkspaceRouteState(
  "?project_id=synthetic-project-r5-s7&view=overview&flow_stage_ref=flow-stage-treatment&flow_node_metric=reached",
);
check(flowStageQuery.isWorkspace && flowStageQuery.valid, "accepts a stage flow filter on the project overview");
check(flowStageQuery.canonical.flow_stage_ref === "flow-stage-treatment" && flowStageQuery.canonical.flow_node_metric === "reached", "keeps the reached metric with a stage selection");
check(flowStageQuery.publicQuery.flow_node_metric === "reached", "exposes the flow metric in the public query");

const flowStageDefaultMetric = parseMedicalMonitoringWorkspaceRouteState(
  "?project_id=synthetic-project-r5-s7&view=overview&flow_stage_ref=flow-stage-treatment",
);
check(flowStageDefaultMetric.valid && flowStageDefaultMetric.canonical.flow_node_metric === "current", "defaults the flow metric to current");

const flowLinkQuery = parseMedicalMonitoringWorkspaceRouteState(
  "?project_id=synthetic-project-r5-s7&view=overview&flow_link_ref=flow-link-screen-treatment&flow_node_metric=reached",
);
check(flowLinkQuery.valid && flowLinkQuery.canonical.flow_link_ref === "flow-link-screen-treatment", "accepts a link flow filter");
check(!flowLinkQuery.canonical.flow_stage_ref && !flowLinkQuery.canonical.flow_node_metric, "ignores the node metric while a link selection wins");

const stageAfterLink = parseMedicalMonitoringWorkspaceRouteState(
  "?project_id=synthetic-project-r5-s7&view=overview&flow_link_ref=flow-link-a&flow_stage_ref=flow-stage-b",
);
check(stageAfterLink.valid && stageAfterLink.canonical.flow_stage_ref === "flow-stage-b" && !stageAfterLink.canonical.flow_link_ref, "keeps the later stage selection when a Journey return carries both keys");
const linkAfterStage = parseMedicalMonitoringWorkspaceRouteState(
  "?project_id=synthetic-project-r5-s7&view=overview&flow_stage_ref=flow-stage-b&flow_link_ref=flow-link-a",
);
check(linkAfterStage.valid && linkAfterStage.canonical.flow_link_ref === "flow-link-a" && !linkAfterStage.canonical.flow_stage_ref, "keeps the later link selection when a Journey return carries both keys");

const flowBandQuery = parseMedicalMonitoringWorkspaceRouteState(
  "?project_id=synthetic-project-r5-s7&view=overview&flow_stage_ref=flow-stage-treatment&flow_risk_band=mid_high",
);
check(flowBandQuery.valid && flowBandQuery.canonical.flow_risk_band === "mid_high", "accepts the mid-high risk band with a stage selection");
check(flowBandQuery.canonical.flow_node_metric === "current", "keeps the default metric beside the risk band");

const badMetric = parseMedicalMonitoringWorkspaceRouteState(
  "?project_id=synthetic-project-r5-s7&view=overview&flow_stage_ref=flow-stage-treatment&flow_node_metric=total",
);
check(!badMetric.valid && badMetric.errorCode === "WORKSPACE_IDENTITY_INCOMPLETE" && badMetric.errorFields.includes("flow_node_metric"), "rejects a flow metric outside the closed registry");
const badBand = parseMedicalMonitoringWorkspaceRouteState(
  "?project_id=synthetic-project-r5-s7&view=overview&flow_stage_ref=flow-stage-treatment&flow_risk_band=low",
);
check(!badBand.valid && badBand.errorCode === "WORKSPACE_IDENTITY_INCOMPLETE" && badBand.errorFields.includes("flow_risk_band"), "rejects a flow risk band outside the closed registry");

const flowSerialized = serializeMedicalMonitoringWorkspaceRouteState(flowBandQuery.canonical);
const flowSerializedParams = new URLSearchParams(flowSerialized.slice(1));
check(flowSerializedParams.get("flow_stage_ref") === "flow-stage-treatment" && flowSerializedParams.get("flow_node_metric") === "current" && flowSerializedParams.get("flow_risk_band") === "mid_high", "serializes the closed flow filter keys");
const linkSerialized = serializeMedicalMonitoringWorkspaceRouteState(flowLinkQuery.canonical);
const linkSerializedParams = new URLSearchParams(linkSerialized.slice(1));
check(linkSerializedParams.get("flow_link_ref") === "flow-link-screen-treatment" && linkSerializedParams.get("flow_node_metric") === null, "serializes a link selection without a node metric");

const journeyWithFlow = routeStateForMedicalMonitoringWorkspaceView(flowBandQuery.canonical, "journey", {
  subject_ref: "synthetic-subject-001",
  site_ref: "synthetic-site-01",
  spine_ref: "synthetic-spine-001",
  window_start: "2026-01-01",
  window_end: "2026-08-20",
});
check(journeyWithFlow.flow_stage_ref === "flow-stage-treatment" && journeyWithFlow.flow_risk_band === "mid_high", "keeps flow context while entering the medical journey");
const returnedWithFlow = routeStateForMedicalMonitoringWorkspaceView(journeyWithFlow, "overview");
check(returnedWithFlow.flow_stage_ref === "flow-stage-treatment" && returnedWithFlow.flow_node_metric === "current" && returnedWithFlow.flow_risk_band === "mid_high", "replays the flow filter after returning from the journey");
const returnedFresh = routeStateForMedicalMonitoringWorkspaceView(subjectWithoutReturnContext.canonical, "overview");
check(!returnedFresh.flow_stage_ref && !returnedFresh.flow_link_ref, "carries no flow keys when none were set");

const patchStageOverLink = routeStateForMedicalMonitoringWorkspaceView(flowLinkQuery.canonical, "overview", { flow_stage_ref: "flow-stage-new" });
check(patchStageOverLink.flow_stage_ref === "flow-stage-new" && !patchStageOverLink.flow_link_ref && patchStageOverLink.flow_node_metric === "current", "treats a patched stage as the most recent selection over an existing link");
const patchLinkOverStage = routeStateForMedicalMonitoringWorkspaceView(flowStageDefaultMetric.canonical, "overview", { flow_link_ref: "flow-link-new" });
check(patchLinkOverStage.flow_link_ref === "flow-link-new" && !patchLinkOverStage.flow_stage_ref && !patchLinkOverStage.flow_node_metric, "treats a patched link as the most recent selection over an existing stage");
const clearedFlow = routeStateForMedicalMonitoringWorkspaceView(flowBandQuery.canonical, "overview", { flow_stage_ref: "", flow_node_metric: "", flow_risk_band: "" });
check(!clearedFlow.flow_stage_ref && !clearedFlow.flow_node_metric && !clearedFlow.flow_risk_band, "clears the whole flow filter with an empty patch");

const normalizedConflict = normalizeMedicalMonitoringWorkspaceRouteState({ flow_stage_ref: "flow-stage-a", flow_link_ref: "flow-link-b" });
check(normalizedConflict.flow_link_ref === "flow-link-b" && !normalizedConflict.flow_stage_ref, "resolves a canonical-order conflict deterministically toward the link selection");
const normalizedOrphanMetric = normalizeMedicalMonitoringWorkspaceRouteState({ flow_node_metric: "reached" });
check(!normalizedOrphanMetric.flow_node_metric, "drops an orphan flow metric without a main selection");
const normalizedBadMetric = normalizeMedicalMonitoringWorkspaceRouteState({ flow_stage_ref: "flow-stage-a", flow_node_metric: "total" });
check(normalizedBadMetric.flow_node_metric === "current", "coerces an invalid flow metric back to the default");
const normalizedEmptyBand = normalizeMedicalMonitoringWorkspaceRouteState({ flow_stage_ref: "flow-stage-a", flow_risk_band: "" });
check(normalizedEmptyBand.flow_stage_ref === "flow-stage-a" && !normalizedEmptyBand.flow_risk_band, "keeps an empty risk band out of canonical state");

const flowSplit = splitMedicalMonitoringWorkspaceState({ ...flowBandQuery.canonical, focus_ref: "flow-stage-treatment" });
check(flowSplit.canonical.flow_stage_ref === "flow-stage-treatment" && flowSplit.ephemeral.focus_ref === "flow-stage-treatment", "keeps flow keys canonical while focus stays ephemeral");
const flowTarget = validateMedicalMonitoringWorkspaceTarget(flowBandQuery.canonical);
check(flowTarget.valid, "keeps a flow-filtered overview a valid target");

const publicResult = parseMedicalMonitoringWorkspaceRouteState(
  "?project_id=project-a&result_context_token=result-context%3A1&view=overview",
);
check(publicResult.isWorkspace && publicResult.valid, "accepts a public result overview without internal 医学监查数据标识");
const publicSubject = parseMedicalMonitoringWorkspaceRouteState(
  "?project_id=project-a&result_context_token=result-context%3A1&view=journey"
    + "&site_id=site-01&subject_id=subject-01&spine_id=spine-01&start=2026-01-01&end=2026-03-31",
);
check(publicSubject.valid, "accepts a public Journey route with public subject and window locators");
const publicSerialized = new URLSearchParams(serializeMedicalMonitoringWorkspaceRouteState(publicSubject.canonical).slice(1));
check(publicSerialized.get("result_context_token") === "result-context:1" && !publicSerialized.get("run_id") && !publicSerialized.get("snapshot_id") && !publicSerialized.get("cutoff"), "serializes public result routes without internal identity");
check([...publicSerialized.keys()].every((key) => ["project_id", "result_context_token", "site_ref", "subject_ref", "spine_ref", "window_start", "window_end", "risk_instance_ref", "risk_anchor_ref", "visit_ref", "event_ref", "source_locator_ref", "view"].includes(key)), "public result query stays inside the public result identity set");
const publicExact = parseMedicalMonitoringWorkspaceRouteState(
  "?project_id=project-a&result_context_token=result-context%3A1&view=journey"
    + "&site_ref=site-01&subject_ref=subject-01&spine_ref=spine-01&window_start=2026-01-01&window_end=2026-03-31",
);
check(publicExact.valid && publicExact.canonical.subject_ref === "subject-01", "accepts exact public locator names on a result route");
const mixedPublic = parseMedicalMonitoringWorkspaceRouteState(
  "?project_id=project-a&result_context_token=result-context%3A1&view=overview&run_id=internal",
);
const publicRiskKey = parseMedicalMonitoringWorkspaceRouteState(
  "?project_id=project-a&result_context_token=result-context%3A1&view=overview&risk_key=legacy-risk",
);
check(!publicRiskKey.valid && publicRiskKey.errorCode === "PUBLIC_RESULT_INTERNAL_IDENTITY", "rejects legacy risk identity from public result URLs");
check(!mixedPublic.valid && mixedPublic.errorCode === "PUBLIC_RESULT_INTERNAL_IDENTITY", "rejects internal identity mixed into a public result route");
const mixedPublicProgress = parseMedicalMonitoringWorkspaceRouteState(
  "?project_id=project-a&public_run_token=run%3A1&view=overview&run_id=internal",
);
check(!mixedPublicProgress.valid && mixedPublicProgress.errorCode === "PUBLIC_PROGRESS_INTERNAL_IDENTITY", "rejects internal identity mixed into a public progress route");
const publicProgress = parseMedicalMonitoringWorkspaceRouteState(
  "?project_id=project-a&public_run_token=run%3A1&view=overview",
);
check(publicProgress.valid, "accepts a public progress route");
console.log(`medicalMonitoringWorkspaceRouteState: ${passed} checks passed`);
