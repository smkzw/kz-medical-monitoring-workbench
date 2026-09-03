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

// --- Phase C C1 data-admission client contract ---
const admissionCalls = [];
const admissionApi = createMedicalMonitoringProductApi({
  baseUrl: "http://127.0.0.1:8911/",
  fetchImpl: async (url, options) => {
    admissionCalls.push({ url, options });
    return jsonResponse({ ok: true });
  },
});

const admissionSignal = Symbol("admission-signal");
await admissionApi.createDataAdmission("proj/01", { source_dir: "/generated/non-real/source" });
await admissionApi.createDataAdmission("proj/01", { source_dir: "/generated/non-real/source" }, { signal: admissionSignal });
await admissionApi.getDataAdmissionStatus("proj/01", "attempt-0001");
await admissionApi.getDataAdmissionProfile("proj/01", "attempt:0002", { signal: admissionSignal });

check(
  admissionCalls[0].url.endsWith("/modules/medical-monitoring/r7/data-admissions"),
  "admission create stays on the R7 project route",
);
check(admissionCalls[0].options.method === "POST", "admission create is a POST");
check(
  admissionCalls[0].options.headers["Content-Type"] === "application/json",
  "admission create serializes JSON",
);
check(
  JSON.parse(admissionCalls[0].options.body).source_dir === "/generated/non-real/source",
  "admission create forwards the read-only source directory",
);
check(
  Object.keys(JSON.parse(admissionCalls[0].options.body)).length === 1,
  "admission create sends no field beyond source_dir",
);
check(
  admissionCalls[2].url.endsWith("/data-admissions/attempt-0001"),
  "admission status reads the attempt route",
);
check(admissionCalls[2].options.method === "GET", "admission status is a GET");
check(admissionCalls[2].options.body === undefined, "admission status sends no request body");
check(
  admissionCalls[3].url.endsWith("/data-admissions/attempt%3A0002/profile"),
  "admission profile reads the attempt profile route with an encoded attempt id",
);
check(admissionCalls[3].options.method === "GET", "admission profile is a GET");
check(
  admissionCalls[1].options.signal === admissionSignal
    && admissionCalls[3].options.signal === admissionSignal,
  "admission calls forward the caller abort signal",
);

await admissionApi.listDataAdmissionMappingCandidates("proj/01", "attempt-0001", { focus: "critical", signal: admissionSignal });
await admissionApi.adoptDataAdmissionMappingDraft("proj/01", "attempt-0001", { reason: "采用建议" });
await admissionApi.editDataAdmissionMappingDraftField("proj/01", "attempt-0001", {
  draft_id: "draft-1",
  domain: "AE",
  source_field: "AETERM",
  patch: { recommended_role: "ae_term" },
  expected_version: 1,
  idempotency_key: "edit-1",
});
await admissionApi.adjudicateDataAdmissionMappingDraft("proj/01", "attempt-0001", {
  draft_id: "draft-1",
});
await admissionApi.confirmDataAdmissionMappingDraft("proj/01", "attempt-0001", {
  draft_id: "draft-1",
  expected_version: 2,
  confirmation_reason: "确认完成",
  idempotency_key: "confirm-1",
});
check(
  admissionCalls[4].url.includes("/mapping-candidates?focus=critical"),
  "mapping candidate list uses focus query",
);
check(admissionCalls[4].options.method === "GET", "mapping candidate list is GET");
check(
  admissionCalls[5].url.endsWith("/mapping-draft"),
  "mapping draft adopt stays on attempt route",
);
check(admissionCalls[5].options.method === "POST", "mapping draft adopt is POST");
check(admissionCalls[6].options.method === "PATCH", "mapping draft field edit is PATCH");
check(
  admissionCalls[7].url.endsWith("/mapping-draft/adjudicate"),
  "mapping draft adjudication stays on attempt route",
);
check(admissionCalls[7].options.method === "POST", "mapping draft adjudication is POST");
check(
  admissionCalls[8].url.endsWith("/mapping-draft/confirm"),
  "mapping draft confirm stays on attempt confirm route",
);
check(admissionCalls[8].options.method === "POST", "mapping draft confirm is POST");
check(
  admissionCalls.every((call) => call.options.headers.Accept === "application/json"),
  "admission requests JSON",
);

for (const invalid of [
  () => admissionApi.createDataAdmission("proj", null),
  () => admissionApi.createDataAdmission("proj", ["/generated/non-real/source"]),
  () => admissionApi.createDataAdmission("proj", { source_dir: "/generated", run_id: "internal" }),
  () => admissionApi.createDataAdmission("", { source_dir: "/generated" }),
  () => admissionApi.getDataAdmissionStatus("proj", ""),
  () => admissionApi.getDataAdmissionProfile("  ", "attempt-0001"),
]) {
  assert.throws(invalid, TypeError);
  passed += 1;
}
check(admissionCalls.length === 9, "invalid admission identifiers and payloads never reach fetch");

const uploadCalls = [];
const admissionUploadApi = createMedicalMonitoringProductApi({
  fetchImpl: async (url, options) => {
    uploadCalls.push({ url, options });
    return jsonResponse({ attempt_id: "attempt-upload-1", state: "profile_ready" });
  },
});
const uploadFile = new File(["subject_id,visit\nS001,V1\n"], "listing.csv", { type: "text/csv" });
Object.defineProperty(uploadFile, "webkitRelativePath", { value: "本期数据/listing.csv" });
await admissionUploadApi.createDataAdmissionUpload("proj/01", [uploadFile], { signal: admissionSignal });
check(uploadCalls.length === 1, "browser upload reaches fetch once");
check(uploadCalls[0].url.endsWith("/data-admissions/upload"), "browser upload stays on the R7 project route");
check(uploadCalls[0].options.method === "POST", "browser upload is a POST");
check(uploadCalls[0].options.body instanceof FormData, "browser upload sends multipart form data");
check(!("Content-Type" in uploadCalls[0].options.headers), "browser supplies the multipart boundary");
check(uploadCalls[0].options.body.get("relative_paths") === "本期数据/listing.csv",
  "browser upload preserves the folder-relative path");
check(uploadCalls[0].options.body.get("files")?.name === "listing.csv", "browser upload includes the selected file");
check(uploadCalls[0].options.signal === admissionSignal, "browser upload forwards the caller abort signal");
for (const invalid of [
  () => admissionUploadApi.createDataAdmissionUpload("proj", []),
  () => admissionUploadApi.createDataAdmissionUpload("proj", [null]),
  () => admissionUploadApi.createDataAdmissionUpload("", [uploadFile]),
]) {
  assert.throws(invalid, TypeError);
  passed += 1;
}
check(uploadCalls.length === 1, "invalid browser uploads never reach fetch");

const documentCalls = [];
const documentApi = createMedicalMonitoringProductApi({
  baseUrl: "http://127.0.0.1:8911/",
  fetchImpl: async (url, options) => {
    documentCalls.push({ url, options });
    return jsonResponse({ ready: true, headline: "研究文件已准备好" });
  },
});
const protocolFile = new File(["synthetic protocol"], "protocol.docx", {
  type: "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
});
await documentApi.getDataAdmissionDocumentReadiness("proj/01", "attempt:0002", {
  signal: admissionSignal,
});
await documentApi.uploadStudyDocument("proj/01", "attempt:0002", "protocol", protocolFile, {
  signal: admissionSignal,
});
await documentApi.startDataAdmissionMappingCandidates("proj/01", "attempt:0002", {
  signal: admissionSignal,
});
check(
  documentCalls[0].url.endsWith("/data-admissions/attempt%3A0002/study-documents"),
  "document readiness stays on the admission attempt route",
);
check(documentCalls[0].options.method === "GET", "document readiness is a GET");
check(documentCalls[0].options.body === undefined, "document readiness sends no body");
check(
  documentCalls[1].url.endsWith("/data-admissions/attempt%3A0002/study-documents?role=protocol"),
  "study document upload is atomically scoped to the admission attempt",
);
check(documentCalls[1].options.method === "POST", "study document upload is a POST");
check(documentCalls[1].options.body instanceof FormData, "study document upload is multipart");
check(documentCalls[1].options.body.get("file")?.name === "protocol.docx", "study document upload includes the file");
check(!("Content-Type" in documentCalls[1].options.headers), "browser supplies the study-document multipart boundary");
check(
  documentCalls[2].url.endsWith("/data-admissions/attempt%3A0002/mapping-candidates"),
  "mapping start uses the dual-generation attempt route",
);
check(documentCalls[2].options.method === "POST", "mapping start is a POST");
check(documentCalls[2].options.body === undefined, "mapping start sends no client-controlled body");
check(
  documentCalls.every((call) => call.options.signal === admissionSignal),
  "study document calls forward the caller abort signal",
);
for (const invalid of [
  () => documentApi.getDataAdmissionDocumentReadiness("proj", ""),
  () => documentApi.uploadStudyDocument("proj", "", "protocol", protocolFile),
  () => documentApi.uploadStudyDocument("proj", "attempt", "", protocolFile),
  () => documentApi.uploadStudyDocument("proj", "attempt", "protocol", null),
  () => documentApi.startDataAdmissionMappingCandidates("proj", ""),
]) {
  assert.throws(invalid, TypeError);
  passed += 1;
}
check(documentCalls.length === 3, "invalid study document calls never reach fetch");

const admissionErrorApi = createMedicalMonitoringProductApi({
  fetchImpl: async () => jsonResponse(
    {
      code: "admission_source_invalid",
      message: "未找到可导入的数据目录。请确认所选数据位置存在且包含数据文件后重试。",
    },
    422,
  ),
});
let admissionError = null;
try {
  await admissionErrorApi.createDataAdmission("proj", { source_dir: "/generated/missing" });
} catch (caught) {
  admissionError = caught;
}
check(admissionError instanceof MedicalMonitoringApiError, "admission errors raise the shared API error");
check(admissionError.status === 422, "admission error preserves HTTP status");
check(admissionError.detail?.code === "admission_source_invalid", "admission error preserves machine code");
check(
  admissionError.message === "未找到可导入的数据目录。请确认所选数据位置存在且包含数据文件后重试。",
  "admission error keeps server Chinese copy",
);

const admissionNotFoundErrorApi = createMedicalMonitoringProductApi({
  fetchImpl: async () => jsonResponse(
    {
      code: "admission_attempt_not_found",
      message: "未找到对应的数据导入记录。请返回上一步重新选择，或重新发起导入。",
    },
    404,
  ),
});
let admissionNotFoundError = null;
try {
  await admissionNotFoundErrorApi.getDataAdmissionStatus("proj", "attempt-missing");
} catch (caught) {
  admissionNotFoundError = caught;
}
check(admissionNotFoundError instanceof MedicalMonitoringApiError, "admission reads raise the shared API error");
check(admissionNotFoundError.status === 404, "admission read error preserves HTTP status");
check(
  admissionNotFoundError.detail?.code === "admission_attempt_not_found",
  "admission read error preserves machine code",
);

check(
  MEDICAL_MONITORING_PRODUCT_PATHS.dataAdmissionUpload("p")
    === "/api/projects/p/modules/medical-monitoring/r7/data-admissions/upload",
  "admission upload path helper remains deterministic",
);
check(
  MEDICAL_MONITORING_PRODUCT_PATHS.dataAdmissionStatus("p", "a")
    === "/api/projects/p/modules/medical-monitoring/r7/data-admissions/a",
  "admission status path helper remains deterministic",
);
check(
  MEDICAL_MONITORING_PRODUCT_PATHS.dataAdmissionProfile("p", "a")
    === "/api/projects/p/modules/medical-monitoring/r7/data-admissions/a/profile",
  "admission profile path helper remains deterministic",
);
check(
  MEDICAL_MONITORING_PRODUCT_PATHS.dataAdmissionStudyDocuments("p", "a")
    === "/api/projects/p/modules/medical-monitoring/r7/data-admissions/a/study-documents",
  "document readiness path helper remains deterministic",
);

console.log(`medicalMonitoringProductApi: ${passed} passed`);
