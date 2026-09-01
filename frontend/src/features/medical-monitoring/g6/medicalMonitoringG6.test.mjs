import assert from "node:assert/strict";
import {
  G6_CANONICAL_ADAPTER_ID,
  G6_CANONICAL_ADAPTER_KIND,
  G6_CANONICAL_APP_VERSION,
  G6_CANONICAL_BUNDLE_DIGEST,
  G6_CANONICAL_CONTRACT_REF,
  G6_CANONICAL_CONTRACT_VERSION,
  G6_CANONICAL_DOMAINS,
  G6_CANONICAL_FIXTURE_DIGEST,
  G6_CANONICAL_MODES,
  G6_CANONICAL_MODEL,
  G6_CANONICAL_PROFILE_BINDING_DIGEST,
  G6_CANONICAL_PROFILE_ID,
  G6_CANONICAL_PROVIDER,
  G6_CANONICAL_RUN_BINDING_DIGEST,
  createG6SyntheticAdapter,
  fetchG6SyntheticBundle,
  validateG6CanonicalBundle,
} from "./medicalMonitoringG6Adapter.mjs";
import { loadCanonicalG6BundleForTest } from "./medicalMonitoringG6CanonicalTestFixture.mjs";
import {
  g6SeverityTone,
  projectG6Domains,
  projectG6Flow,
  projectG6Journey,
  selectG6FlowSubjects,
} from "./medicalMonitoringG6Projection.mjs";
import { G6_SYNTHETIC_ROUTE, isG6SyntheticRoute } from "./medicalMonitoringG6Route.mjs";
import {
  G6_PRODUCTION_VIEWPORTS,
  buildG6EvidencePack,
  expectedG6Measurement,
  measureG6Layout,
  validateG6Measurement,
} from "./medicalMonitoringG6VisualEvidence.mjs";

let passed = 0;
function check(value, message) {
  assert.equal(Boolean(value), true, message);
  passed += 1;
}

check(G6_SYNTHETIC_ROUTE === "/medical-monitoring/synthetic", "synthetic route is canonical");
check(isG6SyntheticRoute({ pathname: G6_SYNTHETIC_ROUTE, search: "" }), "canonical synthetic route is recognized");
check(isG6SyntheticRoute({ pathname: "/", search: "?g6=synthetic" }), "synthetic query route is recognized from the root");
check(!isG6SyntheticRoute({ pathname: "/monitoring", search: "?g6=synthetic" }), "synthetic query does not hijack monitoring");

const bundle = loadCanonicalG6BundleForTest();
const fixture = bundle.fixture;
const binding = bundle.binding;
const validatedBundle = validateG6CanonicalBundle(bundle);
check(validatedBundle.bundle_digest === G6_CANONICAL_BUNDLE_DIGEST, "canonical bundle digest is exact");
check(fixture.fixture_digest === G6_CANONICAL_FIXTURE_DIGEST, "canonical fixture digest is exact");
check(fixture.binding_digest === G6_CANONICAL_PROFILE_BINDING_DIGEST, "canonical profile binding digest is exact");
check(binding.binding_digest === G6_CANONICAL_RUN_BINDING_DIGEST, "canonical selected binding digest is exact");
check(bundle.contract_ref === G6_CANONICAL_CONTRACT_REF && bundle.contract_version === G6_CANONICAL_CONTRACT_VERSION, "canonical contract identity is exact");
check(bundle.app_version === G6_CANONICAL_APP_VERSION && fixture.synthetic_profile_id === G6_CANONICAL_PROFILE_ID, "canonical app and profile identity are exact");
check(bundle.synthetic_only === true && bundle.offline === true && fixture.synthetic_only === true && fixture.offline === true, "canonical fixture is synthetic and offline");
check(binding.provider === G6_CANONICAL_PROVIDER && binding.model === G6_CANONICAL_MODEL, "canonical provider and model are synthetic");
check(binding.adapter_id === G6_CANONICAL_ADAPTER_ID && binding.adapter_kind === G6_CANONICAL_ADAPTER_KIND, "canonical adapter identity is mock recorded");
check(fixture.projects.length === 2 && fixture.centers.length === 3 && fixture.subjects.length === 12, "canonical fixture has two projects, three centers, and twelve subjects");
check(fixture.visits.length === 48 && fixture.events.length === 96, "canonical fixture has forty-eight visits and ninety-six events");
check(fixture.analysis_modes.length === 3 && fixture.analysis_modes.join(",") === G6_CANONICAL_MODES.join(","), "canonical fixture has all three analysis modes");
check(fixture.journey.orientation === "horizontal" && fixture.journey.marker_domains.length === 8, "canonical Journey is horizontal across eight domains");
check(new Set(fixture.events.map((event) => event.domain)).size === 8 && G6_CANONICAL_DOMAINS.every((domain) => fixture.events.some((event) => event.domain === domain)), "canonical events cover every Journey domain");
check(fixture.section_15_4.task_count === 13 && fixture.user_task_evidence === undefined, "fixture keeps the thirteen-task contract without page-only duplication");
check(bundle.user_task_evidence.task_count === 13, "bundle carries thirteen application task evidence rows");
check(new Set(fixture.subjects.map((subject) => subject.risk_state)).size === 8, "canonical fixture carries all eight risk states");
check(fixture.flow_rows.some((row) => row.count === 0), "canonical flow carries a zero-value row");

const domains = projectG6Domains(bundle);
check(domains.length === 8 && domains.every((domain) => domain.shape && domain.tone), "projection preserves eight distinct domain markers");
check(g6SeverityTone("complete_failure") === "danger" && g6SeverityTone("missing_data") === "info", "risk tones stay visible for canonical risk states");
for (const project of fixture.projects) {
  const flow = projectG6Flow(bundle, project.project_ref);
  check(flow.state === "ready", `${project.display_name} flow is readable`);
  check(flow.reconciliation.entry_total === 6 && flow.reconciliation.current_total === 6, `${project.display_name} flow conserves six subjects`);
  check(flow.center_rows.length === 3, `${project.display_name} flow retains all three centers`);
  check(flow.links.some((link) => link.zero_value), `${project.display_name} flow preserves the zero-value branch`);
  check(flow.topology.includes("split") && flow.topology.includes("merge") && flow.topology.includes("zero_value"), `${project.display_name} flow exposes topology challenges`);
  const centerRef = project.center_refs[0];
  const centerFlow = projectG6Flow(bundle, project.project_ref, centerRef);
  check(centerFlow.state === "ready" && centerFlow.subjects.length === 2, `${project.display_name} center flow filters two subjects`);
  check(centerFlow.links.some((link) => link.zero_value), `${project.display_name} center flow retains the zero-value branch`);
  const positiveLink = flow.links.find((link) => link.count > 0);
  check(selectG6FlowSubjects(flow, { linkRef: positiveLink.ref }).every((subject) => positiveLink.subject_refs.includes(subject.subject_ref)), `${project.display_name} link drill-down keeps source identity`);
}

const firstProject = fixture.projects[0];
const denseSubject = fixture.subjects.find((subject) => subject.subject_ref === "synthetic-subject-001");
const journey = projectG6Journey(bundle, firstProject.project_ref, denseSubject.subject_ref);
check(journey.state === "ready" && journey.visits.length === 4 && journey.events.length === 8, "canonical Journey retains four visits and eight subject events");
check(journey.axis.direction === "left-to-right", "canonical Journey axis direction is horizontal");
check(journey.lane_count === 8 && new Set(journey.events.map((event) => event.domain)).size === 8, "canonical Journey retains every domain lane");
check(journey.dense_event_count >= 2 && journey.events.every((event) => event.source_ref), "same-visit events and source identity remain readable");
check(journey.risks.length === 1 && journey.risks[0].subject_ref === denseSubject.subject_ref, "Journey risk remains bound to the same subject");

let requestedEndpoint = "";
const fetched = await fetchG6SyntheticBundle({
  fetchImpl: async (endpoint, options) => {
    requestedEndpoint = `${endpoint}:${options.method}`;
    return { ok: true, json: async () => bundle };
  },
});
check(requestedEndpoint === "/api/g6/synthetic-bundle:GET" && fetched.bundle_digest === G6_CANONICAL_BUNDLE_DIGEST, "adapter loader fetches and validates the canonical endpoint");
let unavailableCode = "";
try {
  await fetchG6SyntheticBundle({ fetchImpl: async () => ({ ok: false, status: 503 }) });
} catch (error) {
  unavailableCode = error.code;
}
check(unavailableCode === "CANONICAL_BUNDLE_UNAVAILABLE", "bundle fetch failure fails closed without fallback");

const adapter = createG6SyntheticAdapter({ bundle });
check(adapter.listProjects().length === 2 && adapter.getModes().length === 3, "adapter exposes only canonical project and mode catalogs");
check(adapter.getDomains().length === 8, "adapter exposes all canonical Journey domains");
const prepared = adapter.prepareRun({ projectRef: firstProject.project_ref, mode: "full", idempotencyKey: "g6-canonical-test" });
const repeated = adapter.prepareRun({ projectRef: firstProject.project_ref, mode: "full", idempotencyKey: "g6-canonical-test" });
check(prepared.run_ref === "synthetic-run-alpha-full" && repeated.run_ref === prepared.run_ref, "canonical run preparation is idempotent");
let conflictingPrepare = "";
try {
  adapter.prepareRun({ projectRef: firstProject.project_ref, mode: "periodic_increment", idempotencyKey: "other" });
} catch (error) {
  conflictingPrepare = error.code;
}
check(conflictingPrepare === "RUN_ALREADY_BOUND", "concurrent canonical modes are rejected");
adapter.startRun(prepared.run_ref);
let progress = prepared;
for (let index = 0; index < 4; index += 1) progress = adapter.readProgress(prepared.run_ref);
check(progress.state === "complete" && progress.percent === 100 && progress.terminal_status === "complete", "canonical full analysis reaches a deterministic terminal state");
check(adapter.getResult(prepared.run_ref).run.state === "complete", "canonical result remains bound to the same run");
check(adapter.getBinding().binding_digest === G6_CANONICAL_RUN_BINDING_DIGEST, "adapter retains canonical selected binding");
check(adapter.getLedger().every((entry) => entry.action !== "real_model_call"), "adapter ledger contains no real model call");
let tamperCode = "";
try {
  const tampered = JSON.parse(JSON.stringify(bundle));
  tampered.binding.synthetic_only = false;
  validateG6CanonicalBundle(tampered);
} catch (error) {
  tamperCode = error.code;
}
check(tamperCode === "BINDING_BOUNDARY_MISMATCH", "binding boundary drift fails closed before rendering");

function fakeElement(rect, extras = {}) {
  return {
    ...extras,
    getBoundingClientRect: () => ({ ...rect, right: rect.left + rect.width, bottom: rect.top + rect.height }),
  };
}
const fakeMap = new Map();
const fakeRoot = {
  scrollLeft: 0,
  scrollTop: 0,
  clientWidth: 1920,
  scrollWidth: 1920,
  clientHeight: 1080,
  scrollHeight: 1600,
  querySelector(selector) {
    return fakeMap.get(selector) || null;
  },
};
const viewport = G6_PRODUCTION_VIEWPORTS[0];
for (const [key, selector] of Object.entries({
  page: "[data-g6-synthetic-page]",
  content: "[data-g6-content]",
  core_action: "[data-g6-core-action]",
  risk_summary: "[data-g6-risk-summary]",
  flow_chart: "[data-g6-flow-chart]",
  flow_table_first_row: "[data-g6-flow-table] tbody tr:first-child",
  journey_axis: "[data-g6-journey-axis]",
  subject_selector: "[data-g6-subject-selector]",
})) {
  fakeMap.set(selector, fakeElement({ left: 80, top: 100, width: key === "flow_chart" ? 1700 : 300, height: key === "page" ? 1080 : 80 }));
}
fakeMap.set("[data-g6-journey-scroll]", fakeElement({ left: 80, top: 880, width: 1700, height: 360 }, { clientWidth: 1700, scrollWidth: 1840, clientHeight: 360, scrollHeight: 360 }));
fakeMap.set("[data-g6-column-grid]", { dataset: { columns: "3" } });
fakeMap.set("[data-g6-reading-column]", fakeElement({ left: 80, top: 200, width: 760, height: 400 }));
const observedMeasurement = measureG6Layout(fakeRoot, viewport);
check(validateG6Measurement(observedMeasurement).valid, "DOM measurement contract accepts canonical structural input");
check(observedMeasurement.scroll.journey.client_width === 1700, "measurement records Journey scroll width");
const overviewMeasurement = measureG6Layout(fakeRoot, viewport, { requiredKeys: ["page", "content", "core_action", "risk_summary", "flow_chart", "flow_table_first_row", "subject_selector"] });
check(validateG6Measurement(overviewMeasurement).valid && overviewMeasurement.scroll.journey === null, "overview measurement can omit the inactive Journey surface");
const partialPack = buildG6EvidencePack({ bundle, measurements: [overviewMeasurement] });
check(partialPack.missing_viewports.length === 3 && partialPack.missing_measurement_keys.some((item) => item.viewport_id === viewport.viewport_id && item.key === "journey_axis"), "evidence pack exposes incomplete per-viewport key coverage");
const expectedMeasurements = G6_PRODUCTION_VIEWPORTS.map(expectedG6Measurement);
check(expectedMeasurements.every((measurement) => validateG6Measurement(measurement).valid), "all three frozen desktop expectations validate");
const pack = buildG6EvidencePack({ bundle, measurements: expectedMeasurements, interactions: [{ action: "canonical_bundle_loaded", result: "ready" }], adapterLedger: adapter.getLedger() });
check(pack.missing_viewports.length === 0 && pack.missing_measurement_keys.length === 0, "evidence pack accounts for every viewport and required key");
check(pack.identity.bundle_digest === G6_CANONICAL_BUNDLE_DIGEST && pack.identity.fixture_digest === G6_CANONICAL_FIXTURE_DIGEST, "evidence pack carries canonical bundle and fixture identity");
check(pack.identity.profile_binding_digest === G6_CANONICAL_PROFILE_BINDING_DIGEST && pack.identity.binding_digest === G6_CANONICAL_RUN_BINDING_DIGEST, "evidence pack carries canonical profile and run binding identity");
check(pack.execution.browser_started === false && pack.execution.real_model_calls === 0, "evidence pack explicitly records deferred browser and zero model calls");
check(pack.acceptance_state === "not_evaluable_without_ego_lite", "structural pack does not overclaim visual acceptance");

console.log(`G6 canonical frontend contract: ${passed} checks passed`);
