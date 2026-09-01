import { MedicalMonitoringApiError } from "./medicalMonitoringApi.mjs";

const API_PREFIX = "/api/projects";

function requireId(value, label) {
  const clean = value === null || value === undefined ? "" : String(value).trim();
  if (!clean) throw new TypeError(`${label} is required`);
  return clean;
}

function encodeSegment(value) {
  return encodeURIComponent(requireId(value, "path identifier"));
}

function r7RunPath(projectId, runRef) {
  return `${API_PREFIX}/${encodeSegment(requireId(projectId, "projectId"))}`
    + `/modules/medical-monitoring/r7/runs/${encodeSegment(requireId(runRef, "runRef"))}`;
}

export const MEDICAL_MONITORING_R7_PROGRESS_PATHS = Object.freeze({
  progress: (projectId, runRef) => `${r7RunPath(projectId, runRef)}/progress`,
  executionStart: (projectId, runRef) => `${r7RunPath(projectId, runRef)}/execution/start`,
  executionCancel: (projectId, runRef) => `${r7RunPath(projectId, runRef)}/execution/cancel`,
  executionResume: (projectId, runRef) => `${r7RunPath(projectId, runRef)}/execution/resume`,
});

function joinBaseUrl(baseUrl, path) {
  const base = String(baseUrl || "").replace(/\/+$/, "");
  return `${base}${path}`;
}

async function responsePayload(response) {
  if (response.status === 204) return null;
  const contentType = response.headers?.get?.("content-type") || "";
  if (contentType.includes("application/json")) return response.json();
  const text = await response.text();
  if (!text) return null;
  try {
    return JSON.parse(text);
  } catch {
    return text;
  }
}

function errorMessage(payload, response) {
  if (payload && typeof payload === "object") {
    if (typeof payload.message === "string" && payload.message.trim()) {
      return payload.message;
    }
    if (typeof payload.detail === "string") return payload.detail;
    if (payload.detail && typeof payload.detail === "object") {
      if (typeof payload.detail.message === "string") return payload.detail.message;
      if (typeof payload.detail.code === "string") return payload.detail.code;
    }
    if (typeof payload.code === "string") return payload.code;
  }
  if (typeof payload === "string" && payload.trim()) return payload.trim();
  return `Medical monitoring R7 request failed (${response.status})`;
}

export function createMedicalMonitoringR7ProgressApi({
  fetchImpl = globalThis.fetch,
  baseUrl = "",
} = {}) {
  if (typeof fetchImpl !== "function") {
    throw new TypeError("fetchImpl must be a function");
  }

  async function request(method, path, { signal } = {}) {
    const url = joinBaseUrl(baseUrl, path);
    // Action endpoints accept an empty body server-side; the client sends
    // none. Errors are never swallowed: non-2xx raises with the server
    // payload preserved on `detail`, and fetch rejections propagate.
    const response = await fetchImpl(url, {
      method,
      headers: { Accept: "application/json" },
      signal,
    });
    const payload = await responsePayload(response);
    if (!response.ok) {
      throw new MedicalMonitoringApiError(errorMessage(payload, response), {
        status: response.status,
        url,
        detail: payload,
      });
    }
    return payload;
  }

  return Object.freeze({
    getProgress(projectId, runRef, { signal } = {}) {
      return request(
        "GET",
        MEDICAL_MONITORING_R7_PROGRESS_PATHS.progress(
          requireId(projectId, "projectId"),
          requireId(runRef, "runRef"),
        ),
        { signal },
      );
    },

    startExecution(projectId, runRef, { signal } = {}) {
      return request(
        "POST",
        MEDICAL_MONITORING_R7_PROGRESS_PATHS.executionStart(
          requireId(projectId, "projectId"),
          requireId(runRef, "runRef"),
        ),
        { signal },
      );
    },

    cancelExecution(projectId, runRef, { signal } = {}) {
      return request(
        "POST",
        MEDICAL_MONITORING_R7_PROGRESS_PATHS.executionCancel(
          requireId(projectId, "projectId"),
          requireId(runRef, "runRef"),
        ),
        { signal },
      );
    },

    resumeExecution(projectId, runRef, { signal } = {}) {
      return request(
        "POST",
        MEDICAL_MONITORING_R7_PROGRESS_PATHS.executionResume(
          requireId(projectId, "projectId"),
          requireId(runRef, "runRef"),
        ),
        { signal },
      );
    },
  });
}
