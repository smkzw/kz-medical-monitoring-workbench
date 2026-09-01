import assert from "node:assert/strict";
import { MedicalMonitoringApiError } from "./medicalMonitoringApi.mjs";
import {
  MEDICAL_MONITORING_R7_PROGRESS_PATHS,
  createMedicalMonitoringR7ProgressApi,
} from "./medicalMonitoringProgressApi.mjs";

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

const calls = [];
const api = createMedicalMonitoringR7ProgressApi({
  baseUrl: "http://127.0.0.1:8911/",
  fetchImpl: async (url, options) => {
    calls.push({ url, options });
    return jsonResponse({ ok: true });
  },
});

const progress = await api.getProgress("proj/01", "run 07");
check(
  calls[0].url === "http://127.0.0.1:8911/api/projects/proj%2F01/modules/medical-monitoring/r7/runs/run%2007/progress",
  "progress GET pins the project-scoped R7 run progress path",
);
check(calls[0].options.method === "GET", "progress read stays GET");
check(calls[0].options.body === undefined, "progress read carries no body");

await api.startExecution("proj/01", "run 07");
await api.cancelExecution("proj/01", "run 07");
await api.resumeExecution("proj/01", "run 07");
check(
  calls[1].url.endsWith("/modules/medical-monitoring/r7/runs/run%2007/execution/start"),
  "start action posts to execution/start",
);
check(
  calls[2].url.endsWith("/modules/medical-monitoring/r7/runs/run%2007/execution/cancel"),
  "stop action posts to execution/cancel",
);
check(
  calls[3].url.endsWith("/modules/medical-monitoring/r7/runs/run%2007/execution/resume"),
  "resume action posts to execution/resume",
);
check(
  calls.slice(1).every((call) => call.options.method === "POST"), "actions are POST",
);
check(
  calls.slice(1).every((call) => call.options.body === undefined),
  "action posts send an empty body",
);
check(
  calls.slice(1).every((call) => call.options.headers["Content-Type"] === undefined),
  "empty action posts carry no JSON content type",
);

const controller = new AbortController();
await api.getProgress("p1", "r1", { signal: controller.signal });
check(
  calls[4].options.signal === controller.signal,
  "AbortSignal passes through to fetch",
);
await api.cancelExecution("p1", "r1", { signal: controller.signal });
check(
  calls[5].options.signal === controller.signal,
  "action AbortSignal passes through to fetch",
);

for (const [fn, args] of [
  [api.getProgress, [" ", "r1"]],
  [api.getProgress, ["p1", "  "]],
  [api.startExecution, ["p1", null]],
]) {
  let validationError = null;
  try {
    await fn(...args);
  } catch (error) {
    validationError = error;
  }
  check(validationError instanceof TypeError, "blank identifiers reject before fetch");
}
check(calls.length === 6, "invalid identifiers never reach fetch");

const errorApi = createMedicalMonitoringR7ProgressApi({
  fetchImpl: async () => jsonResponse(
    { code: "run_binding_not_found", message: "未找到本次监查运行。" },
    404,
  ),
});
let bindingError = null;
try {
  await errorApi.getProgress("p1", "missing-run");
} catch (error) {
  bindingError = error;
}
check(bindingError instanceof MedicalMonitoringApiError, "non-2xx raises the shared api error");
check(bindingError.status === 404, "error keeps the HTTP status");
check(
  bindingError.detail?.code === "run_binding_not_found",
  "error preserves the machine-readable code on detail",
);
check(
  bindingError.message === "未找到本次监查运行。",
  "error surfaces the server Chinese message",
);

const forbiddenApi = createMedicalMonitoringR7ProgressApi({
  fetchImpl: async () => jsonResponse(
    { code: "not_permitted", message: "当前身份无权执行该医学监查 R7 操作。" },
    403,
  ),
});
let forbiddenError = null;
try {
  await forbiddenApi.startExecution("p1", "r1");
} catch (error) {
  forbiddenError = error;
}
check(forbiddenError?.status === 403, "action 403 is not swallowed");
check(forbiddenError?.detail?.code === "not_permitted", "action 403 keeps its code");

const networkApi = createMedicalMonitoringR7ProgressApi({
  fetchImpl: async () => {
    throw new Error("network down");
  },
});
let networkError = null;
try {
  await networkApi.getProgress("p1", "r1");
} catch (error) {
  networkError = error;
}
check(networkError?.message === "network down", "fetch rejections propagate unchanged");

const abortApi = createMedicalMonitoringR7ProgressApi({
  fetchImpl: async () => {
    const error = new Error("aborted");
    error.name = "AbortError";
    throw error;
  },
});
let abortError = null;
try {
  await abortApi.getProgress("p1", "r1");
} catch (error) {
  abortError = error;
}
check(abortError?.name === "AbortError", "abort errors propagate unchanged");

check(
  MEDICAL_MONITORING_R7_PROGRESS_PATHS.progress("p", "r")
    === "/api/projects/p/modules/medical-monitoring/r7/runs/r/progress",
  "path helper stays on the mounted R7 module prefix",
);

let factoryError = null;
try {
  createMedicalMonitoringR7ProgressApi({ fetchImpl: null });
} catch (error) {
  factoryError = error;
}
check(factoryError instanceof TypeError, "factory requires a fetch implementation");

console.log(`medicalMonitoringProgressApi: ${passed} passed`);
