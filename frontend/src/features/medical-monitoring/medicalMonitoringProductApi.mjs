import { MedicalMonitoringApiError } from "./medicalMonitoringApi.mjs";

const API_PREFIX = "/api/projects";
export const MONITORING_PRODUCT_DEFAULT_HISTORY_LIMIT = 50;

function requireId(value, label) {
  const clean = value === null || value === undefined ? "" : String(value).trim();
  if (!clean) throw new TypeError(`${label} is required`);
  return clean;
}

function encodeSegment(value, label = "path identifier") {
  return encodeURIComponent(requireId(value, label));
}

function projectPath(projectId) {
  return `${API_PREFIX}/${encodeSegment(projectId, "projectId")}/modules/medical-monitoring/r7`;
}

function appendQuery(path, values) {
  const params = new URLSearchParams();
  for (const [key, value] of Object.entries(values || {})) {
    if (value === null || value === undefined || value === "") continue;
    params.set(key, String(value));
  }

  const query = params.toString();
  return query ? `${path}?${query}` : path;
}
function requiredOption(value, label) {
  return requireId(value, label);
}
const PUBLIC_PREPARE_FIELDS = new Set([
  "current_snapshot_token",
  "mode",
  "execution_basis",
  "baseline_token",
  "risk_rule_tokens",
  "idempotency_key",
]);

function publicPreparePayload(payload) {
  if (!payload || typeof payload !== "object" || Array.isArray(payload)) {
    throw new TypeError("prepare payload must be an object");
  }
  const unknown = Object.keys(payload).filter((key) => !PUBLIC_PREPARE_FIELDS.has(key));
  if (unknown.length) {
    throw new TypeError("prepare payload contains a non-public field");
  }
  return { ...payload };
}

// Phase C C1 admission create accepts only the read-only source directory;
// the backend rejects any extra field, so the client fails fast on them too.
const PUBLIC_ADMISSION_CREATE_FIELDS = new Set(["source_dir"]);

function publicAdmissionCreatePayload(payload) {
  if (!payload || typeof payload !== "object" || Array.isArray(payload)) {
    throw new TypeError("admission create payload must be an object");
  }
  const unknown = Object.keys(payload).filter((key) => !PUBLIC_ADMISSION_CREATE_FIELDS.has(key));
  if (unknown.length) {
    throw new TypeError("admission create payload contains a non-public field");
  }
  return { ...payload };
}

function queryValues(values) {
  const source = values && typeof values === "object" && !Array.isArray(values)
    ? values
    : {};
  return Object.fromEntries(
    Object.entries(source).map(([key, value]) => [key, value === undefined || value === null ? value : String(value)]),
  );
}

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
    if (typeof payload.message === "string" && payload.message.trim()) return payload.message;
    if (typeof payload.detail === "string" && payload.detail.trim()) return payload.detail;
    if (payload.detail && typeof payload.detail === "object") {
      if (typeof payload.detail.message === "string" && payload.detail.message.trim()) {
        return payload.detail.message;
      }
      if (typeof payload.detail.code === "string" && payload.detail.code.trim()) {
        return payload.detail.code;
      }
    }
    if (typeof payload.code === "string" && payload.code.trim()) return payload.code;
  }
  if (typeof payload === "string" && payload.trim()) return payload.trim();
  return `医学监查请求失败 (${response.status})`;
}

export const MEDICAL_MONITORING_PRODUCT_PATHS = Object.freeze({
  workspaceBootstrap: (projectId) => `${projectPath(projectId)}/workspace/bootstrap`,
  setupOptions: (projectId, selector = {}) => {
    const options = typeof selector === "string"
      ? { currentSnapshotToken: selector }
      : selector || {};
    return appendQuery(
      `${projectPath(projectId)}/run-setup/options`,
      {
        current_snapshot_token: options.currentSnapshotToken
          || options.snapshotToken
          || options.current_snapshot_token
          || options.snapshot_token,
      },
    );
  },
  riskRulePreview: (projectId) => `${projectPath(projectId)}/risk-rules/preview`,
  riskRules: (projectId) => `${projectPath(projectId)}/risk-rules`,
  prepareAndStart: (projectId) => `${projectPath(projectId)}/runs/prepare-and-start`,
  runs: (projectId, { limit = MONITORING_PRODUCT_DEFAULT_HISTORY_LIMIT } = {}) => appendQuery(
    `${projectPath(projectId)}/runs`,
    { limit },
  ),
  publicProgress: (projectId, publicRunToken) => (
    `${projectPath(projectId)}/runs/${encodeSegment(publicRunToken, "publicRunToken")}/progress`
  ),
  publication: (projectId, publicRunToken) => (
    `${projectPath(projectId)}/runs/${encodeSegment(publicRunToken, "publicRunToken")}/publication`
  ),
  resultEntry: (projectId, publicRunToken) => (
    `${projectPath(projectId)}/runs/${encodeSegment(publicRunToken, "publicRunToken")}/result-entry`
  ),
  resultOverview: (projectId, resultContextToken, options = {}) => appendQuery(
    `${projectPath(projectId)}/results/${encodeSegment(resultContextToken, "resultContextToken")}/overview`,
    { site_ref: options?.siteRef || options?.site_ref },
  ),
  resultSubject: (
    projectId,
    resultContextToken,
    subjectRef,
    options = {},
  ) => appendQuery(
    `${projectPath(projectId)}/results/${encodeSegment(resultContextToken, "resultContextToken")}/subjects/${encodeSegment(subjectRef, "subjectRef")}`,
    {
      site_ref: options?.siteRef || options?.site_ref,
      spine_ref: options?.spineRef || options?.spine_ref,
      window_start: options?.windowStart || options?.window_start,
      window_end: options?.windowEnd || options?.window_end,
      risk_instance_ref: options?.riskInstanceRef || options?.risk_instance_ref,
      risk_anchor_ref: options?.riskAnchorRef || options?.risk_anchor_ref,
      visit_ref: options?.visitRef || options?.visit_ref,
      event_ref: options?.eventRef || options?.event_ref,
    },
  ),
  resultSourceEvidence: (
    projectId,
    resultContextToken,
    options = {},
  ) => appendQuery(
    `${projectPath(projectId)}/results/${encodeSegment(resultContextToken, "resultContextToken")}/source-evidence`,
    {
      risk_instance_ref: options?.riskInstanceRef || options?.risk_instance_ref,
      source_locator_ref: options?.sourceLocatorRef || options?.source_locator_ref,
    },
  ),
  // Slice-08C-2: read-only continuity comparison. Only the existing optional
  // `site_ref` query is accepted; no request body is ever sent.
  resultContinuity: (
    projectId,
    resultContextToken,
    options = {},
  ) => appendQuery(
    `${projectPath(projectId)}/results/${encodeSegment(resultContextToken, "resultContextToken")}/continuity`,
    { site_ref: options?.siteRef || options?.site_ref },
  ),
  // Phase C C1 data admission: create posts only `source_dir`; status and
  // profile are read-only GETs on the attempt id. Paths, hashes and internal
  // object ids stay inside the server-side `technical_details` projection and
  // are never constructed here.
  dataAdmissionCreate: (projectId) => `${projectPath(projectId)}/data-admissions`,
  dataAdmissionUpload: (projectId) => `${projectPath(projectId)}/data-admissions/upload`,
  dataAdmissionLatest: (projectId) => `${projectPath(projectId)}/data-admissions/latest`,
  dataAdmissionStatus: (projectId, attemptId) => (
    `${projectPath(projectId)}/data-admissions/${encodeSegment(attemptId, "attemptId")}`
  ),
  dataAdmissionProfile: (projectId, attemptId) => (
    `${projectPath(projectId)}/data-admissions/${encodeSegment(attemptId, "attemptId")}/profile`
  ),
  dataAdmissionStudyDocuments: (projectId, attemptId) => (
    `${projectPath(projectId)}/data-admissions/${encodeSegment(attemptId, "attemptId")}/study-documents`
  ),
  dataAdmissionStudyDocumentsAnalyze: (projectId, attemptId) => (
    `${MEDICAL_MONITORING_PRODUCT_PATHS.dataAdmissionStudyDocuments(projectId, attemptId)}/analyze`
  ),
  dataAdmissionStudyDocumentsResolve: (projectId, attemptId) => (
    `${MEDICAL_MONITORING_PRODUCT_PATHS.dataAdmissionStudyDocuments(projectId, attemptId)}/resolve`
  ),
  dataAdmissionMappingCandidates: (projectId, attemptId, options = {}) => appendQuery(
    `${projectPath(projectId)}/data-admissions/${encodeSegment(attemptId, "attemptId")}/mapping-candidates`,
    { focus: options?.focus },
  ),
  dataAdmissionMappingDraft: (projectId, attemptId) => (
    `${projectPath(projectId)}/data-admissions/${encodeSegment(attemptId, "attemptId")}/mapping-draft`
  ),
  dataAdmissionMappingDraftField: (projectId, attemptId) => (
    `${projectPath(projectId)}/data-admissions/${encodeSegment(attemptId, "attemptId")}/mapping-draft/field`
  ),
  dataAdmissionMappingDraftAdjudicate: (projectId, attemptId) => (
    `${projectPath(projectId)}/data-admissions/${encodeSegment(attemptId, "attemptId")}/mapping-draft/adjudicate`
  ),
  dataAdmissionMappingDraftConfirm: (projectId, attemptId) => (
    `${projectPath(projectId)}/data-admissions/${encodeSegment(attemptId, "attemptId")}/mapping-draft/confirm`
  ),
  dataAdmissionFacts: (projectId, attemptId) => (
    `${projectPath(projectId)}/data-admissions/${encodeSegment(attemptId, "attemptId")}/facts`
  ),
  // Names used by the product layer; each delegates to the same path shape.
  runSetupOptions: (projectId, selector = {}) => MEDICAL_MONITORING_PRODUCT_PATHS.setupOptions(projectId, selector),
  history: (projectId, options = {}) => MEDICAL_MONITORING_PRODUCT_PATHS.runs(projectId, options),
  progress: (projectId, publicRunToken) => MEDICAL_MONITORING_PRODUCT_PATHS.publicProgress(projectId, publicRunToken),
  overview: (projectId, resultContextToken, options = {}) => MEDICAL_MONITORING_PRODUCT_PATHS.resultOverview(projectId, resultContextToken, options),
  subject: (projectId, resultContextToken, subjectRef, options = {}) => MEDICAL_MONITORING_PRODUCT_PATHS.resultSubject(projectId, resultContextToken, subjectRef, options),
  sourceEvidence: (projectId, resultContextToken, options = {}) => MEDICAL_MONITORING_PRODUCT_PATHS.resultSourceEvidence(projectId, resultContextToken, options),
  continuity: (projectId, resultContextToken, options = {}) => MEDICAL_MONITORING_PRODUCT_PATHS.resultContinuity(projectId, resultContextToken, options),
});

// Explicit aliases keep route names readable at call sites without creating a
// second transport implementation. All result reads remain on the public
// result-context prefix; no internal 医学监查数据标识 is accepted here.
export const MEDICAL_MONITORING_PUBLIC_RESULT_PATHS = Object.freeze({
  overview: MEDICAL_MONITORING_PRODUCT_PATHS.resultOverview,
  subject: MEDICAL_MONITORING_PRODUCT_PATHS.resultSubject,
  sourceEvidence: MEDICAL_MONITORING_PRODUCT_PATHS.resultSourceEvidence,
  continuity: MEDICAL_MONITORING_PRODUCT_PATHS.resultContinuity,
});

export function createMedicalMonitoringProductApi({
  fetchImpl = globalThis.fetch,
  baseUrl = "",
} = {}) {
  if (typeof fetchImpl !== "function") {
    throw new TypeError("fetchImpl must be a function");
  }

  async function request(method, path, { signal, body, formBody, headers = {} } = {}) {
    const url = joinBaseUrl(baseUrl, path);
    const hasBody = body !== undefined;
    const hasFormBody = formBody !== undefined;
    const response = await fetchImpl(url, {
      method,
      headers: {
        Accept: "application/json",
        ...(hasBody && !hasFormBody ? { "Content-Type": "application/json" } : {}),
        ...headers,
      },
      ...(hasFormBody ? { body: formBody } : hasBody ? { body: JSON.stringify(body) } : {}),
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

  const get = (path, options = {}) => request("GET", path, options);
  const post = (path, body, options = {}) => request("POST", path, { ...options, body });
  const patch = (path, body, options = {}) => request("PATCH", path, { ...options, body });
  const postForm = (path, formBody, options = {}) => request("POST", path, { ...options, formBody });
  const listRuns = (projectId, { limit = MONITORING_PRODUCT_DEFAULT_HISTORY_LIMIT, signal } = {}) => get(
    MEDICAL_MONITORING_PRODUCT_PATHS.runs(
      requireId(projectId, "projectId"),
      { limit },
    ),
    { signal },
  );
  const getPublicProgress = (projectId, publicRunToken, { signal } = {}) => get(
    MEDICAL_MONITORING_PRODUCT_PATHS.publicProgress(
      requireId(projectId, "projectId"),
      requireId(publicRunToken, "publicRunToken"),
    ),
    { signal },
  );
  const getResultOverview = (projectId, resultContextToken, options = {}) => get(
    MEDICAL_MONITORING_PRODUCT_PATHS.resultOverview(
      requireId(projectId, "projectId"),
      requireId(resultContextToken, "resultContextToken"),
      options || {},
    ),
    { signal: options?.signal },
  );
  const getResultSubject = (
    projectId,
    resultContextToken,
    subjectRef,
    options = {},
  ) => {
    const source = options || {};
    const publicOptions = {
      siteRef: source.siteRef || source.site_ref,
      spineRef: source.spineRef || source.spine_ref,
      windowStart: source.windowStart || source.window_start,
      windowEnd: source.windowEnd || source.window_end,
      riskInstanceRef: source.riskInstanceRef || source.risk_instance_ref,
      riskAnchorRef: source.riskAnchorRef || source.risk_anchor_ref,
      visitRef: source.visitRef || source.visit_ref,
      eventRef: source.eventRef || source.event_ref,
    };
    for (const [value, label] of [
      [publicOptions.siteRef, "siteRef"],
      [publicOptions.spineRef, "spineRef"],
      [publicOptions.windowStart, "windowStart"],
      [publicOptions.windowEnd, "windowEnd"],
    ]) {
      requiredOption(value, label);
    }
    return get(
      MEDICAL_MONITORING_PRODUCT_PATHS.resultSubject(
        requireId(projectId, "projectId"),
        requireId(resultContextToken, "resultContextToken"),
        requireId(subjectRef, "subjectRef"),
        publicOptions,
      ),
      { signal: source.signal },
    );
  };
  const getResultSourceEvidence = (
    projectId,
    resultContextToken,
    options = {},
  ) => {
    const source = options || {};
    const publicOptions = {
      riskInstanceRef: source.riskInstanceRef || source.risk_instance_ref,
      sourceLocatorRef: source.sourceLocatorRef || source.source_locator_ref,
    };
    requiredOption(publicOptions.riskInstanceRef, "riskInstanceRef");
    requiredOption(publicOptions.sourceLocatorRef, "sourceLocatorRef");
    return get(
      MEDICAL_MONITORING_PRODUCT_PATHS.resultSourceEvidence(
        requireId(projectId, "projectId"),
        requireId(resultContextToken, "resultContextToken"),
        publicOptions,
      ),
      { signal: source.signal },
    );
  };
  // Slice-08C-2 continuity read: GET only, optional site_ref query only,
  // no request body; the caller-owned signal enables stale-request abort.
  const getResultContinuity = (
    projectId,
    resultContextToken,
    options = {},
  ) => {
    const source = options || {};
    return get(
      MEDICAL_MONITORING_PRODUCT_PATHS.resultContinuity(
        requireId(projectId, "projectId"),
        requireId(resultContextToken, "resultContextToken"),
        { siteRef: source.siteRef || source.site_ref },
      ),
      { signal: source.signal },
    );
  };

  const api = {
    bootstrapWorkspace(projectId, { signal } = {}) {
      return post(MEDICAL_MONITORING_PRODUCT_PATHS.workspaceBootstrap(
        requireId(projectId, "projectId"),
      ), undefined, { signal });
    },

    // Phase C C1 data admission transport. The create payload is scoped to
    // `source_dir` only; status and profile carry no request body.
    createDataAdmission(projectId, payload, { signal } = {}) {
      return post(MEDICAL_MONITORING_PRODUCT_PATHS.dataAdmissionCreate(
        requireId(projectId, "projectId"),
      ), publicAdmissionCreatePayload(payload), { signal });
    },

    createDataAdmissionUpload(projectId, files, { signal } = {}) {
      const selected = Array.from(files || []);
      if (!selected.length || selected.some((file) => !file || !file.name)) {
        throw new TypeError("admission upload requires selected files");
      }
      const form = new FormData();
      for (const file of selected) {
        form.append("files", file, file.name);
        form.append("relative_paths", file.webkitRelativePath || file.name);
      }
      return postForm(MEDICAL_MONITORING_PRODUCT_PATHS.dataAdmissionUpload(
        requireId(projectId, "projectId"),
      ), form, { signal });
    },

    getLatestDataAdmission(projectId, { signal } = {}) {
      return get(MEDICAL_MONITORING_PRODUCT_PATHS.dataAdmissionLatest(
        requireId(projectId, "projectId"),
      ), { signal });
    },

    getDataAdmissionStatus(projectId, attemptId, { signal } = {}) {
      return get(MEDICAL_MONITORING_PRODUCT_PATHS.dataAdmissionStatus(
        requireId(projectId, "projectId"),
        requireId(attemptId, "attemptId"),
      ), { signal });
    },

    getDataAdmissionProfile(projectId, attemptId, { signal } = {}) {
      return get(MEDICAL_MONITORING_PRODUCT_PATHS.dataAdmissionProfile(
        requireId(projectId, "projectId"),
        requireId(attemptId, "attemptId"),
      ), { signal });
    },

    getDataAdmissionDocumentReadiness(projectId, attemptId, { signal } = {}) {
      return get(MEDICAL_MONITORING_PRODUCT_PATHS.dataAdmissionStudyDocuments(
        requireId(projectId, "projectId"),
        requireId(attemptId, "attemptId"),
      ), { signal });
    },

    uploadStudyDocument(projectId, attemptId, role, file, { signal } = {}) {
      if (!file?.name) throw new TypeError("study document file is required");
      const cleanRole = requireId(role, "documentRole");
      const form = new FormData();
      form.append("file", file, file.name);
      return postForm(appendQuery(
        MEDICAL_MONITORING_PRODUCT_PATHS.dataAdmissionStudyDocuments(
          requireId(projectId, "projectId"),
          requireId(attemptId, "attemptId"),
        ),
        { role: cleanRole },
      ), form, { signal });
    },

    analyzeStudyDocuments(projectId, attemptId, files, { signal } = {}) {
      const selected = Array.from(files || []);
      if (!selected.length || selected.some((file) => !file?.name)) {
        throw new TypeError("study document files are required");
      }
      const form = new FormData();
      for (const file of selected) form.append("files", file, file.name);
      return postForm(
        MEDICAL_MONITORING_PRODUCT_PATHS.dataAdmissionStudyDocumentsAnalyze(
          requireId(projectId, "projectId"),
          requireId(attemptId, "attemptId"),
        ),
        form,
        { signal },
      );
    },

    resolveStudyDocuments(projectId, attemptId, analysisToken, { signal } = {}) {
      return post(
        MEDICAL_MONITORING_PRODUCT_PATHS.dataAdmissionStudyDocumentsResolve(
          requireId(projectId, "projectId"),
          requireId(attemptId, "attemptId"),
        ),
        { batch_id: requireId(analysisToken, "analysisToken") },
        { signal },
      );
    },

    startDataAdmissionMappingCandidates(projectId, attemptId, { signal } = {}) {
      return post(MEDICAL_MONITORING_PRODUCT_PATHS.dataAdmissionMappingCandidates(
        requireId(projectId, "projectId"),
        requireId(attemptId, "attemptId"),
        { focus: undefined },
      ), undefined, { signal });
    },

    listDataAdmissionMappingCandidates(projectId, attemptId, { focus = "critical", signal } = {}) {
      return get(MEDICAL_MONITORING_PRODUCT_PATHS.dataAdmissionMappingCandidates(
        requireId(projectId, "projectId"),
        requireId(attemptId, "attemptId"),
        { focus },
      ), { signal });
    },

    adoptDataAdmissionMappingDraft(projectId, attemptId, payload, { signal } = {}) {
      return post(MEDICAL_MONITORING_PRODUCT_PATHS.dataAdmissionMappingDraft(
        requireId(projectId, "projectId"),
        requireId(attemptId, "attemptId"),
      ), payload, { signal });
    },

    editDataAdmissionMappingDraftField(projectId, attemptId, payload, { signal } = {}) {
      return patch(MEDICAL_MONITORING_PRODUCT_PATHS.dataAdmissionMappingDraftField(
        requireId(projectId, "projectId"),
        requireId(attemptId, "attemptId"),
      ), payload, { signal });
    },

    adjudicateDataAdmissionMappingDraft(projectId, attemptId, payload, { signal } = {}) {
      return post(MEDICAL_MONITORING_PRODUCT_PATHS.dataAdmissionMappingDraftAdjudicate(
        requireId(projectId, "projectId"),
        requireId(attemptId, "attemptId"),
      ), payload, { signal });
    },

    confirmDataAdmissionMappingDraft(projectId, attemptId, payload, { signal } = {}) {
      return post(MEDICAL_MONITORING_PRODUCT_PATHS.dataAdmissionMappingDraftConfirm(
        requireId(projectId, "projectId"),
        requireId(attemptId, "attemptId"),
      ), payload, { signal });
    },

    generateDataAdmissionFacts(projectId, attemptId, { signal } = {}) {
      return post(MEDICAL_MONITORING_PRODUCT_PATHS.dataAdmissionFacts(
        requireId(projectId, "projectId"),
        requireId(attemptId, "attemptId"),
      ), undefined, { signal });
    },

    getDataAdmissionFacts(projectId, attemptId, { signal } = {}) {
      return get(MEDICAL_MONITORING_PRODUCT_PATHS.dataAdmissionFacts(
        requireId(projectId, "projectId"),
        requireId(attemptId, "attemptId"),
      ), { signal });
    },

    getSetupOptions(projectId, options = {}) {
      const source = options || {};
      return get(MEDICAL_MONITORING_PRODUCT_PATHS.setupOptions(
        requireId(projectId, "projectId"),
        source,
      ), { signal: source.signal });
    },

    getRunSetupOptions(projectId, options = {}) {
      const source = options || {};
      return get(MEDICAL_MONITORING_PRODUCT_PATHS.setupOptions(
        requireId(projectId, "projectId"),
        source,
      ), { signal: source.signal });
    },

    previewRiskRule(projectId, payload, { signal } = {}) {
      return post(MEDICAL_MONITORING_PRODUCT_PATHS.riskRulePreview(
        requireId(projectId, "projectId"),
      ), payload, { signal });
    },

    listRiskRules(projectId, { signal } = {}) {
      return get(MEDICAL_MONITORING_PRODUCT_PATHS.riskRules(
        requireId(projectId, "projectId"),
      ), { signal });
    },

    confirmRiskRule(projectId, payload, { signal } = {}) {
      return post(MEDICAL_MONITORING_PRODUCT_PATHS.riskRules(
        requireId(projectId, "projectId"),
      ), payload, { signal });
    },

    prepareAndStart(projectId, payload, { signal } = {}) {
      return post(MEDICAL_MONITORING_PRODUCT_PATHS.prepareAndStart(
        requireId(projectId, "projectId"),
      ), publicPreparePayload(payload), { signal });
    },

    listRuns,
    getHistory: listRuns,
    listHistory: listRuns,
    getRunHistory: listRuns,
    getPublicProgress,
    getPublicRunProgress: getPublicProgress,

    // This name is intentionally public-token-only. The older
    // medicalMonitoringProgressApi remains the shared progress transport
    // compatibility surface and is not used by result pages.
    getProgress: getPublicProgress,

    publishResult(projectId, publicRunToken, payload, { signal } = {}) {
      return post(MEDICAL_MONITORING_PRODUCT_PATHS.publication(
        requireId(projectId, "projectId"),
        requireId(publicRunToken, "publicRunToken"),
      ), payload, { signal });
    },

    getResultEntry(projectId, publicRunToken, { signal } = {}) {
      return get(MEDICAL_MONITORING_PRODUCT_PATHS.resultEntry(
        requireId(projectId, "projectId"),
        requireId(publicRunToken, "publicRunToken"),
      ), { signal });
    },

    getResultOverview,
    getPublicResultOverview: getResultOverview,
    getResultSubject,
    getPublicResultSubject: getResultSubject,
    getResultSourceEvidence,
    getPublicResultSourceEvidence: getResultSourceEvidence,
    getResultContinuity,
    getPublicResultContinuity: getResultContinuity,
    getContinuity: getResultContinuity,
    getResultContext(projectId, publicRunToken, options = {}) {
      return api.getResultEntry(projectId, publicRunToken, options);
    },
    getOverview: getResultOverview,
    getSubjectWorkspace: getResultSubject,
    getSourceEvidence: getResultSourceEvidence,
    appendRiskRule: (projectId, payload, options = {}) => api.confirmRiskRule(projectId, payload, options),
    prepareRun: (projectId, payload, options = {}) => api.prepareAndStart(projectId, payload, options),
  };

  return Object.freeze(api);
}

export function normalizeMonitoringProductQuery(values) {
  return queryValues(values);
}

export { appendQuery as appendMonitoringProductQuery };
