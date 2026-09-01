import assert from "node:assert/strict";

import { MedicalMonitoringApiError } from "./medicalMonitoringApi.mjs";
import {
  MEDICAL_MONITORING_PRODUCT_PATHS,
  MEDICAL_MONITORING_PUBLIC_RESULT_PATHS,
  MONITORING_PRODUCT_DEFAULT_HISTORY_LIMIT,
  createMedicalMonitoringProductApi,
} from "./medicalMonitoringProductApi.mjs";

let passed = 0;
function check(condition, message) {
  assert.equal(Boolean(condition), true, message);
  passed += 1;
}

function jsonResponse(body, status = 200) {
  return {
    status,
    ok: status >= 200 && status < 300,
    headers: { get: () => "application/json" },
    json: async () => body,
    text: async () => JSON.stringify(body),
  };
}

const calls = [];
const api = createMedicalMonitoringProductApi({
  baseUrl: "http://127.0.0.1:8911/",
  fetchImpl: async (url, options) => {
    calls.push({ url, options });
    return jsonResponse({ ok: true });
  },
});

await api.bootstrapWorkspace("proj/01");
await api.getSetupOptions("proj/01", { currentSnapshotToken: "snap 01" });
await api.previewRiskRule("proj/01", { source_text: "ALT 超过上限" });
await api.listRiskRules("proj/01");
await api.confirmRiskRule("proj/01", { preview_token: "preview-1", candidate_id: "hepatic-data" });
await api.prepareAndStart("proj/01", {
  current_snapshot_token: "snap-01",
  mode: "daily",
  execution_basis: "full",
  baseline_token: null,
  risk_rule_tokens: [],
  idempotency_key: "monitoring-test-1",
});
await api.listRuns("proj/01");
await api.getPublicProgress("proj/01", "run:01");
await api.getResultEntry("proj/01", "run:01");
await api.getResultOverview("proj/01", "result-context:01", { siteRef: "site/01" });
await api.getResultSubject("proj/01", "result-context:01", "S/01", {
  siteRef: "site/01",
  spineRef: "spine/01",
  windowStart: "2026-01-01",
  windowEnd: "2026-03-31",
  riskInstanceRef: "risk/01",
  riskAnchorRef: "anchor/01",
  visitRef: "visit/01",
  eventRef: "event/01",
});
await api.getResultSourceEvidence("proj/01", "result-context:01", {
  riskInstanceRef: "risk/01",
  sourceLocatorRef: "source/01",
});

check(calls[0].url.endsWith("/workspace/bootstrap"), "bootstrap uses the R7 project route");
check(calls[0].options.method === "POST", "bootstrap is a POST");
check(calls[0].options.body === undefined, "bootstrap has no client body");
check(calls[1].url.includes("current_snapshot_token=snap+01"), "setup reads the optional current snapshot selector");
check(calls[1].options.method === "GET", "setup options remains a GET");
check(calls[2].options.headers["Content-Type"] === "application/json", "risk preview serializes JSON");
check(JSON.parse(calls[5].options.body).idempotency_key === "monitoring-test-1", "prepare forwards the caller nonce");
check(calls[6].url.endsWith(`/runs?limit=${MONITORING_PRODUCT_DEFAULT_HISTORY_LIMIT}`), "history uses the frozen default limit");
check(calls[7].url.endsWith("/runs/run%3A01/progress"), "public progress encodes the public run token");
check(calls[8].url.endsWith("/runs/run%3A01/result-entry"), "result entry stays on the public run route");
check(calls[9].url.includes("/results/result-context%3A01/overview?site_ref=site%2F01"), "overview uses result context and site locator");
check(calls[10].url.includes("/subjects/S%2F01?"), "subject route encodes the subject locator");
const subjectUrl = new URL(calls[10].url);
check(subjectUrl.searchParams.get("window_start") === "2026-01-01", "subject preserves the public window");
check(subjectUrl.searchParams.get("risk_instance_ref") === "risk/01", "subject preserves the optional risk locator");
check(calls[11].url.includes("risk_instance_ref=risk%2F01"), "source evidence uses the public risk locator");
check(calls.every((call) => call.options.headers.Accept === "application/json"), "all product calls request JSON");

for (const invalid of [
  () => api.getSetupOptions(""),
  () => api.getPublicProgress("proj", ""),
  () => api.getResultOverview("proj", ""),
  () => api.getResultSubject("proj", "ctx", ""),
  () => api.getResultSubject("proj", "ctx", "subject", {}),
  () => api.getResultSourceEvidence("proj", "ctx", {}),
  () => api.prepareAndStart("proj", { run_id: "internal" }),
]) {
  assert.throws(invalid, TypeError);
  passed += 1;
}
check(calls.length === 12, "invalid identifiers and non-public payloads never reach fetch");

const errorApi = createMedicalMonitoringProductApi({
  fetchImpl: async () => jsonResponse(
    { code: "result_context_unavailable", message: "本次结果暂不可查看，请返回进度页" },
    409,
  ),
});
let error = null;
try {
  await errorApi.getResultOverview("proj", "result-context:missing");
} catch (caught) {
  error = caught;
}
check(error instanceof MedicalMonitoringApiError, "non-2xx product reads raise the shared API error");
check(error.status === 409, "product error preserves HTTP status");
check(error.detail?.code === "result_context_unavailable", "product error preserves machine code");
check(error.message === "本次结果暂不可查看，请返回进度页", "product error keeps server Chinese copy");

const networkApi = createMedicalMonitoringProductApi({
  fetchImpl: async () => { throw new Error("network down"); },
});
await assert.rejects(networkApi.getPublicProgress("proj", "run:01"), /network down/);
passed += 1;

check(
  MEDICAL_MONITORING_PRODUCT_PATHS.resultSourceEvidence("p", "ctx", {
    riskInstanceRef: "r",
    sourceLocatorRef: "s",
  }) === "/api/projects/p/modules/medical-monitoring/r7/results/ctx/source-evidence?risk_instance_ref=r&source_locator_ref=s",
  "public result path helpers remain deterministic",
);

// --- Slice-08C-2 continuity client contract ---
const continuityCalls = [];
const continuityApi = createMedicalMonitoringProductApi({
  baseUrl: "http://127.0.0.1:8911/",
  fetchImpl: async (url, options) => {
    continuityCalls.push({ url, options });
    return jsonResponse({ ok: true });
  },
});

const continuitySignal = Symbol("continuity-signal");
await continuityApi.getResultContinuity("proj/01", "result-context:01");
await continuityApi.getResultContinuity("proj/01", "result-context:02", { siteRef: "site/01" });
await continuityApi.getPublicResultContinuity("proj/01", "result-context:03", {
  site_ref: "site/02",
  signal: continuitySignal,
});

check(
  continuityCalls[0].url.endsWith("/results/result-context%3A01/continuity"),
  "continuity stays on the public result-context route",
);
check(continuityCalls[0].options.method === "GET", "continuity is a GET");
check(continuityCalls[0].options.body === undefined, "continuity never sends a request body");
check(!continuityCalls[0].url.includes("?"), "continuity without selector sends no query");
check(
  continuityCalls[1].url === "http://127.0.0.1:8911/api/projects/proj%2F01/modules/medical-monitoring/r7/results/result-context%3A02/continuity?site_ref=site%2F01",
  "continuity forwards only the optional site_ref query",
);
check(
  new URL(continuityCalls[1].url).search === "?site_ref=site%2F01",
  "continuity query contains no keys beyond site_ref",
);
check(
  continuityCalls[2].options.signal === continuitySignal,
  "continuity forwards the caller abort signal",
);
check(
  continuityCalls.every((call) => call.options.headers.Accept === "application/json"),
  "continuity requests JSON",
);

for (const invalid of [
  () => continuityApi.getResultContinuity("", "result-context:01"),
  () => continuityApi.getResultContinuity("  ", "result-context:01"),
  () => continuityApi.getResultContinuity("proj", ""),
]) {
  assert.throws(invalid, TypeError);
  passed += 1;
}
check(continuityCalls.length === 3, "invalid continuity identifiers never reach fetch");

const continuityErrorApi = createMedicalMonitoringProductApi({
  fetchImpl: async () => jsonResponse(
    { code: "continuity_unavailable", message: "连续性比较结果暂不可查看，请返回结果页" },
    409,
  ),
});
let continuityError = null;
try {
  await continuityErrorApi.getResultContinuity("proj", "result-context:missing");
} catch (caught) {
  continuityError = caught;
}
check(continuityError instanceof MedicalMonitoringApiError, "continuity errors raise the shared API error");
check(continuityError.status === 409, "continuity error preserves HTTP status");
check(continuityError.detail?.code === "continuity_unavailable", "continuity error preserves machine code");
check(continuityError.message === "连续性比较结果暂不可查看，请返回结果页", "continuity error keeps server Chinese copy");

check(
  MEDICAL_MONITORING_PRODUCT_PATHS.resultContinuity("p", "ctx", { siteRef: "s" })
    === "/api/projects/p/modules/medical-monitoring/r7/results/ctx/continuity?site_ref=s",
  "continuity path helper remains deterministic",
);
check(
  MEDICAL_MONITORING_PUBLIC_RESULT_PATHS.continuity("p", "ctx")
    === "/api/projects/p/modules/medical-monitoring/r7/results/ctx/continuity",
  "public result path alias covers continuity",
);

console.log(`medicalMonitoringProductApi: ${passed} passed`);
