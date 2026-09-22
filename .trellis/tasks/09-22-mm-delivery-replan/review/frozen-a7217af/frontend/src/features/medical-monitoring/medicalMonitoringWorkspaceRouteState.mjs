export const MEDICAL_MONITORING_WORKSPACE_VIEWS = Object.freeze([
  "overview",
  "site_overview",
  "queries",
  "journey",
  "profile",
  "timeline",
  "evidence",
]);

export const MEDICAL_MONITORING_WORKSPACE_CANONICAL_KEYS = Object.freeze([
  "project_ref",
  "run_ref",
  "snapshot_ref",
  "cutoff_state",
  "cutoff_ref",
  "public_run_token",
  "result_context_token",
  "site_ref",
  "subject_ref",
  "risk_ref",
  "risk_instance_ref",
  "flow_stage_ref",
  "flow_node_metric",
  "flow_link_ref",
  "flow_risk_band",
  "view",
  "spine_ref",
  "axis_mode",
  "window_start",
  "window_end",
  "visit_ref",
  "event_ref",
  "risk_anchor_ref",
  "source_locator_ref",
  "return_context_key",
]);

export const MEDICAL_MONITORING_WORKSPACE_FLOW_NODE_METRICS = Object.freeze(["current", "reached"]);
export const MEDICAL_MONITORING_WORKSPACE_FLOW_RISK_BANDS = Object.freeze(["mid_high"]);

export const MEDICAL_MONITORING_WORKSPACE_EPHEMERAL_KEYS = Object.freeze([
  "scroll_refs",
  "inspector_width",
  "inspector_expanded",
  "temporary_expansion_refs",
  "focus_ref",
]);

const WORKSPACE_VIEW_SET = new Set(MEDICAL_MONITORING_WORKSPACE_VIEWS);
const WORKSPACE_AXIS_MODES = new Set(["calendar", "study_day"]);
const WORKSPACE_FLOW_NODE_METRIC_SET = new Set(MEDICAL_MONITORING_WORKSPACE_FLOW_NODE_METRICS);
const WORKSPACE_FLOW_RISK_BAND_SET = new Set(MEDICAL_MONITORING_WORKSPACE_FLOW_RISK_BANDS);
const WORKSPACE_QUERY_KEYS = new Set([
  "project_id",
  "run_id",
  "snapshot_id",
  "cutoff",
  "public_run_token",
  "result_context_token",
  "scope",
  "site_id",
  "subject_id",
  "risk_key",
  "risk_instance_id",
  "view",
  "spine_id",
  "axis_mode",
  "start",
  "end",
  "site_ref",
  "subject_ref",
  "spine_ref",
  "window_start",
  "window_end",
  "risk_instance_ref",
  "visit_ref",
  "event_ref",
  "risk_anchor_ref",
  "source_locator_ref",
  "return_context_key",
  "flow_stage_ref",
  "flow_node_metric",
  "flow_link_ref",
  "flow_risk_band",
]);

const PUBLIC_TO_CANONICAL = Object.freeze({
  project_id: "project_ref",
  run_id: "run_ref",
  snapshot_id: "snapshot_ref",
  cutoff: "cutoff_ref",
  public_run_token: "public_run_token",
  result_context_token: "result_context_token",
  site_id: "site_ref",
  subject_id: "subject_ref",
  risk_key: "risk_ref",
  risk_instance_id: "risk_instance_ref",
  spine_id: "spine_ref",
  start: "window_start",
  end: "window_end",
  view: "view",
  axis_mode: "axis_mode",
  visit_ref: "visit_ref",
  event_ref: "event_ref",
  risk_anchor_ref: "risk_anchor_ref",
  source_locator_ref: "source_locator_ref",
  return_context_key: "return_context_key",
  flow_stage_ref: "flow_stage_ref",
  flow_node_metric: "flow_node_metric",
  flow_link_ref: "flow_link_ref",
  flow_risk_band: "flow_risk_band",
});
const PUBLIC_RESULT_QUERY_TO_CANONICAL = Object.freeze({
  site_ref: "site_ref",
  subject_ref: "subject_ref",
  spine_ref: "spine_ref",
  window_start: "window_start",
  window_end: "window_end",
  risk_instance_ref: "risk_instance_ref",
  visit_ref: "visit_ref",
  event_ref: "event_ref",
  risk_anchor_ref: "risk_anchor_ref",
  source_locator_ref: "source_locator_ref",
});

const CANONICAL_TO_PUBLIC = Object.freeze(Object.fromEntries(
  Object.entries(PUBLIC_TO_CANONICAL).map(([publicKey, canonicalKey]) => [canonicalKey, publicKey]),
));

function clean(value) {
  if (value === null || value === undefined) return "";
  return String(value).trim();
}

function paramsFrom(input) {
  if (input instanceof URLSearchParams) return new URLSearchParams(input);
  if (input instanceof URL) return new URLSearchParams(input.searchParams);
  if (input && typeof input === "object" && typeof input.search === "string") {
    return new URLSearchParams(input.search);
  }
  const raw = typeof input === "string" ? input.trim() : "";
  if (!raw) return new URLSearchParams();
  if (/^[a-z][a-z\d+.-]*:\/\//i.test(raw)) return new URL(raw).searchParams;
  return new URLSearchParams(raw.startsWith("?") ? raw.slice(1) : raw);
}

function result(status, fields = {}) {
  return Object.freeze({
    isWorkspace: status !== "legacy",
    status,
    valid: status === "valid",
    ...fields,
  });
}

function resolveFlowSelection(source, keyOrder) {
  const order = Array.isArray(keyOrder) && keyOrder.length ? keyOrder : Object.keys(source || {});
  let stageRef = clean(source?.flow_stage_ref);
  let linkRef = clean(source?.flow_link_ref);
  if (stageRef && linkRef) {
    // 阶段与连线同时出现时只保留最近一次选择（后写入者），不得求交成空表。
    if (order.indexOf("flow_link_ref") > order.indexOf("flow_stage_ref")) stageRef = "";
    else linkRef = "";
  }
  let nodeMetric = clean(source?.flow_node_metric);
  if (!stageRef || linkRef) nodeMetric = "";
  else if (!WORKSPACE_FLOW_NODE_METRIC_SET.has(nodeMetric)) nodeMetric = "current";
  let riskBand = clean(source?.flow_risk_band);
  if (riskBand && !WORKSPACE_FLOW_RISK_BAND_SET.has(riskBand)) riskBand = "";
  return { flow_stage_ref: stageRef, flow_node_metric: nodeMetric, flow_link_ref: linkRef, flow_risk_band: riskBand };
}

function applyFlowSelection(target, selection) {
  for (const key of ["flow_stage_ref", "flow_node_metric", "flow_link_ref", "flow_risk_band"]) {
    if (selection[key]) target[key] = selection[key];
    else delete target[key];
  }
  return target;
}

function identityFailure(canonical, unknownKeys) {
  const missing = [];
  if (!canonical.project_ref) missing.push("project_ref");

  const publicResult = Boolean(canonical.result_context_token);
  const publicProgress = Boolean(canonical.public_run_token) && !publicResult;
  if (publicResult) {
    // Public result URLs carry only result-context and public locator fields.
    // Internal authority references and the legacy risk key are never accepted.
    if (canonical.run_ref || canonical.snapshot_ref || canonical.cutoff_ref || canonical.risk_ref || canonical.return_context_key || canonical.public_run_token) {
      return { code: "PUBLIC_RESULT_INTERNAL_IDENTITY", fields: ["result_context_token"] };
    }
    if (canonical.view === "site_overview" && !canonical.site_ref) missing.push("site_ref");
    if (["journey", "profile", "timeline"].includes(canonical.view)) {
      for (const key of ["site_ref", "subject_ref", "spine_ref", "window_start", "window_end"]) {
        if (!canonical[key]) missing.push(key);
      }
    }
    if (canonical.view === "evidence") {
      for (const key of ["risk_instance_ref", "source_locator_ref"]) {
        if (!canonical[key]) missing.push(key);
      }
    }
  } else if (publicProgress) {
    if (canonical.run_ref || canonical.snapshot_ref || canonical.cutoff_ref || canonical.risk_ref || canonical.return_context_key) {
      return { code: "PUBLIC_PROGRESS_INTERNAL_IDENTITY", fields: ["public_run_token"] };
    }
  } else {
    if (canonical.view === "site_overview" && !canonical.site_ref) missing.push("site_ref");
    if (["journey", "profile", "timeline"].includes(canonical.view)) {
      for (const key of [
        "run_ref",
        "snapshot_ref",
        "cutoff_ref",
        "site_ref",
        "subject_ref",
        "spine_ref",
        "window_start",
        "window_end",
      ]) {
        if (!canonical[key]) missing.push(key);
      }
    }
    if (canonical.view === "evidence") {
      for (const key of ["run_ref", "snapshot_ref", "cutoff_ref", "risk_instance_ref", "source_locator_ref"]) {
        if (!canonical[key]) missing.push(key);
      }
    }
  }
  if (canonical.risk_instance_ref && !canonical.risk_ref && !publicResult) missing.push("risk_ref");
  if (canonical.risk_ref && !canonical.risk_instance_ref && !publicResult) missing.push("risk_instance_ref");
  if (canonical.window_start && !canonical.window_end) missing.push("window_end");
  if (canonical.window_end && !canonical.window_start) missing.push("window_start");
  if (canonical.axis_mode && !WORKSPACE_AXIS_MODES.has(canonical.axis_mode)) missing.push("axis_mode");
  if (canonical.flow_node_metric && !WORKSPACE_FLOW_NODE_METRIC_SET.has(canonical.flow_node_metric)) missing.push("flow_node_metric");
  if (canonical.flow_risk_band && !WORKSPACE_FLOW_RISK_BAND_SET.has(canonical.flow_risk_band)) missing.push("flow_risk_band");
  if (!publicResult && !publicProgress) {
    const authorityRefs = [canonical.run_ref, canonical.snapshot_ref, canonical.cutoff_ref].filter(Boolean);
    if (authorityRefs.length > 0 && authorityRefs.length < 3) {
      for (const key of ["run_ref", "snapshot_ref", "cutoff_ref"]) if (!canonical[key]) missing.push(key);
    }
  }
  if (unknownKeys.length) return { code: "UNKNOWN_QUERY_KEY", fields: unknownKeys };
  if (missing.length) return { code: "WORKSPACE_IDENTITY_INCOMPLETE", fields: [...new Set(missing)] };
  return null;
}

export function isMedicalMonitoringWorkspaceView(view) {
  return WORKSPACE_VIEW_SET.has(clean(view).toLowerCase());
}

export function parseMedicalMonitoringWorkspaceRouteState(input = "") {
  const params = paramsFrom(input);
  const rawView = clean(params.get("view")).toLowerCase();
  if (!isMedicalMonitoringWorkspaceView(rawView)) return result("legacy", { canonical: {}, unknownKeys: [] });

  const unknownKeys = [...new Set([...params.keys()].filter((key) => !WORKSPACE_QUERY_KEYS.has(key)))];
  const canonical = {};
  for (const [publicKey, canonicalKey] of Object.entries(PUBLIC_TO_CANONICAL)) {
    const value = clean(params.get(publicKey));
    if (value) canonical[canonicalKey] = value;
  }
  if (params.has("result_context_token")) {
    for (const [publicKey, canonicalKey] of Object.entries(PUBLIC_RESULT_QUERY_TO_CANONICAL)) {
      const value = clean(params.get(publicKey));
      if (value) canonical[canonicalKey] = value;
    }
  }
  canonical.view = rawView;
  canonical.cutoff_state = canonical.cutoff_ref ? "present" : "absent";
  canonical.axis_mode = canonical.axis_mode || "calendar";
  const failure = identityFailure(canonical, unknownKeys);
  applyFlowSelection(canonical, resolveFlowSelection(canonical, [...params.keys()]));

  return result(failure ? "invalid" : "valid", {
    canonical,
    unknownKeys,
    errorCode: failure?.code || "",
    errorFields: failure?.fields || [],
    publicQuery: Object.freeze(Object.fromEntries(
      [...WORKSPACE_QUERY_KEYS]
        .map((key) => [key, clean(params.get(key))])
        .filter(([, value]) => value),
    )),
  });
}

export function normalizeMedicalMonitoringWorkspaceRouteState(input = {}) {
  const source = input && typeof input === "object" ? input : {};
  const flowSelection = resolveFlowSelection(source, Object.keys(source));
  const normalized = {};
  for (const key of MEDICAL_MONITORING_WORKSPACE_CANONICAL_KEYS) {
    const value = clean(source[key]);
    if (value) normalized[key] = value;
  }
  normalized.view = isMedicalMonitoringWorkspaceView(normalized.view) ? normalized.view : "overview";
  normalized.cutoff_state = normalized.cutoff_ref ? "present" : "absent";
  normalized.axis_mode = WORKSPACE_AXIS_MODES.has(normalized.axis_mode) ? normalized.axis_mode : "calendar";
  applyFlowSelection(normalized, flowSelection);
  return normalized;
}

export function validateMedicalMonitoringWorkspaceTarget(state, { view = state?.view } = {}) {
  const canonical = normalizeMedicalMonitoringWorkspaceRouteState(state);
  const target = view || canonical.view;
  if (!isMedicalMonitoringWorkspaceView(target)) return { valid: false, code: "WORKSPACE_VIEW_INVALID", fields: ["view"] };
  const failure = identityFailure({ ...canonical, view: target }, []);
  return failure
    ? { valid: false, code: failure.code, fields: failure.fields }
    : { valid: true, code: "", fields: [] };
}

export function splitMedicalMonitoringWorkspaceState(state = {}) {
  const canonical = normalizeMedicalMonitoringWorkspaceRouteState(state);
  const source = state && typeof state === "object" ? state : {};
  const ephemeral = {};
  for (const key of MEDICAL_MONITORING_WORKSPACE_EPHEMERAL_KEYS) {
    if (source[key] !== undefined) ephemeral[key] = source[key];
  }
  return Object.freeze({ canonical, ephemeral });
}

export function serializeMedicalMonitoringWorkspaceRouteState(state = {}) {
  const canonical = normalizeMedicalMonitoringWorkspaceRouteState(state);
  const params = new URLSearchParams();
  const publicResult = Boolean(canonical.result_context_token);
  const publicProgress = Boolean(canonical.public_run_token) && !publicResult;
  if (publicResult) {
    for (const [queryKey, canonicalKey] of Object.entries({
      project_id: "project_ref",
      result_context_token: "result_context_token",
      site_ref: "site_ref",
      subject_ref: "subject_ref",
      spine_ref: "spine_ref",
      window_start: "window_start",
      window_end: "window_end",
      risk_instance_ref: "risk_instance_ref",
      risk_anchor_ref: "risk_anchor_ref",
      visit_ref: "visit_ref",
      event_ref: "event_ref",
      source_locator_ref: "source_locator_ref",
      view: "view",
    })) {
      const value = clean(canonical[canonicalKey]);
      if (value) params.set(queryKey, value);
    }
  } else {
    const keys = publicProgress
      ? ["project_ref", "public_run_token", "view"]
      : ["project_ref", "run_ref", "snapshot_ref", "cutoff_ref", "site_ref", "subject_ref", "risk_ref", "risk_instance_ref", "view", "spine_ref", "axis_mode", "window_start", "window_end", "visit_ref", "event_ref", "risk_anchor_ref", "source_locator_ref", "return_context_key", "flow_stage_ref", "flow_node_metric", "flow_link_ref", "flow_risk_band"];
    for (const key of keys) {
      const publicKey = CANONICAL_TO_PUBLIC[key];
      const value = clean(canonical[key]);
      if (publicKey && value) params.set(publicKey, value);
    }
  }
  if (!publicResult && !publicProgress) {
    const requestedScope = clean(state?.scope).toLowerCase();
    const scope = ["trial", "site", "subject"].includes(requestedScope)
      ? requestedScope
      : canonical.subject_ref ? "subject" : canonical.site_ref ? "site" : "trial";
    params.set("scope", scope);
  }
  return params.toString() ? `?${params.toString()}` : "";
}

export function routeStateForMedicalMonitoringWorkspaceView(state, view, patch = {}) {
  const next = normalizeMedicalMonitoringWorkspaceRouteState({ ...state, ...patch, view });
  if (["overview", "site_overview"].includes(view)) {
    if (view === "overview") delete next.site_ref;
    delete next.subject_ref;
    delete next.spine_ref;
    if (!next.return_context_key) {
      delete next.window_start;
      delete next.window_end;
    }
    delete next.visit_ref;
    delete next.event_ref;
    delete next.risk_anchor_ref;
    delete next.source_locator_ref;
    if (!next.return_context_key) {
      delete next.risk_ref;
      delete next.risk_instance_ref;
    }
  }
  if (["journey", "profile", "timeline"].includes(view)) delete next.source_locator_ref;
  return next;
}

export function monitoringSubjectView(view) {
  if (view === "profile") return "trend";
  if (view === "timeline") return "events";
  return "journey";
}

export const medicalMonitoringWorkspaceRouteQueryKeys = Object.freeze([...WORKSPACE_QUERY_KEYS]);
