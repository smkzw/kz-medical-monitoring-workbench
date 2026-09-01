import {
  MEDICAL_MONITORING_R5_CANONICAL_KEYS,
  r5SubjectView,
} from "./medicalMonitoringR5RouteState.mjs";

export const MEDICAL_MONITORING_R5_SCHEMA = "medical-monitoring-r5-s7-product-read-model-v0.1";
export const MEDICAL_MONITORING_R5_API_PREFIX = "/api/projects";

const HASH_KEYS = [
  "target_projection_content_hash",
  "authority_hash",
  "source_snapshot_sha256",
  "response_snapshot_sha256",
  "principal_identity_hash",
  "authorization_decision_sha256",
];

const IDENTITY_KEYS = [
  "tenant_id",
  "project_ref",
  "run_ref",
  "snapshot_ref",
  "cutoff_state",
  "cutoff_ref",
  "site_ref",
  "subject_ref",
  "risk_ref",
  "risk_instance_ref",
  "spine_ref",
  "view",
  "axis_mode",
  "window_start",
  "window_end",
  "visit_ref",
  "event_ref",
  "risk_anchor_ref",
  "source_locator_ref",
  "target_projection_content_hash",
  "return_context_key",
  "authority_hash",
  "source_snapshot_sha256",
  "response_snapshot_sha256",
  "principal_identity_hash",
  "authorization_decision_sha256",
  "audit_id",
];

const REQUIRED_IDENTITY_STRINGS = [
  "tenant_id",
  "project_ref",
  "run_ref",
  "snapshot_ref",
  "cutoff_state",
  "view",
  "axis_mode",
  "target_projection_content_hash",
  "return_context_key",
  "authority_hash",
  "source_snapshot_sha256",
  "response_snapshot_sha256",
  "principal_identity_hash",
  "authorization_decision_sha256",
  "audit_id",
];

const DOMAINS = Object.freeze({
  ae: { label: "AE", shape: "rounded_rect", line: "solid" },
  mh: { label: "MH", shape: "bookmark", line: "dot_dash" },
  cm: { label: "合并用药", shape: "capsule", line: "solid" },
  ip: { label: "试验药", shape: "hexagon", line: "step" },
  lab_exam: { label: "检验/检查", shape: "square", line: "trend" },
  hospital_procedure: { label: "住院/操作", shape: "doorframe", line: "solid" },
  symptom_efficacy: { label: "症状/疗效", shape: "circle", line: "trend" },
  protocol_compliance: { label: "方案符合", shape: "single_flag", line: "bracket" },
});

const SEVERITIES = Object.freeze({
  critical: "紧急",
  high: "高",
  medium: "中",
  low: "低",
});

const DATE_STATES = Object.freeze({
  exact: "精确日期",
  partial: "日期部分明确",
  conflicted: "日期存在冲突",
  missing: "日期待确认",
});

const COVERAGE_STATES = Object.freeze({
  complete: "完整",
  partial: "部分覆盖",
  truncated: "截断",
  small_sample: "样本量较小，暂不评价",
  unknown: "覆盖待确认",
  not_applicable: "不适用",
});

const CHANGE_CAUSES = Object.freeze({
  data: "新增或修订数据",
  coverage: "数据覆盖范围变化",
  rule: "监查规则变化",
  manual: "人工补充条件",
});

const CHANGE_KINDS = Object.freeze({
  initial_current: "当前",
  new: "新增",
  upgraded: "升级",
  continued: "持续",
  downgraded: "降级",
  resolved: "关闭",
  closed: "关闭",
  reopened: "重开",
  needs_rejudgment: "需重新判断",
  superseded: "被替代",
  not_comparable: "暂不可比较",
});

const FLOW_STAGE_KINDS = Object.freeze(["main", "branch_terminal", "unknown", "missing", "not_applicable"]);
const FLOW_PATH_STATES = Object.freeze(["complete", "partial", "conflicted"]);
const FLOW_STAGE_CHANGE_KINDS = Object.freeze({
  initial: "首次记录",
  new: "阶段新增",
  advanced: "阶段前进",
  returned: "阶段退回",
  corrected: "数据已更正",
  unchanged: "与上次相同",
  not_comparable: "暂不可比较",
});

export class MedicalMonitoringR5AdapterError extends Error {
  constructor(code, message, details = {}) {
    super(message);
    this.name = "MedicalMonitoringR5AdapterError";
    this.code = code;
    this.details = details;
    this.status = details.status || 0;
  }
}

function clean(value) {
  if (value === null || value === undefined) return "";
  return String(value).trim();
}

function required(value, name) {
  if (value === null || value === undefined || value === "") {
    throw new MedicalMonitoringR5AdapterError("REQUIRED_FIELD_MISSING", `R5 response field missing: ${name}`, { field: name });
  }
  return value;
}

function hasOwn(value, key) {
  return Boolean(value && Object.prototype.hasOwnProperty.call(value, key));
}

function hash(value, name) {
  if (typeof value !== "string" || !/^[a-f0-9]{64}$/.test(value)) {
    throw new MedicalMonitoringR5AdapterError("DIGEST_INVALID", `R5 response digest invalid: ${name}`, { field: name });
  }
  return value;
}

function requiredString(value, name) {
  if (typeof value !== "string" || !value.trim()) {
    throw new MedicalMonitoringR5AdapterError("REQUIRED_STRING_MISSING", `R5 response string missing: ${name}`, { field: name });
  }
  return value;
}

function canonicalize(value) {
  if (Array.isArray(value)) return value.map(canonicalize);
  if (value && typeof value === "object") {
    return Object.fromEntries(Object.keys(value).sort().map((key) => [key, canonicalize(value[key])]));
  }
  return value;
}

function stripResponseDigest(value, parentKey = "") {
  if (Array.isArray(value)) return value.map((item) => stripResponseDigest(item, parentKey));
  if (value && typeof value === "object") {
    return Object.fromEntries(
      Object.entries(value)
        .filter(([key]) => key !== "response_snapshot_sha256" && !(parentKey === "read_handoff" && key === "contract_sha256"))
        .map(([key, item]) => [key, stripResponseDigest(item, key)]),
    );
  }
  return value;
}

async function sha256Hex(text) {
  if (!globalThis.crypto?.subtle || typeof TextEncoder !== "function") {
    throw new MedicalMonitoringR5AdapterError("DIGEST_UNAVAILABLE", "R5 response digest verification is unavailable in this runtime.");
  }
  const digest = await globalThis.crypto.subtle.digest("SHA-256", new TextEncoder().encode(text));
  return [...new Uint8Array(digest)].map((value) => value.toString(16).padStart(2, "0")).join("");
}

export async function computeMedicalMonitoringR5ResponseDigest(envelope) {
  return sha256Hex(JSON.stringify(canonicalize(stripResponseDigest(envelope))));
}

function array(value, name) {
  if (!Array.isArray(value)) {
    throw new MedicalMonitoringR5AdapterError("SCHEMA_FIELD_INVALID", `R5 response array invalid: ${name}`, { field: name });
  }
  return value;
}

function queryEntries(values, allowed, requiredKeys = []) {
  const source = values && typeof values === "object" ? values : {};
  const entries = [];
  const unknown = Object.keys(source).filter((key) => !allowed.has(key));
  if (unknown.length) {
    throw new MedicalMonitoringR5AdapterError("QUERY_KEY_INVALID", "R5 request query is outside the closed read surface.", { fields: unknown });
  }
  for (const key of requiredKeys) {
    if (!clean(source[key])) {
      throw new MedicalMonitoringR5AdapterError("QUERY_FIELD_MISSING", `R5 request field missing: ${key}`, { field: key });
    }
  }
  for (const [key, value] of Object.entries(source)) {
    const text = clean(value);
    if (text) entries.push([key, text]);
  }
  return entries;
}

function rejectOptionKeys(options, allowed) {
  const unknown = Object.keys(options || {}).filter((key) => !allowed.has(key));
  if (unknown.length) {
    throw new MedicalMonitoringR5AdapterError("QUERY_OPTION_INVALID", "R5 adapter options are outside the closed read surface.", { fields: unknown });
  }
}

function createPath(projectId, suffix) {
  const project = clean(projectId);
  if (!project) throw new TypeError("R5 project identity is required.");
  return `${MEDICAL_MONITORING_R5_API_PREFIX}/${encodeURIComponent(project)}/modules/medical-monitoring/r5/${suffix}`;
}

function endpointUrl(baseUrl, path, entries) {
  const url = new URL(path, baseUrl || "http://workbench.invalid");
  for (const [key, value] of entries) url.searchParams.set(key, value);
  return baseUrl ? url.toString() : `${url.pathname}${url.search}`;
}

async function readResponse(response) {
  const payload = await response.json().catch(() => null);
  if (!response.ok) {
    const detail = payload?.detail?.message || payload?.detail || payload?.message || `HTTP ${response.status}`;
    throw new MedicalMonitoringR5AdapterError("HTTP_READ_FAILED", String(detail), {
      status: response.status,
      payload,
    });
  }
  return payload;
}

function validateIdentity(identity, expected = {}) {
  required(identity, "identity");
  for (const key of IDENTITY_KEYS) {
    if (!hasOwn(identity, key)) {
      throw new MedicalMonitoringR5AdapterError("IDENTITY_FIELD_MISSING", `R5 identity field missing: ${key}`, { field: key });
    }
  }
  for (const key of REQUIRED_IDENTITY_STRINGS) requiredString(identity[key], `identity.${key}`);
  if (!["present", "absent"].includes(identity.cutoff_state)) {
    throw new MedicalMonitoringR5AdapterError("IDENTITY_FIELD_INVALID", "R5 identity cutoff_state is invalid.", { field: "cutoff_state" });
  }
  if (identity.cutoff_state === "present") requiredString(identity.cutoff_ref, "identity.cutoff_ref");
  for (const key of HASH_KEYS) hash(identity[key], `identity.${key}`);
  if (clean(expected.projectRef) && identity.project_ref !== expected.projectRef) {
    throw new MedicalMonitoringR5AdapterError("IDENTITY_PROJECT_MISMATCH", "R5 response project identity does not match the requested project.");
  }
  for (const [expectedKey, identityKey] of [
    ["runRef", "run_ref"],
    ["snapshotRef", "snapshot_ref"],
    ["cutoffRef", "cutoff_ref"],
    ["siteRef", "site_ref"],
    ["subjectRef", "subject_ref"],
    ["spineRef", "spine_ref"],
    ["riskRef", "risk_ref"],
    ["riskInstanceRef", "risk_instance_ref"],
    ["sourceLocatorRef", "source_locator_ref"],
  ]) {
    const expectedValue = clean(expected[expectedKey]);
    if (expectedValue && identity[identityKey] !== expectedValue) {
      throw new MedicalMonitoringR5AdapterError("IDENTITY_TARGET_MISMATCH", `R5 response target identity does not match: ${identityKey}`, { field: identityKey });
    }
  }
  return identity;
}

async function validateEnvelope(payload, expected = {}) {
  required(payload, "response");
  if (payload.schema !== MEDICAL_MONITORING_R5_SCHEMA) {
    throw new MedicalMonitoringR5AdapterError("SCHEMA_MISMATCH", "R5 response schema is not accepted.");
  }
  for (const key of ["authority_receipt", "identity", "projection", "counts", "source_refs", "read_handoff"]) {
    if (!hasOwn(payload, key)) {
      throw new MedicalMonitoringR5AdapterError("SCHEMA_FIELD_MISSING", `R5 response field missing: ${key}`, { field: key });
    }
  }
  if (payload.read_only !== true || payload.mutation_applied !== false || payload.persisted !== false) {
    throw new MedicalMonitoringR5AdapterError("READ_FLAGS_INVALID", "R5 response is not marked as an immutable read.");
  }
  if (hasOwn(payload, "cas_version_before") && payload.cas_version_before !== payload.cas_version_after) {
    throw new MedicalMonitoringR5AdapterError("CAS_CHANGED", "R5 response aggregate changed during the read.");
  }
  if (hasOwn(payload, "aggregate_version_before") && payload.aggregate_version_before !== payload.aggregate_version_after) {
    throw new MedicalMonitoringR5AdapterError("AGGREGATE_CHANGED", "R5 response aggregate changed during the read.");
  }
  const responseHash = hash(payload.response_snapshot_sha256, "response_snapshot_sha256");
  const recomputedResponseHash = await computeMedicalMonitoringR5ResponseDigest(payload);
  if (recomputedResponseHash !== responseHash) {
    throw new MedicalMonitoringR5AdapterError("RESPONSE_DIGEST_MISMATCH", "R5 response bytes are not bound to response_snapshot_sha256.");
  }
  const identity = validateIdentity(payload.identity, expected);
  if (identity.response_snapshot_sha256 !== responseHash) {
    throw new MedicalMonitoringR5AdapterError("DIGEST_IDENTITY_MISMATCH", "R5 response digest is not bound to its identity trace.");
  }
  const receipt = required(payload.authority_receipt, "authority_receipt");
  for (const key of ["project_ref", "run_ref", "snapshot_ref", "cutoff_ref"]) {
    if (!hasOwn(receipt, key)) {
      throw new MedicalMonitoringR5AdapterError("RECEIPT_FIELD_MISSING", `R5 authority receipt field missing: ${key}`, { field: key });
    }
    if (receipt[key] !== identity[key]) {
      throw new MedicalMonitoringR5AdapterError("RECEIPT_IDENTITY_MISMATCH", `R5 authority receipt mismatch: ${key}`, { field: key });
    }
  }
  const projectionHash = hash(payload.projection.content_hash, "projection.content_hash");
  if (identity.target_projection_content_hash !== projectionHash) {
    throw new MedicalMonitoringR5AdapterError("PROJECTION_DIGEST_MISMATCH", "R5 projection content is not bound to its identity trace.");
  }
  if (hasOwn(receipt, "authority_hash")) hash(receipt.authority_hash, "authority_receipt.authority_hash");
  if (hasOwn(receipt, "source_snapshot_sha256")) hash(receipt.source_snapshot_sha256, "authority_receipt.source_snapshot_sha256");
  if (hasOwn(receipt, "projectable") && receipt.projectable !== true) {
    throw new MedicalMonitoringR5AdapterError("PROJECTION_NOT_PROJECTABLE", "R5 authority receipt does not permit this projection.");
  }
  array(payload.source_refs, "source_refs");
  const readHandoff = required(payload.read_handoff, "read_handoff");
  const handoffResponseHash = hash(readHandoff.response_snapshot_sha256, "read_handoff.response_snapshot_sha256");
  if (handoffResponseHash !== responseHash) {
    throw new MedicalMonitoringR5AdapterError("DIGEST_HANDOFF_MISMATCH", "R5 read handoff is not bound to response_snapshot_sha256.");
  }
  return { ...payload, identity, response_snapshot_sha256: responseHash };
}

function severityLabel(value) {
  return SEVERITIES[value] || "风险等级待确认";
}

function dateLabel(value) {
  return DATE_STATES[value] || "日期待确认";
}

function coverageLabel(value) {
  return COVERAGE_STATES[value] || "覆盖待确认";
}

function changeLabel(value) {
  return CHANGE_KINDS[value] || "变化待确认";
}

function domainEncoding(value = {}) {
  if (!value || typeof value !== "object" || Array.isArray(value)) {
    throw new MedicalMonitoringR5AdapterError("DOMAIN_ENCODING_INVALID", "R5 projection domain encoding must be an object.");
  }
  const domain = requiredString(value.domain, "domain_encoding.domain");
  if (!DOMAINS[domain]) {
    throw new MedicalMonitoringR5AdapterError("DOMAIN_UNKNOWN", "R5 projection contains a domain outside the accepted eight-domain registry.", { domain });
  }
  return {
    domain,
    shortLabel: requiredString(value.short_label_zh, `domain_encoding.${domain}.short_label_zh`),
    shape: requiredString(value.event_shape, `domain_encoding.${domain}.event_shape`),
    lineStyle: requiredString(value.line_style, `domain_encoding.${domain}.line_style`),
  };
}

function normalizeRisk(value = {}, domainRegistry = new Map()) {
  if (!value || typeof value !== "object" || Array.isArray(value)) {
    throw new MedicalMonitoringR5AdapterError("RISK_SCHEMA_INVALID", "R5 current-risk row must be an object.");
  }
  const riskRef = requiredString(value.risk_key || value.risk_ref, "current_risk.risk_ref");
  const riskInstanceRef = requiredString(value.risk_instance_ref || value.risk_instance_id, "current_risk.risk_instance_ref");
  const siteRef = requiredString(value.site_ref || value.site_id, "current_risk.site_ref");
  const subjectRef = requiredString(value.subject_ref || value.subject_id, "current_risk.subject_ref");
  const spineRef = requiredString(value.spine_ref, "current_risk.spine_ref");
  const severity = requiredString(value.severity, "current_risk.severity").toLowerCase();
  if (!Object.prototype.hasOwnProperty.call(SEVERITIES, severity)) {
    throw new MedicalMonitoringR5AdapterError("RISK_SEVERITY_UNKNOWN", "R5 current-risk severity is outside the accepted registry.", { severity });
  }
  const dateState = requiredString(value.date_state, "current_risk.date_state");
  if (!Object.prototype.hasOwnProperty.call(DATE_STATES, dateState)) {
    throw new MedicalMonitoringR5AdapterError("RISK_DATE_STATE_UNKNOWN", "R5 current-risk date state is outside the accepted registry.", { dateState });
  }
  const changeKind = requiredString(value.change_kind, "current_risk.change_kind");
  if (!Object.prototype.hasOwnProperty.call(CHANGE_KINDS, changeKind)) {
    throw new MedicalMonitoringR5AdapterError("RISK_CHANGE_KIND_UNKNOWN", "R5 current-risk change kind is outside the accepted registry.", { changeKind });
  }
  const riskType = requiredString(value.risk_type_zh || value.risk_type || value.title, "current_risk.risk_type_zh");
  const riskAnchorRef = requiredString(value.risk_anchor_ref, "current_risk.risk_anchor_ref");
  const domain = typeof value.domain === "object"
    ? domainEncoding(value.domain)
    : domainRegistry.get(requiredString(value.domain, "current_risk.domain"));
  if (!domain) {
    throw new MedicalMonitoringR5AdapterError("DOMAIN_ENCODING_MISSING", "R5 current-risk domain has no authoritative encoding.", { domain: value.domain });
  }
  if (value.source_locator_refs !== undefined && !Array.isArray(value.source_locator_refs)) {
    throw new MedicalMonitoringR5AdapterError("RISK_SOURCE_REFS_INVALID", "R5 current-risk source locator refs must be an array.");
  }
  return {
    ...value,
    riskRef,
    riskInstanceRef,
    siteRef,
    subjectRef,
    spineRef,
    domain: domain.domain,
    domainEncoding: domain,
    domainStatus: "confirmed",
    severity,
    severityLabel: severityLabel(severity),
    riskType,
    subjectLabel: clean(value.subject_label || value.subject_name),
    siteLabel: clean(value.site_label || value.site_name),
    dateState,
    dateLabel: dateLabel(dateState),
    changeKind,
    changeLabel: changeLabel(changeKind),
    changeCauseLabel: CHANGE_CAUSES[value.change_cause] || "变化原因待确认",
    eventRef: clean(value.event_ref),
    riskAnchorRef,
    sourceLocatorRef: clean(value.source_locator_ref || value.source_locator_refs?.[0]),
    evidenceSummary: value.evidence_summary || null,
    analysisDisagreement: value.analysis_disagreement || null,
    riskStatus: "confirmed",
  };
}

function normalizeMeasure(value = {}) {
  return {
    ...value,
    numerator: value.numerator_value ?? value.numerator ?? null,
    denominator: value.denominator_value ?? value.denominator ?? null,
    coverageState: clean(value.coverage_state || measures[0]?.coverageState) || "unknown",
    coverageLabel: coverageLabel(value.coverage_state || measures[0]?.coverageState),
    unit: clean(value.unit) === "subject" ? "受试者" : clean(value.unit) || "受试者",
  };
}

function normalizeCenter(value = {}, measureCatalog = new Map(), domainRegistry = new Map()) {
  if (!value || typeof value !== "object" || Array.isArray(value)) {
    throw new MedicalMonitoringR5AdapterError("CENTER_CELL_INVALID", "R5 center_map cell must be an object.");
  }
  const siteRef = requiredString(value.site_ref || value.site_id, "center_map.cells.site_ref");
  const measures = Array.isArray(value.measures)
    ? value.measures.map(normalizeMeasure)
    : Array.isArray(value.measure_refs)
      ? value.measure_refs.map((ref) => {
        const measure = measureCatalog.get(ref);
        if (!measure) throw new MedicalMonitoringR5AdapterError("MEASURE_NOT_BOUND", "R5 center measure ref is not bound to a measure.", { measureRef: ref });
        return normalizeMeasure({ ...measure, measure_ref: ref });
      })
      : [];
  return {
    ...value,
    siteRef,
    siteLabel: clean(value.site_label || value.site_name),
    measures,
    risks: Array.isArray(value.risks) ? value.risks.map((risk) => normalizeRisk(risk, domainRegistry)) : [],
    coverageState: clean(value.coverage_state) || "unknown",
    coverageLabel: coverageLabel(value.coverage_state),
  };
}

function normalizeEvent(value = {}) {
  const domain = domainEncoding({ ...(value.encoding || {}), domain: value.domain });
  const eventRef = requiredString(value.event_ref, "event.event_ref");
  const subtype = requiredString(value.subtype, "event.subtype");
  const dateState = requiredString(value.date_state, "event.date_state");
  if (!Object.prototype.hasOwnProperty.call(DATE_STATES, dateState)) {
    throw new MedicalMonitoringR5AdapterError("EVENT_DATE_STATE_UNKNOWN", "R5 event date state is outside the accepted registry.", { dateState });
  }
  const eventLabel = requiredString(value.event_label || value.label_zh || value.label, "event.label_zh");
  if (value.risk_anchor_refs !== undefined && !Array.isArray(value.risk_anchor_refs)) {
    throw new MedicalMonitoringR5AdapterError("EVENT_RISK_ANCHORS_INVALID", "R5 event risk anchors must be an array.");
  }
  if (value.source_locator_refs !== undefined && !Array.isArray(value.source_locator_refs)) {
    throw new MedicalMonitoringR5AdapterError("EVENT_SOURCE_REFS_INVALID", "R5 event source locator refs must be an array.");
  }
  return {
    ...value,
    eventRef,
    domain: domain.domain,
    domainEncoding: domain,
    subtype,
    start: value.start ?? value.start_date ?? null,
    end: value.end ?? value.end_date ?? null,
    dateState,
    dateLabel: dateLabel(dateState),
    riskAnchorRefs: Array.isArray(value.risk_anchor_refs) ? value.risk_anchor_refs : [],
    sourceLocatorRefs: Array.isArray(value.source_locator_refs) ? value.source_locator_refs : [],
    eventLabel,
  };
}

function normalizeIndicator(value = {}, index = 0) {
  if (!value || typeof value !== "object" || Array.isArray(value)) {
    throw new MedicalMonitoringR5AdapterError("INDICATOR_SCHEMA_INVALID", "R5 indicator must be an object.", { index });
  }
  const indicatorRef = requiredString(value.indicator_ref || value.metric_ref || value.id, `indicator[${index}].indicator_ref`);
  const label = requiredString(value.label || value.label_zh || value.indicator_label, `indicator[${index}].label`);
  const rawPoints = value.points ?? value.trend_points ?? value.values;
  if (!Array.isArray(rawPoints)) {
    throw new MedicalMonitoringR5AdapterError("INDICATOR_POINTS_INVALID", "R5 indicator trend points are missing or invalid.", { index });
  }
  const points = rawPoints.map((point, pointIndex) => {
    if (!point || typeof point !== "object" || Array.isArray(point)) {
      throw new MedicalMonitoringR5AdapterError("INDICATOR_POINT_INVALID", "R5 indicator point is invalid.", { index, pointIndex });
    }
    return {
      ...point,
      date: clean(point.date || point.event_date || point.x) || null,
      value: point.value ?? point.y ?? null,
    };
  });
  return { ...value, indicatorRef, label, points };
}

function countValue(value, name) {
  if (value === null || value === undefined || value === "") return null;
  if (!Number.isInteger(value) || value < 0) {
    throw new MedicalMonitoringR5AdapterError("COUNT_INVALID", `R5 authoritative count invalid: ${name}`, { field: name });
  }
  return value;
}

function normalizeCounts(value = {}) {
  if (!value || typeof value !== "object" || Array.isArray(value)) {
    throw new MedicalMonitoringR5AdapterError("COUNTS_SCHEMA_INVALID", "R5 authoritative counts must be an object.");
  }
  const current = value.current_risk || value.currentRisk || value.current_risk_counts || {};
  if (!current || typeof current !== "object" || Array.isArray(current)) {
    throw new MedicalMonitoringR5AdapterError("COUNTS_SCHEMA_INVALID", "R5 current-risk counts must be an object.");
  }
  return {
    ...value,
    currentRisk: {
      critical: countValue(current.critical ?? value.current_critical_risk ?? value.current_risk_critical, "currentRisk.critical"),
      high: countValue(current.high ?? value.current_high_risk ?? value.current_risk_high, "currentRisk.high"),
      medium: countValue(current.medium ?? value.current_medium_risk ?? value.current_risk_medium, "currentRisk.medium"),
      low: countValue(current.low ?? value.current_low_risk ?? value.current_risk_low, "currentRisk.low"),
      total: countValue(current.total ?? value.current_risk_total, "currentRisk.total"),
    },
    changeBand: countValue(
      value.change_band_count
        ?? value.change_bands_count
        ?? value.current_change_band_count
        ?? (typeof value.change_band === "number" ? value.change_band : value.change_band?.count)
        ?? (typeof value.changeBand === "number" ? value.changeBand : value.changeBand?.count),
      "changeBand",
    ),
  };
}

function flowCount(value, name) {
  if (!Number.isInteger(value) || value < 0) {
    throw new MedicalMonitoringR5AdapterError("SUBJECT_FLOW_FIELD_INVALID", `R5 subject_flow count invalid: ${name}`, { field: name });
  }
  return value;
}

function flowBoolean(value, name) {
  if (typeof value !== "boolean") {
    throw new MedicalMonitoringR5AdapterError("SUBJECT_FLOW_FIELD_INVALID", `R5 subject_flow flag invalid: ${name}`, { field: name });
  }
  return value;
}

function flowEnum(value, registry, name, errorSuffix) {
  const text = requiredString(value, name);
  if (!registry.includes(text)) {
    throw new MedicalMonitoringR5AdapterError("SUBJECT_FLOW_FIELD_INVALID", `R5 subject_flow ${errorSuffix} is outside the accepted registry: ${name}`, { field: name, value: text });
  }
  return text;
}

function flowLocatorRefs(value, name) {
  if (value === undefined || value === null) return [];
  return array(value, name).map((ref, index) => requiredString(ref, `${name}[${index}]`));
}

function normalizeSubjectFlowStage(stage) {
  if (!stage || typeof stage !== "object" || Array.isArray(stage)) {
    throw new MedicalMonitoringR5AdapterError("SUBJECT_FLOW_FIELD_INVALID", "R5 subject_flow stage must be an object.", { field: "subject_flow.stages" });
  }
  const stageRef = requiredString(stage.stage_ref, "subject_flow.stages[].stage_ref");
  return {
    stageRef,
    stageLabelZh: requiredString(stage.stage_label_zh || stage.stage_label, `subject_flow.stages.${stageRef}.stage_label_zh`),
    columnOrder: flowCount(stage.column_order, `subject_flow.stages.${stageRef}.column_order`),
    rowOrder: flowCount(stage.row_order, `subject_flow.stages.${stageRef}.row_order`),
    stageKind: flowEnum(stage.stage_kind, FLOW_STAGE_KINDS, `subject_flow.stages.${stageRef}.stage_kind`, "stage kind"),
    isEntry: flowBoolean(stage.is_entry, `subject_flow.stages.${stageRef}.is_entry`),
    isTerminal: flowBoolean(stage.is_terminal, `subject_flow.stages.${stageRef}.is_terminal`),
    sourceLocatorRefs: flowLocatorRefs(stage.source_locator_refs, `subject_flow.stages.${stageRef}.source_locator_refs`),
    reachedCount: flowCount(stage.reached_count, `subject_flow.stages.${stageRef}.reached_count`),
    currentCount: flowCount(stage.current_count, `subject_flow.stages.${stageRef}.current_count`),
    currentMidHighRiskCount: flowCount(stage.current_mid_high_risk_count, `subject_flow.stages.${stageRef}.current_mid_high_risk_count`),
  };
}

function normalizeSubjectFlowLink(link, stageRefs) {
  if (!link || typeof link !== "object" || Array.isArray(link)) {
    throw new MedicalMonitoringR5AdapterError("SUBJECT_FLOW_FIELD_INVALID", "R5 subject_flow link must be an object.", { field: "subject_flow.links" });
  }
  const linkRef = requiredString(link.link_ref, "subject_flow.links[].link_ref");
  const fromStageRef = requiredString(link.from_stage_ref, `subject_flow.links.${linkRef}.from_stage_ref`);
  const toStageRef = requiredString(link.to_stage_ref, `subject_flow.links.${linkRef}.to_stage_ref`);
  if (!stageRefs.has(fromStageRef) || !stageRefs.has(toStageRef)) {
    throw new MedicalMonitoringR5AdapterError("SUBJECT_FLOW_REF_UNRESOLVED", `R5 subject_flow link does not resolve to a declared stage: ${linkRef}`, { field: `subject_flow.links.${linkRef}` });
  }
  return {
    linkRef,
    fromStageRef,
    toStageRef,
    count: flowCount(link.count, `subject_flow.links.${linkRef}.count`),
    currentMidHighRiskCount: flowCount(link.current_mid_high_risk_count, `subject_flow.links.${linkRef}.current_mid_high_risk_count`),
  };
}

function normalizeSubjectFlowSubject(row, stageRefs, scopeSiteRef) {
  if (!row || typeof row !== "object" || Array.isArray(row)) {
    throw new MedicalMonitoringR5AdapterError("SUBJECT_FLOW_FIELD_INVALID", "R5 subject_flow subject row must be an object.", { field: "subject_flow.subjects" });
  }
  const subjectRef = requiredString(row.subject_ref, "subject_flow.subjects[].subject_ref");
  const siteRef = requiredString(row.site_ref, `subject_flow.subjects.${subjectRef}.site_ref`);
  if (scopeSiteRef && siteRef !== scopeSiteRef) {
    throw new MedicalMonitoringR5AdapterError("SUBJECT_FLOW_IDENTITY_MISMATCH", `R5 subject_flow subject row is outside the scoped center: ${subjectRef}`, { field: `subject_flow.subjects.${subjectRef}.site_ref` });
  }
  const currentStageRef = requiredString(row.current_stage_ref, `subject_flow.subjects.${subjectRef}.current_stage_ref`);
  if (!stageRefs.has(currentStageRef)) {
    throw new MedicalMonitoringR5AdapterError("SUBJECT_FLOW_REF_UNRESOLVED", `R5 subject_flow subject row does not resolve to a declared stage: ${subjectRef}`, { field: `subject_flow.subjects.${subjectRef}.current_stage_ref` });
  }
  const priorStageRef = clean(row.prior_stage_ref);
  if (priorStageRef && !stageRefs.has(priorStageRef)) {
    throw new MedicalMonitoringR5AdapterError("SUBJECT_FLOW_REF_UNRESOLVED", `R5 subject_flow subject prior stage does not resolve to a declared stage: ${subjectRef}`, { field: `subject_flow.subjects.${subjectRef}.prior_stage_ref` });
  }
  const dateState = clean(row.date_state);
  if (dateState && !Object.prototype.hasOwnProperty.call(DATE_STATES, dateState)) {
    throw new MedicalMonitoringR5AdapterError("SUBJECT_FLOW_FIELD_INVALID", `R5 subject_flow subject date state is outside the accepted registry: ${subjectRef}`, { field: `subject_flow.subjects.${subjectRef}.date_state` });
  }
  const stageChangeKind = clean(row.stage_change_kind);
  if (stageChangeKind && !Object.prototype.hasOwnProperty.call(FLOW_STAGE_CHANGE_KINDS, stageChangeKind)) {
    throw new MedicalMonitoringR5AdapterError("SUBJECT_FLOW_FIELD_INVALID", `R5 subject_flow stage change kind is outside the accepted registry: ${subjectRef}`, { field: `subject_flow.subjects.${subjectRef}.stage_change_kind` });
  }
  const riskChangeKind = clean(row.risk_change_kind);
  if (riskChangeKind && !Object.prototype.hasOwnProperty.call(CHANGE_KINDS, riskChangeKind)) {
    throw new MedicalMonitoringR5AdapterError("SUBJECT_FLOW_FIELD_INVALID", `R5 subject_flow risk change kind is outside the accepted registry: ${subjectRef}`, { field: `subject_flow.subjects.${subjectRef}.risk_change_kind` });
  }
  let currentMidHighRisk = false;
  if (typeof row.current_mid_high_risk === "boolean") currentMidHighRisk = row.current_mid_high_risk;
  else if (row.current_mid_high_risk_count !== undefined && row.current_mid_high_risk_count !== null) {
    currentMidHighRisk = flowCount(row.current_mid_high_risk_count, `subject_flow.subjects.${subjectRef}.current_mid_high_risk_count`) > 0;
  } else if (row.current_mid_high_risk !== undefined && row.current_mid_high_risk !== null) {
    throw new MedicalMonitoringR5AdapterError("SUBJECT_FLOW_FIELD_INVALID", `R5 subject_flow subject risk flag invalid: ${subjectRef}`, { field: `subject_flow.subjects.${subjectRef}.current_mid_high_risk` });
  }
  const jumpWindowStart = clean(row.jump_window_start);
  const jumpWindowEnd = clean(row.jump_window_end);
  if (Boolean(jumpWindowStart) !== Boolean(jumpWindowEnd)) {
    throw new MedicalMonitoringR5AdapterError("SUBJECT_FLOW_WINDOW_INVALID", `R5 subject_flow journey window must be provided as a closed pair: ${subjectRef}`, { field: `subject_flow.subjects.${subjectRef}.jump_window` });
  }
  const pathStageRefs = flowLocatorRefs(row.path_stage_refs, `subject_flow.subjects.${subjectRef}.path_stage_refs`);
  const pathLinkRefs = flowLocatorRefs(row.path_link_refs, `subject_flow.subjects.${subjectRef}.path_link_refs`);
  if (pathStageRefs.some((ref) => !stageRefs.has(ref))) {
    throw new MedicalMonitoringR5AdapterError("SUBJECT_FLOW_REF_UNRESOLVED", `R5 subject_flow subject path does not resolve to declared stages: ${subjectRef}`, { field: `subject_flow.subjects.${subjectRef}.path_stage_refs` });
  }
  return {
    subjectRef,
    subjectLabel: clean(row.subject_label || row.subject_name),
    siteRef,
    siteLabel: clean(row.site_label || row.site_name),
    spineRef: clean(row.spine_ref),
    currentStageRef,
    priorStageRef,
    pathStageRefs,
    pathLinkRefs,
    enteredDate: clean(row.entered_date),
    basisDate: clean(row.basis_date),
    dateState,
    dateLabel: dateState ? dateLabel(dateState) : "",
    transitionReasonZh: clean(row.transition_reason_zh),
    stageChangeKind,
    stageChangeLabel: stageChangeKind ? FLOW_STAGE_CHANGE_KINDS[stageChangeKind] : "",
    riskChangeKind,
    riskChangeLabel: riskChangeKind ? changeLabel(riskChangeKind) : "",
    riskSummaryZh: clean(row.risk_summary_zh),
    currentMidHighRisk,
    pathState: flowEnum(row.path_state, FLOW_PATH_STATES, `subject_flow.subjects.${subjectRef}.path_state`, "path state"),
    jumpWindowStart,
    jumpWindowEnd,
    jumpWindowAvailable: Boolean(jumpWindowStart && jumpWindowEnd),
  };
}

function normalizeSubjectFlow(value, identity) {
  if (value === undefined || value === null) return null;
  if (!value || typeof value !== "object" || Array.isArray(value)) {
    throw new MedicalMonitoringR5AdapterError("SUBJECT_FLOW_SCHEMA_INVALID", "R5 subject_flow projection must be an object.");
  }
  const availability = requiredString(value.availability, "subject_flow.availability");
  if (!["available", "not_provided"].includes(availability)) {
    throw new MedicalMonitoringR5AdapterError("SUBJECT_FLOW_AVAILABILITY_INVALID", "R5 subject_flow availability is outside the accepted registry.", { field: "subject_flow.availability", value: availability });
  }
  if (availability === "not_provided") {
    const reasonZh = clean(value.reason_zh || value.not_provided_reason_zh);
    if (!reasonZh) {
      throw new MedicalMonitoringR5AdapterError("SUBJECT_FLOW_REASON_MISSING", "R5 subject_flow not-provided state must carry a Chinese reason.", { field: "subject_flow.reason_zh" });
    }
    return {
      raw: value,
      availability,
      visualKind: "",
      scope: null,
      reasonZh,
      blockedReasonZh: "",
      reconciliation: null,
      stages: [],
      links: [],
      subjects: [],
      coverage: {},
    };
  }
  const visualKind = requiredString(value.visual_kind, "subject_flow.visual_kind");
  if (visualKind !== "path_throughput_sankey") {
    throw new MedicalMonitoringR5AdapterError("SUBJECT_FLOW_FIELD_INVALID", "R5 subject_flow visual kind is not the frozen path-throughput surface.", { field: "subject_flow.visual_kind", value: visualKind });
  }
  const scope = value.scope;
  if (!scope || typeof scope !== "object" || Array.isArray(scope)) {
    throw new MedicalMonitoringR5AdapterError("SUBJECT_FLOW_SCHEMA_INVALID", "R5 subject_flow scope must be an object.");
  }
  for (const scopeKey of ["project_ref", "run_ref", "snapshot_ref", "cutoff_ref", "site_ref"]) {
    if (clean(scope[scopeKey]) !== clean(identity[scopeKey])) {
      throw new MedicalMonitoringR5AdapterError("SUBJECT_FLOW_IDENTITY_MISMATCH", `R5 subject_flow scope is not bound to the response identity: ${scopeKey}`, { field: `subject_flow.scope.${scopeKey}` });
    }
  }
  const normalizedScope = {
    projectRef: clean(scope.project_ref),
    runRef: clean(scope.run_ref),
    snapshotRef: clean(scope.snapshot_ref),
    cutoffRef: clean(scope.cutoff_ref),
    siteRef: clean(scope.site_ref),
  };
  const reconciliation = value.reconciliation;
  if (!reconciliation || typeof reconciliation !== "object" || Array.isArray(reconciliation)) {
    throw new MedicalMonitoringR5AdapterError("SUBJECT_FLOW_SCHEMA_INVALID", "R5 subject_flow reconciliation must be an object.");
  }
  const reconciliationState = requiredString(reconciliation.state, "subject_flow.reconciliation.state");
  if (!["matched", "blocked"].includes(reconciliationState)) {
    throw new MedicalMonitoringR5AdapterError("SUBJECT_FLOW_FIELD_INVALID", "R5 subject_flow reconciliation state is outside the accepted registry.", { field: "subject_flow.reconciliation.state", value: reconciliationState });
  }
  const blockedReasonZh = clean(reconciliation.gap_zh || reconciliation.reason_zh || value.blocked_reason_zh || value.reason_zh);
  if (reconciliationState === "blocked") {
    if (!blockedReasonZh) {
      throw new MedicalMonitoringR5AdapterError("SUBJECT_FLOW_GAP_MISSING", "R5 subject_flow blocked state must carry a Chinese gap explanation.", { field: "subject_flow.reconciliation.gap_zh" });
    }
    return {
      raw: value,
      availability,
      visualKind,
      scope: normalizedScope,
      reasonZh: "",
      blockedReasonZh,
      reconciliation: {
        state: "blocked",
        totalSubjectCount: null,
        entryCount: null,
        currentStayCount: null,
        detailCount: null,
        nodeConservationMatched: null,
        linkConservationMatched: null,
        gapZh: blockedReasonZh,
      },
      stages: [],
      links: [],
      subjects: [],
      coverage: {},
    };
  }
  const rawStages = array(value.stages, "subject_flow.stages");
  const rawLinks = array(value.links, "subject_flow.links");
  const rawSubjects = array(value.subjects, "subject_flow.subjects");
  const stages = rawStages.map(normalizeSubjectFlowStage);
  const stageRefs = new Set(stages.map((stage) => stage.stageRef));
  if (stageRefs.size !== stages.length) {
    throw new MedicalMonitoringR5AdapterError("SUBJECT_FLOW_REF_DUPLICATE", "R5 subject_flow declares a duplicated stage ref.", { field: "subject_flow.stages" });
  }
  const links = rawLinks.map((link) => normalizeSubjectFlowLink(link, stageRefs));
  const linkRefs = new Set(links.map((link) => link.linkRef));
  if (linkRefs.size !== links.length) {
    throw new MedicalMonitoringR5AdapterError("SUBJECT_FLOW_REF_DUPLICATE", "R5 subject_flow declares a duplicated link ref.", { field: "subject_flow.links" });
  }
  const linkPairs = new Set(links.map((link) => `${link.fromStageRef}->${link.toStageRef}`));
  if (linkPairs.size !== links.length) {
    throw new MedicalMonitoringR5AdapterError("SUBJECT_FLOW_REF_DUPLICATE", "R5 subject_flow declares a duplicated stage pair.", { field: "subject_flow.links" });
  }
  const subjects = rawSubjects.map((row) => normalizeSubjectFlowSubject(row, stageRefs, normalizedScope.siteRef));
  const subjectRefs = new Set(subjects.map((row) => row.subjectRef));
  if (subjectRefs.size !== subjects.length) {
    throw new MedicalMonitoringR5AdapterError("SUBJECT_FLOW_REF_DUPLICATE", "R5 subject_flow declares a duplicated subject ref.", { field: "subject_flow.subjects" });
  }
  const rawCoverage = value.coverage === undefined || value.coverage === null ? {} : value.coverage;
  if (!rawCoverage || typeof rawCoverage !== "object" || Array.isArray(rawCoverage)) {
    throw new MedicalMonitoringR5AdapterError("SUBJECT_FLOW_SCHEMA_INVALID", "R5 subject_flow coverage must be an object.");
  }
  const coverage = {};
  for (const [key, count] of Object.entries(rawCoverage)) coverage[key] = flowCount(count, `subject_flow.coverage.${key}`);
  const totalSubjectCount = flowCount(reconciliation.total_subject_count ?? reconciliation.subject_count, "subject_flow.reconciliation.total_subject_count");
  const entryCount = flowCount(reconciliation.entry_count, "subject_flow.reconciliation.entry_count");
  const currentStayCount = flowCount(reconciliation.current_stay_count, "subject_flow.reconciliation.current_stay_count");
  const detailCount = flowCount(reconciliation.detail_count, "subject_flow.reconciliation.detail_count");
  const nodeConservationMatched = flowBoolean(reconciliation.node_conservation_matched, "subject_flow.reconciliation.node_conservation_matched");
  const linkConservationMatched = flowBoolean(reconciliation.link_conservation_matched, "subject_flow.reconciliation.link_conservation_matched");
  if (subjects.length !== totalSubjectCount || totalSubjectCount !== detailCount
    || entryCount !== totalSubjectCount || currentStayCount !== totalSubjectCount
    || !nodeConservationMatched || !linkConservationMatched) {
    throw new MedicalMonitoringR5AdapterError("SUBJECT_FLOW_RECONCILIATION_MISMATCH", "R5 subject_flow reconciliation does not conserve the scoped subject set.", { field: "subject_flow.reconciliation" });
  }
  const rowsByCurrentStage = new Map();
  const riskRowsByCurrentStage = new Map();
  for (const row of subjects) {
    rowsByCurrentStage.set(row.currentStageRef, (rowsByCurrentStage.get(row.currentStageRef) || 0) + 1);
    if (row.currentMidHighRisk) riskRowsByCurrentStage.set(row.currentStageRef, (riskRowsByCurrentStage.get(row.currentStageRef) || 0) + 1);
  }
  for (const stage of stages) {
    if ((rowsByCurrentStage.get(stage.stageRef) || 0) !== stage.currentCount
      || (riskRowsByCurrentStage.get(stage.stageRef) || 0) !== stage.currentMidHighRiskCount) {
      throw new MedicalMonitoringR5AdapterError("SUBJECT_FLOW_RECONCILIATION_MISMATCH", `R5 subject_flow node counts do not match the scoped subject rows: ${stage.stageRef}`, { field: `subject_flow.stages.${stage.stageRef}` });
    }
  }
  return {
    raw: value,
    availability,
    visualKind,
    scope: normalizedScope,
    reasonZh: "",
    blockedReasonZh: "",
    reconciliation: {
      state: "matched",
      totalSubjectCount,
      entryCount,
      currentStayCount,
      detailCount,
      nodeConservationMatched,
      linkConservationMatched,
      gapZh: "",
    },
    stages,
    links,
    subjects,
    coverage,
  };
}

function mergeRiskRows(rows) {
  const byKey = new Map();
  for (const row of rows) {
    const key = row.riskInstanceRef || row.riskRef;
    const existing = byKey.get(key);
    if (!existing || (existing.riskStatus === "unresolved" && row.riskStatus === "confirmed")) byKey.set(key, row);
  }
  return [...byKey.values()];
}

function sourceRefMatchesEvidence(source, evidence, identity, projection) {
  if (!source || typeof source !== "object" || Array.isArray(source)) {
    throw new MedicalMonitoringR5AdapterError("SOURCE_EVIDENCE_SOURCE_INVALID", "R5 source-evidence source ref must be an object.");
  }
  for (const field of ["locator_ref", "snapshot_ref", "source_file_ref", "source_revision_ref", "record_ref", "canonical_location"]) {
    requiredString(source[field], `source_refs[0].${field}`);
  }
  array(source.lineage, "source_refs[0].lineage");
  for (const [index, value] of source.lineage.entries()) requiredString(value, `source_refs[0].lineage[${index}]`);
  requiredString(source.excerpt, "source_refs[0].excerpt");
  hash(source.source_revision_content_hash, "source_refs[0].source_revision_content_hash");
  if (source.locator_ref !== projection.source_locator_ref || source.locator_ref !== identity.source_locator_ref) {
    throw new MedicalMonitoringR5AdapterError("SOURCE_EVIDENCE_SOURCE_MISMATCH", "R5 source-evidence locator is not bound to the requested source.");
  }
  if (source.snapshot_ref !== identity.snapshot_ref || source.source_revision_ref !== evidence.source_revision_ref || source.source_revision_content_hash !== evidence.source_revision_content_hash || source.record_ref !== evidence.record_ref || source.canonical_location !== evidence.canonical_location || source.excerpt !== evidence.excerpt || JSON.stringify(source.lineage) !== JSON.stringify(evidence.lineage)) {
    throw new MedicalMonitoringR5AdapterError("SOURCE_EVIDENCE_SOURCE_MISMATCH", "R5 source-evidence fields are not bound to the exact source ref.");
  }
}

function normalizeSourceEvidenceProjection(projection, identity, sourceRefs, receipt) {
  if (!projection || typeof projection !== "object" || Array.isArray(projection) || projection.kind !== "source_evidence") {
    throw new MedicalMonitoringR5AdapterError("SOURCE_EVIDENCE_PROJECTION_INVALID", "R5 source-evidence projection kind is invalid.");
  }
  for (const field of ["risk_ref", "risk_instance_ref", "source_locator_ref", "authority_receipt_ref"]) {
    requiredString(projection[field], `projection.${field}`);
  }
  for (const [projectionKey, identityKey] of [["risk_ref", "risk_ref"], ["risk_instance_ref", "risk_instance_ref"], ["source_locator_ref", "source_locator_ref"]]) {
    if (projection[projectionKey] !== identity[identityKey]) {
      throw new MedicalMonitoringR5AdapterError("SOURCE_EVIDENCE_IDENTITY_MISMATCH", `R5 source-evidence identity mismatch: ${projectionKey}`, { field: projectionKey });
    }
  }
  if (receipt?.receipt_id && projection.authority_receipt_ref !== receipt.receipt_id) {
    throw new MedicalMonitoringR5AdapterError("SOURCE_EVIDENCE_RECEIPT_MISMATCH", "R5 source-evidence authority receipt is not bound.");
  }
  const evidence = required(projection.evidence, "projection.evidence");
  if (!evidence || typeof evidence !== "object" || Array.isArray(evidence)) {
    throw new MedicalMonitoringR5AdapterError("SOURCE_EVIDENCE_FIELDS_INVALID", "R5 source-evidence evidence must be an object.");
  }
  for (const field of ["excerpt", "record_ref", "canonical_location", "source_revision_ref"]) {
    requiredString(evidence[field], `projection.evidence.${field}`);
  }
  array(evidence.lineage, "projection.evidence.lineage");
  for (const [index, value] of evidence.lineage.entries()) requiredString(value, `projection.evidence.lineage[${index}]`);
  hash(evidence.source_revision_content_hash, "projection.evidence.source_revision_content_hash");
  if (!Array.isArray(sourceRefs) || sourceRefs.length !== 1) {
    throw new MedicalMonitoringR5AdapterError("SOURCE_EVIDENCE_SOURCE_INVALID", "R5 source-evidence must bind exactly one source ref.");
  }
  sourceRefMatchesEvidence(sourceRefs[0], evidence, identity, projection);
  return {
    ...evidence,
    riskRef: projection.risk_ref,
    riskInstanceRef: projection.risk_instance_ref,
    sourceLocatorRef: projection.source_locator_ref,
    authorityReceiptRef: projection.authority_receipt_ref,
  };
}

function currentRiskRefs(projection) {
  const set = projection.current_risk_set;
  if (set === undefined || set === null) return [];
  if (!set || typeof set !== "object" || Array.isArray(set)) {
    throw new MedicalMonitoringR5AdapterError("CURRENT_RISK_SET_INVALID", "R5 current_risk_set must be an object.");
  }
  const refs = [];
  for (const [key, values] of [["high_risk_refs", set.high_risk_refs], ["medium_risk_refs", set.medium_risk_refs], ["low_risk_cluster_refs", set.low_risk_cluster_refs]]) {
    if (values === undefined || values === null) continue;
    array(values, `projection.current_risk_set.${key}`);
    values.forEach((value, index) => refs.push(requiredString(value, `projection.current_risk_set.${key}[${index}]`)));
  }
  return refs;
}

function authorityHasCurrentRisks(counts, riskRefs) {
  const current = counts?.current_risk || counts?.currentRisk || counts?.current_risk_counts || {};
  const countPresent = current && typeof current === "object" && !Array.isArray(current)
    && Object.values(current).some((value) => Number.isInteger(value) && value > 0);
  return Boolean(riskRefs.length || countPresent);
}

function normalizeProjection(projection = {}, identity = {}, options = {}) {
  if (identity.view === "evidence") {
    const sourceEvidence = normalizeSourceEvidenceProjection(projection, identity, options.sourceRefs, options.receipt);
    return {
      raw: projection,
      identity,
      project: {},
      coverage: {},
      cutoff: identity.cutoff_ref || "",
      changeBands: [],
      currentRisks: [],
      centers: [],
      domains: [],
      subjects: [],
      temporalSpine: { spineRef: clean(identity.spine_ref), axisMode: clean(identity.axis_mode) || "calendar", windowStart: identity.window_start || null, windowEnd: identity.window_end || null, visits: [], pendingDates: [] },
      events: [],
      riskAnchors: [],
      domainTracks: [],
      indicators: null,
      aemhHistory: [],
      sourceEvidence,
      subjectFlow: null,
      workspaceState: {},
    };
  }
  const domainValues = projection.domain_encodings
    ?? projection.domain_encoding
    ?? projection.audience_encoding?.domain_items
    ?? projection.encoding_registry?.domain_items
    ?? (Array.isArray(projection.domain_tracks)
      ? projection.domain_tracks.map((track) => ({ ...(track.encoding || {}), domain: track.domain }))
      : null);
  if (!Array.isArray(domainValues) || domainValues.length === 0) {
    throw new MedicalMonitoringR5AdapterError("DOMAIN_ENCODING_MISSING", "R5 projection must provide the accepted eight-domain encoding registry.");
  }
  const domains = domainValues.map((value) => domainEncoding(value));
  const domainRegistry = new Map(domains.map((domain) => [domain.domain, domain]));
  const domainSet = new Set(domains.map((domain) => domain.domain));
  if (domains.length !== Object.keys(DOMAINS).length || domainSet.size !== domains.length || Object.keys(DOMAINS).some((domain) => !domainSet.has(domain))) {
    throw new MedicalMonitoringR5AdapterError("DOMAIN_ENCODING_SET_INVALID", "R5 projection domain encoding must contain each accepted domain exactly once.");
  }

  if (!hasOwn(projection, "current_risks") || !Array.isArray(projection.current_risks)) {
    throw new MedicalMonitoringR5AdapterError("CURRENT_RISKS_REQUIRED", "R5 overview and subject projections must provide current_risks as an array.");
  }
  const explicitCurrentValues = projection.current_risks;
  const rawRiskAnchors = projection.risk_anchors ?? projection.temporal_spine?.risk_anchors;
  if (rawRiskAnchors !== undefined && rawRiskAnchors !== null && !Array.isArray(rawRiskAnchors)) {
    throw new MedicalMonitoringR5AdapterError("RISK_ANCHORS_INVALID", "R5 risk_anchors must be an array.");
  }
  const normalizedRiskAnchors = (rawRiskAnchors || []).map((risk) => normalizeRisk(risk, domainRegistry));
  const riskRefs = currentRiskRefs(projection);
  if (!explicitCurrentValues.length && authorityHasCurrentRisks(options.counts, riskRefs)) {
    throw new MedicalMonitoringR5AdapterError("CURRENT_RISKS_REQUIRED", "R5 authority indicates current risks exist but projection.current_risks is empty.");
  }
  const normalizedCurrentRisks = explicitCurrentValues.map((risk) => normalizeRisk(risk, domainRegistry));
  const currentRisks = mergeRiskRows([...normalizedCurrentRisks, ...normalizedRiskAnchors]);

  let centerValues = [];
  if (hasOwn(projection, "center_map")) {
    if (Array.isArray(projection.center_map)) centerValues = projection.center_map;
    else if (projection.center_map && Array.isArray(projection.center_map.cells)) centerValues = projection.center_map.cells;
    else throw new MedicalMonitoringR5AdapterError("CENTER_MAP_INVALID", "R5 center_map must be an object containing cells.");
  } else if (Array.isArray(projection.centers)) centerValues = projection.centers;
  else if (Array.isArray(projection.centerMap?.cells)) centerValues = projection.centerMap.cells;
  else if (Array.isArray(projection.center_map_projection?.cells)) centerValues = projection.center_map_projection.cells;

  const eventValues = projection.events ?? projection.temporal_spine?.events ?? [];
  if (!Array.isArray(eventValues)) throw new MedicalMonitoringR5AdapterError("EVENTS_SCHEMA_INVALID", "R5 events must be an array.");
  const temporalSpine = projection.temporal_spine || projection.spine || {};
  const visits = projection.visits || temporalSpine.visits || [];
  const pendingDates = (projection.pending_dates ?? projection.date_pending_refs ?? temporalSpine.pending_dates ?? []).map((item) => (
    typeof item === "string" ? { item_ref: item, item_kind: "event", date_state: "missing" } : item
  ));
  const rawIndicators = projection.indicators ?? projection.trends ?? projection.indicator_trends ?? projection.metrics;
  const indicators = rawIndicators === undefined || rawIndicators === null
    ? null
    : array(rawIndicators, "projection.indicators").map((value, index) => normalizeIndicator(value, index));
  const measures = projection.measures === undefined || projection.measures === null ? [] : array(projection.measures, "projection.measures");
  const measureCatalog = new Map(measures.map((measure) => [measure.measure_ref, measure]));
  const normalizedCenters = centerValues.map((value) => normalizeCenter(value, measureCatalog, domainRegistry));
  const centerBySite = new Map();
  for (const center of normalizedCenters) {
    const existing = centerBySite.get(center.siteRef);
    if (!existing) {
      centerBySite.set(center.siteRef, { ...center, measures: [...center.measures] });
    } else {
      existing.measures.push(...center.measures);
      existing.risks.push(...center.risks);
    }
  }
  return {
    raw: projection,
    identity,
    project: projection.project || projection.project_identity || projection.project_summary || {},
    coverage: projection.coverage || projection.coverage_summary || {},
    cutoff: projection.cutoff || projection.cutoff_ref || identity.cutoff_ref || "",
    changeBands: projection.change_bands || projection.changes || [],
    currentRisks,
    centers: [...centerBySite.values()],
    domains,
    subjects: projection.subjects || projection.subject_options || [],
    subjectFlow: normalizeSubjectFlow(projection.subject_flow, identity),
    temporalSpine: {
      ...temporalSpine,
      spineRef: clean(temporalSpine.spine_ref || identity.spine_ref),
      axisMode: clean(temporalSpine.axis_mode || identity.axis_mode) || "calendar",
      windowStart: temporalSpine.window_start ?? identity.window_start ?? null,
      windowEnd: temporalSpine.window_end ?? identity.window_end ?? null,
      visits,
      pendingDates,
    },
    events: eventValues.map(normalizeEvent),
    riskAnchors: normalizedRiskAnchors,
    domainTracks: projection.domain_tracks || projection.tracks || [],
    indicators,
    aemhHistory: projection.aemh_history || projection.aemh_match_history || projection.ae_mh_history || [],
    sourceEvidence: projection.source_evidence || projection.evidence || null,
    workspaceState: projection.workspace_state || projection.subject_workspace_state || {},
  };
}

async function adaptEnvelope(payload, expected) {
  const validated = await validateEnvelope(payload, expected);
  const projection = normalizeProjection(validated.projection, validated.identity, { counts: validated.counts, sourceRefs: validated.source_refs, receipt: validated.authority_receipt });
  return Object.freeze({
    ...validated,
    counts: normalizeCounts(validated.counts),
    projection,
    publicIdentity: {
      projectRef: validated.identity.project_ref,
      runRef: validated.identity.run_ref,
      snapshotRef: validated.identity.snapshot_ref,
      cutoffState: validated.identity.cutoff_state,
      cutoffRef: validated.identity.cutoff_ref,
      siteRef: validated.identity.site_ref,
      subjectRef: validated.identity.subject_ref,
      riskRef: validated.identity.risk_ref,
      riskInstanceRef: validated.identity.risk_instance_ref,
      spineRef: validated.identity.spine_ref,
      view: validated.identity.view,
      axisMode: validated.identity.axis_mode,
      windowStart: validated.identity.window_start,
      windowEnd: validated.identity.window_end,
      visitRef: validated.identity.visit_ref,
      eventRef: validated.identity.event_ref,
      riskAnchorRef: validated.identity.risk_anchor_ref,
      sourceLocatorRef: validated.identity.source_locator_ref,
      returnContextKey: validated.identity.return_context_key,
    },
    labels: Object.freeze({ severity: SEVERITIES, dateState: DATE_STATES, coverageState: COVERAGE_STATES, changeKind: CHANGE_KINDS, flowStageChangeKind: FLOW_STAGE_CHANGE_KINDS }),
  });
}

export function createMedicalMonitoringR5Adapter({ baseUrl = "", fetchImpl = globalThis.fetch } = {}) {
  if (typeof fetchImpl !== "function") throw new TypeError("R5 adapter requires a fetch implementation.");

  const get = async (path, query, allowed, requiredKeys, expected, signal) => {
    const url = endpointUrl(baseUrl, path, queryEntries(query, allowed, requiredKeys));
    const response = await fetchImpl(url, {
      method: "GET",
      headers: { Accept: "application/json" },
      signal,
    });
    return adaptEnvelope(await readResponse(response), expected);
  };

  return Object.freeze({
    async getOverview(options = {}) {
      rejectOptionKeys(options, new Set(["projectId", "runRef", "snapshotRef", "cutoffRef", "siteRef", "signal"]));
      const { projectId, runRef = "", snapshotRef = "", cutoffRef = "", siteRef = "", signal } = options;
      const authorityRefs = [runRef, snapshotRef, cutoffRef].filter(Boolean);
      if (authorityRefs.length > 0 && authorityRefs.length < 3) {
        throw new MedicalMonitoringR5AdapterError("QUERY_GROUP_INCOMPLETE", "R5 overview identity refs must be supplied together.");
      }
      const allowed = new Set(["run_ref", "snapshot_ref", "cutoff_ref", "site_ref"]);
      return get(
        createPath(projectId, "overview"),
        { run_ref: runRef, snapshot_ref: snapshotRef, cutoff_ref: cutoffRef, site_ref: siteRef },
        allowed,
        [],
        { projectRef: clean(projectId), runRef, snapshotRef, cutoffRef, siteRef },
        signal,
      );
    },

    async getSubjectWorkspace(options = {}) {
      rejectOptionKeys(options, new Set(["projectId", "subjectId", "runRef", "snapshotRef", "cutoffRef", "siteRef", "spineRef", "windowStart", "windowEnd", "riskInstanceRef", "riskAnchorRef", "visitRef", "eventRef", "signal"]));
      const { projectId, subjectId, runRef, snapshotRef, cutoffRef, siteRef, spineRef, windowStart, windowEnd, riskInstanceRef = "", riskAnchorRef = "", visitRef = "", eventRef = "", signal } = options;
      const allowed = new Set([
        "run_ref",
        "snapshot_ref",
        "cutoff_ref",
        "site_ref",
        "spine_ref",
        "window_start",
        "window_end",
        "risk_instance_ref",
        "risk_anchor_ref",
        "visit_ref",
        "event_ref",
      ]);
      return get(
        createPath(projectId, `subject-workspaces/${encodeURIComponent(clean(subjectId))}`),
        {
          run_ref: runRef,
          snapshot_ref: snapshotRef,
          cutoff_ref: cutoffRef,
          site_ref: siteRef,
          spine_ref: spineRef,
          window_start: windowStart,
          window_end: windowEnd,
          risk_instance_ref: riskInstanceRef,
          risk_anchor_ref: riskAnchorRef,
          visit_ref: visitRef,
          event_ref: eventRef,
        },
        allowed,
        ["run_ref", "snapshot_ref", "cutoff_ref", "site_ref", "spine_ref", "window_start", "window_end"],
        { projectRef: clean(projectId), runRef, snapshotRef, cutoffRef, siteRef, subjectRef: clean(subjectId), spineRef },
        signal,
      );
    },

    async getSourceEvidence(options = {}) {
      rejectOptionKeys(options, new Set(["projectId", "runRef", "snapshotRef", "cutoffRef", "riskInstanceRef", "sourceLocatorRef", "signal"]));
      const { projectId, runRef, snapshotRef, cutoffRef, riskInstanceRef, sourceLocatorRef, signal } = options;
      const allowed = new Set(["run_ref", "snapshot_ref", "cutoff_ref", "risk_instance_ref", "source_locator_ref"]);
      return get(
        createPath(projectId, "source-evidence"),
        { run_ref: runRef, snapshot_ref: snapshotRef, cutoff_ref: cutoffRef, risk_instance_ref: riskInstanceRef, source_locator_ref: sourceLocatorRef },
        allowed,
        [...allowed],
        { projectRef: clean(projectId), runRef, snapshotRef, cutoffRef, riskInstanceRef, sourceLocatorRef },
        signal,
      );
    },
  });
}

export function projectR5SubjectView(payload, view) {
  const normalized = payload?.projection || payload;
  return { ...normalized, activeView: r5SubjectView(view) };
}

export const medicalMonitoringR5IdentityKeys = Object.freeze([...IDENTITY_KEYS]);
export const medicalMonitoringR5DomainRegistry = Object.freeze({ ...DOMAINS });
export const medicalMonitoringR5SeverityLabels = Object.freeze({ ...SEVERITIES });
export const medicalMonitoringR5CanonicalKeys = Object.freeze([...MEDICAL_MONITORING_R5_CANONICAL_KEYS]);
