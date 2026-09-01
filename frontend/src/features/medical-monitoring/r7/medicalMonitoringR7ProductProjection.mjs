import {
  projectR7Progress,
  R7_RUN_STATES,
} from "./medicalMonitoringR7ProgressProjection.mjs";

export const R7_PRODUCT_MODES = Object.freeze([
  "daily",
  "pre_lock",
  "post_lock_pre_cfdi",
]);

export const R7_PRODUCT_IN_FLIGHT_STATES = Object.freeze([
  "waiting_start",
  "running",
  "stopping",
  "interrupted_resumable",
]);

export const R7_PRODUCT_HISTORY_FIELDS = Object.freeze([
  "public_run_token",
  "mode_text",
  "data_cutoff_text",
  "comparison_range_text",
  "run_state",
  "result_available",
  "main_action",
  "status_text",
]);

export const R7_PUBLIC_RESULT_VIEWS = Object.freeze([
  "overview",
  "journey",
  "evidence",
]);

export const R7_PUBLIC_RESULT_LOCATOR_FIELDS = Object.freeze([
  "site_ref",
  "subject_ref",
  "spine_ref",
  "window_start",
  "window_end",
  "risk_instance_ref",
  "risk_anchor_ref",
  "visit_ref",
  "event_ref",
  "source_locator_ref",
]);

export const R7_PUBLIC_RESULT_IDENTITY_FIELDS = Object.freeze([
  "project_ref",
  "public_run_token",
  "snapshot_token",
  "data_cutoff_text",
  "view",
  "mode_text",
  "site_scope_text",
  "site_options",
  ...R7_PUBLIC_RESULT_LOCATOR_FIELDS,
]);

export const R7_PUBLIC_RESULT_ENVELOPE_FIELDS = Object.freeze([
  "identity",
  "projection",
  "result_context_token",
  "response_digest",
]);
export const R7_PUBLIC_RESULT_ENTRY_FIELDS = Object.freeze([
  "project_ref",
  "public_run_token",
  "snapshot_token",
  "data_cutoff_text",
  "site_options",
  "result_context_token",
]);

export const R7_PRODUCT_STATE_KINDS = Object.freeze([
  "loading",
  "ready",
  "active_run",
  "result_available",
  "unavailable",
]);

export const R7_PUBLIC_RESULT_UNAVAILABLE_TEXT = "本次结果暂不可查看，请返回进度页";
export const R7_OPTIONS_REFRESH_TEXT = "监查范围已更新，请重新确认";
export const R7_COMPARISON_UNAVAILABLE_TEXT = "当前数据尚不能与上次结果逐项比较";
export const R7_PUBLIC_RESULT_CENTER_OUT_OF_SCOPE_TEXT = "该中心不在本次监查范围";
export const R7_PUBLIC_RESULT_UNPUBLISHED_TEXT = "分析已结束，结果整理未完成";

const R7_RUN_STATE_SET = new Set(R7_RUN_STATES);
const R7_PRODUCT_MODE_SET = new Set(R7_PRODUCT_MODES);
const R7_IN_FLIGHT_SET = new Set(R7_PRODUCT_IN_FLIGHT_STATES);
const R7_RESULT_VIEW_SET = new Set(R7_PUBLIC_RESULT_VIEWS);
const R7_HISTORY_FIELD_SET = new Set(R7_PRODUCT_HISTORY_FIELDS);
const R7_RESULT_ENTRY_FIELD_SET = new Set(R7_PUBLIC_RESULT_ENTRY_FIELDS);
const R7_RESULT_IDENTITY_FIELD_SET = new Set(R7_PUBLIC_RESULT_IDENTITY_FIELDS);
const R7_RESULT_ENVELOPE_FIELD_SET = new Set(R7_PUBLIC_RESULT_ENVELOPE_FIELDS);
const R7_PUBLICATION_STATE_SET = new Set([
  "not_started",
  "publishing",
  "available",
  "blocked",
  "recoverable_failed",
]);

const PUBLIC_KEY_EXACT_FORBIDDEN = new Set([
  "run_id",
  "run_ref",
  "snapshot_ref",
  "cutoff_ref",
  "cutoff_state",
  "opaque_run_ref",
  "opaque_snapshot_ref",
  "authority",
  "authority_hash",
  "authority_digest",
  "authority_receipt",
  "authority_receipt_ref",
  "receipt_id",
  "receipt_ref",
  "receipt_set_digest",
  "digest",
  "packet_identity",
  "packet_digest",
  "r5_authority_packet_id",
  "r5_authority_packet_digest",
  "r5_digest",
  "source_snapshot_sha256",
  "source_revision_content_hash",
  "response_snapshot_sha256",
  "return_context_key",
]);

const PUBLIC_KEY_PREFIX_FORBIDDEN = ["authority_", "receipt_", "s4_", "r5_"];
const HEX_64 = /^[0-9a-f]{64}$/i;
const RESULT_CONTEXT_PREFIX = "result-context:";

function isRecord(value) {
  return value !== null && typeof value === "object" && !Array.isArray(value);
}

function clean(value) {
  return typeof value === "string" ? value.trim() : "";
}

function nonNegativeInteger(value) {
  return Number.isInteger(value) && value >= 0 ? value : 0;
}

function clone(value) {
  if (Array.isArray(value)) return value.map(clone);
  if (isRecord(value)) {
    return Object.fromEntries(Object.entries(value).map(([key, item]) => [key, clone(item)]));
  }
  return value;
}

function freeze(value) {
  if (Array.isArray(value)) {
    value.forEach((item) => freeze(item));
  } else if (isRecord(value)) {
    Object.values(value).forEach((item) => freeze(item));
  }
  return Object.freeze(value);
}

function projectionError(code, text, field = "") {
  const error = new Error(text);
  error.name = "MedicalMonitoringR7ProductProjectionError";
  error.code = code;
  error.field = field;
  return error;
}

export class MedicalMonitoringR7PublicEnvelopeError extends Error {
  constructor(code, message, field = "") {
    super(message);
    this.name = "MedicalMonitoringR7PublicEnvelopeError";
    this.code = code;
    this.field = field;
  }
}

function invalidResult(error, fallback = "数据暂时无法展示") {
  const code = error?.code || "invalid_projection";
  const text = error?.message || fallback;
  return freeze({
    kind: "invalid",
    ok: false,
    code,
    text,
    error: text,
    value: null,
  });
}

function normalizedResult(value) {
  return freeze({ ok: true, error: "", value: freeze(value) });
}

function requiredText(value, field, code = "invalid_projection") {
  const text = clean(value);
  if (!text) throw projectionError(code, `${field} 缺失，暂不展示本次监查。`, field);
  return text;
}

function optionalText(value) {
  return clean(value);
}

function assertExpectedProject(actual, expected, message) {
  const expectedProject = clean(expected);
  if (expectedProject && actual !== expectedProject) {
    throw projectionError("project_identity_mismatch", message, "project_id");
  }
}

function keyIsForbidden(key) {
  const lowered = String(key).toLowerCase();
  if (PUBLIC_KEY_EXACT_FORBIDDEN.has(lowered)) return true;
  if (PUBLIC_KEY_PREFIX_FORBIDDEN.some((prefix) => lowered.startsWith(prefix))) return true;
  if (lowered.endsWith("_snapshot_ref") || lowered.endsWith("_cutoff_ref")) return true;
  return false;
}

function findForbiddenKey(value, path = "") {
  if (Array.isArray(value)) {
    for (let index = 0; index < value.length; index += 1) {
      const found = findForbiddenKey(value[index], `${path}[${index}]`);
      if (found) return found;
    }
    return null;
  }
  if (!isRecord(value)) return null;
  for (const [key, item] of Object.entries(value)) {
    const currentPath = path ? `${path}.${key}` : key;
    if (keyIsForbidden(key)) return currentPath;
    const found = findForbiddenKey(item, currentPath);
    if (found) return found;
  }
  return null;
}

function normalizeDataBatch(value, index) {
  if (!isRecord(value)) {
    throw projectionError("invalid_setup_options", `数据版本 ${index + 1} 格式异常，暂不展示监查范围。`);
  }
  const snapshotToken = requiredText(value.snapshot_token, `data_batches[${index}].snapshot_token`, "invalid_setup_options");
  return freeze({
    snapshotToken,
    dataCutoff: optionalText(value.data_cutoff),
    importedAt: optionalText(value.imported_at),
    scopeDescription: optionalText(value.scope_description),
    rowCount: nonNegativeInteger(value.row_count),
    canCompare: value.can_compare === true,
  });
}

function normalizeBaseline(value, index) {
  if (!isRecord(value)) {
    throw projectionError("invalid_setup_options", `比较基线 ${index + 1} 格式异常，暂不展示监查范围。`);
  }
  return freeze({
    baselineToken: requiredText(value.baseline_token, `baseline_options[${index}].baseline_token`, "invalid_setup_options"),
    mode: optionalText(value.mode),
    modeText: optionalText(value.mode_text),
    dataCutoff: optionalText(value.data_cutoff),
    publishedAt: optionalText(value.published_at),
    scopeDescription: optionalText(value.scope_description),
    recommended: value.recommended === true,
    selectable: value.selectable === true,
  });
}

function normalizeMode(value, index) {
  if (!isRecord(value)) {
    throw projectionError("invalid_setup_options", `监查方式 ${index + 1} 格式异常，暂不展示监查方式。`);
  }
  const mode = requiredText(value.mode, `modes[${index}].mode`, "invalid_setup_options");
  if (!R7_PRODUCT_MODE_SET.has(mode)) {
    // The product page is closed to the three server-registered modes. An
    // unknown future/forged option is not silently presented as a fourth card.
    throw projectionError("unsupported_mode", `监查方式 ${mode} 不在当前可用范围内。`, `modes[${index}].mode`);
  }
  const basisOptions = Array.isArray(value.execution_basis_options)
    ? value.execution_basis_options.map((item, basisIndex) => {
      if (!isRecord(item)) {
        throw projectionError("invalid_setup_options", `执行基础 ${basisIndex + 1} 格式异常。`);
      }
      return freeze({
        value: requiredText(item.value, `modes[${index}].execution_basis_options[${basisIndex}].value`, "invalid_setup_options"),
        label: optionalText(item.label),
        available: item.available === true,
        disabledReason: optionalText(item.disabled_reason),
      });
    })
    : [];
  const baselineOptions = Array.isArray(value.baseline_options)
    ? value.baseline_options.map(normalizeBaseline)
    : [];
  return freeze({
    mode,
    // Labels, descriptions, availability, and recommendation reasons are
    // copied from the service. This module does not invent mode wording.
    label: optionalText(value.label),
    description: optionalText(value.description),
    executionBasisOptions: freeze(basisOptions),
    defaultExecutionBasis: optionalText(value.default_execution_basis),
    requiresPublishedSameModeBaseline: value.requires_published_same_mode_baseline === true,
    baselineOptions: freeze(baselineOptions),
    available: value.available === true,
    disabledReason: optionalText(value.disabled_reason),
    recommended: value.recommended === true,
    recommendationReason: optionalText(value.recommendation_reason),
  });
}

function normalizeRuleRevision(value, index, expectedProject) {
  if (!isRecord(value)) {
    throw projectionError("invalid_setup_options", `特殊关注规则 ${index + 1} 格式异常。`);
  }
  const projectId = optionalText(value.project_id);
  assertExpectedProject(projectId, expectedProject, "特殊关注规则项目身份不一致，已阻止写入当前向导。");
  return freeze({
    projectId,
    revision: Number.isInteger(value.revision) && value.revision > 0 ? value.revision : 0,
    revisionToken: requiredText(value.revision_token, `rule_revisions[${index}].revision_token`, "invalid_setup_options"),
    summary: optionalText(value.summary),
    applicableScope: optionalText(value.applicable_scope),
    startingRun: optionalText(value.starting_run),
    selectable: value.selectable !== false,
    recommended: value.recommended === true,
    createdAt: optionalText(value.created_at),
  });
}

function normalizeSetupOptionsOrThrow(payload, { projectId } = {}) {
  if (!isRecord(payload)) {
    throw projectionError("invalid_setup_options", "监查范围响应格式异常，暂不展示监查方式。", "response");
  }
  const forbidden = findForbiddenKey(payload);
  if (forbidden) {
    throw projectionError("public_identity_forbidden", `监查范围响应包含不可公开身份：${forbidden}。`, forbidden);
  }
  const responseProject = requiredText(payload.project_id, "project_id", "invalid_setup_options");
  assertExpectedProject(responseProject, projectId, "监查范围项目身份不一致，已阻止写入当前向导。");
  if (!Array.isArray(payload.modes)) {
    throw projectionError("invalid_setup_options", "监查方式响应格式异常，暂不展示监查方式。", "modes");
  }
  const modes = payload.modes.map(normalizeMode);
  if (modes.length !== R7_PRODUCT_MODES.length || modes.some((item) => !R7_PRODUCT_MODE_SET.has(item.mode))) {
    throw projectionError("invalid_setup_options", "当前监查方式响应不完整，暂不展示向导。", "modes");
  }
  const seenModes = new Set(modes.map((item) => item.mode));
  if (seenModes.size !== modes.length || R7_PRODUCT_MODES.some((mode) => !seenModes.has(mode))) {
    throw projectionError("invalid_setup_options", "当前监查方式响应不完整，暂不展示向导。", "modes");
  }
  const batches = Array.isArray(payload.data_batches)
    ? payload.data_batches.map(normalizeDataBatch)
    : [];
  const currentData = payload.current_data === null || payload.current_data === undefined
    ? null
    : normalizeDataBatch(payload.current_data, 0);
  const rules = Array.isArray(payload.rule_revisions)
    ? payload.rule_revisions.map((item, index) => normalizeRuleRevision(item, index, responseProject))
    : [];
  const recommendedMode = optionalText(payload.recommended_mode);
  if (recommendedMode && !R7_PRODUCT_MODE_SET.has(recommendedMode)) {
    throw projectionError("invalid_setup_options", "服务端推荐的监查方式不可用。", "recommended_mode");
  }
  return {
    kind: "setup",
    schemaVersion: optionalText(payload.schema_version),
    projectId: responseProject,
    dataBatches: freeze(batches),
    currentData,
    modes: freeze(modes),
    ruleRevisions: freeze(rules),
    recommendedMode,
    recommendationReason: optionalText(payload.recommendation_reason),
  };
}

export function normalizeR7SetupOptions(payload, expected = {}) {
  try {
    return normalizedResult(normalizeSetupOptionsOrThrow(payload, expected));
  } catch (error) {
    return invalidResult(error, "监查范围响应格式异常，暂不展示监查方式。");
  }
}

export function projectR7SetupOptions(payload, expected = {}) {
  const normalized = normalizeR7SetupOptions(payload, expected);
  if (!normalized.ok) return invalidResult({ code: normalized.code, message: normalized.error });
  return normalized.value;
}

export const projectR7RunSetupOptions = projectR7SetupOptions;

function normalizeHistoryRow(value, index) {
  if (!isRecord(value)) {
    throw projectionError("invalid_history", `第 ${index + 1} 条历史记录格式异常，暂不展示历史。`);
  }
  const keys = Object.keys(value);
  if (keys.length !== R7_PRODUCT_HISTORY_FIELDS.length || keys.some((key) => !R7_HISTORY_FIELD_SET.has(key))) {
    throw projectionError("invalid_history", "历史记录字段不完整，暂不展示历史。", `runs[${index}]`);
  }
  const publicRunToken = requiredText(value.public_run_token, `runs[${index}].public_run_token`, "invalid_history");
  const runState = requiredText(value.run_state, `runs[${index}].run_state`, "invalid_history");
  if (!R7_RUN_STATE_SET.has(runState)) {
    throw projectionError("invalid_history", "历史记录状态无法核对，暂不展示历史。", `runs[${index}].run_state`);
  }
  if (typeof value.result_available !== "boolean") {
    throw projectionError("invalid_history", "历史记录结果状态格式异常，暂不展示历史。", `runs[${index}].result_available`);
  }
  return freeze({
    publicRunToken,
    modeText: requiredText(value.mode_text, `runs[${index}].mode_text`, "invalid_history"),
    dataCutoffText: requiredText(value.data_cutoff_text, `runs[${index}].data_cutoff_text`, "invalid_history"),
    comparisonRangeText: requiredText(value.comparison_range_text, `runs[${index}].comparison_range_text`, "invalid_history"),
    runState,
    resultAvailable: value.result_available,
    mainAction: requiredText(value.main_action, `runs[${index}].main_action`, "invalid_history"),
    statusText: requiredText(value.status_text, `runs[${index}].status_text`, "invalid_history"),
  });
}

function normalizeHistoryOrThrow(payload, { projectId } = {}) {
  if (!isRecord(payload) || !Array.isArray(payload.runs)) {
    throw projectionError("invalid_history", "监查历史响应格式异常，暂不展示历史。", "runs");
  }
  const forbidden = findForbiddenKey(payload);
  if (forbidden) {
    throw projectionError("public_identity_forbidden", `监查历史响应包含不可公开身份：${forbidden}。`, forbidden);
  }
  if (clean(payload.project_id)) {
    assertExpectedProject(clean(payload.project_id), projectId, "监查历史项目身份不一致，已阻止写入当前历史。");
  }
  const rows = payload.runs.map(normalizeHistoryRow);
  return {
    kind: "history",
    projectId: clean(projectId) || clean(payload.project_id),
    rows: freeze(rows),
    // `runs` is a view-model alias, not a second data source.
    runs: freeze(rows),
  };
}

export function normalizeR7History(payload, expected = {}) {
  try {
    return normalizedResult(normalizeHistoryOrThrow(payload, expected));
  } catch (error) {
    return invalidResult(error, "监查历史响应格式异常，暂不展示历史。");
  }
}

export function projectR7History(payload, expected = {}) {
  const normalized = normalizeR7History(payload, expected);
  if (!normalized.ok) return invalidResult({ code: normalized.code, message: normalized.error });
  return normalized.value;
}

export const projectR7RunHistory = projectR7History;
function normalizeResultEntryOrThrow(payload, {
  projectId,
  publicRunToken,
  resultContextToken,
} = {}) {
  if (!isRecord(payload)) {
    throw projectionError("invalid_result_entry", "本次结果暂不可查看，请返回进度页", "response");
  }
  const keys = Object.keys(payload);
  if (keys.length !== R7_PUBLIC_RESULT_ENTRY_FIELDS.length || keys.some((key) => !R7_RESULT_ENTRY_FIELD_SET.has(key))) {
    throw projectionError("invalid_result_entry", "本次结果暂不可查看，请返回进度页", "response");
  }
  const forbidden = findForbiddenKey(payload);
  if (forbidden) {
    throw projectionError("public_identity_forbidden", "本次结果暂不可查看，请返回进度页", forbidden);
  }
  const projectRef = requiredText(payload.project_ref, "project_ref", "invalid_result_entry");
  assertExpectedProject(projectRef, projectId, "本次结果项目身份不一致，已阻止展示结果。");
  const runToken = requiredText(payload.public_run_token, "public_run_token", "invalid_result_entry");
  const contextToken = requiredText(payload.result_context_token, "result_context_token", "invalid_result_entry");
  if (!contextToken.startsWith(RESULT_CONTEXT_PREFIX)) {
    throw projectionError("invalid_result_entry", "本次结果暂不可查看，请返回进度页", "result_context_token");
  }
  if (clean(publicRunToken) && runToken !== clean(publicRunToken)) {
    throw projectionError("public_identity_mismatch", "本次结果暂不可查看，请返回进度页", "public_run_token");
  }
  if (clean(resultContextToken) && contextToken !== clean(resultContextToken)) {
    throw projectionError("public_identity_mismatch", "本次结果暂不可查看，请返回进度页", "result_context_token");
  }
  if (!Array.isArray(payload.site_options) || payload.site_options.some((item) => (
    !isRecord(item)
    || Object.keys(item).some((key) => !["site_ref", "site_label"].includes(key))
    || !clean(item.site_ref)
    || !clean(item.site_label)
  ))) {
    throw projectionError("invalid_result_entry", "本次结果暂不可查看，请返回进度页", "site_options");
  }
  return {
    kind: "result_entry",
    projectRef,
    publicRunToken: runToken,
    snapshotToken: requiredText(payload.snapshot_token, "snapshot_token", "invalid_result_entry"),
    dataCutoffText: requiredText(payload.data_cutoff_text, "data_cutoff_text", "invalid_result_entry"),
    siteOptions: clone(payload.site_options),
    resultContextToken: contextToken,
  };
}

export function normalizeR7ResultEntry(payload, expected = {}) {
  try {
    return normalizedResult(normalizeResultEntryOrThrow(payload, expected));
  } catch (error) {
    return invalidResult(error, R7_PUBLIC_RESULT_UNAVAILABLE_TEXT);
  }
}

export function projectR7ResultEntry(payload, expected = {}) {
  const normalized = normalizeR7ResultEntry(payload, expected);
  if (!normalized.ok) return invalidResult({ code: normalized.code, message: normalized.error });
  return normalized.value;
}

export const projectR7PublicResultEntry = projectR7ResultEntry;

function publicProgressPollDecision(runState, publicationState) {
  const analysisActive = R7_PRODUCT_IN_FLIGHT_STATES.includes(runState);
  const publicationActive = runState === "completed"
    && ["not_started", "publishing"].includes(publicationState);
  return freeze({
    active: analysisActive || publicationActive,
    intervalMs: analysisActive || publicationActive ? 2000 : 0,
    reason: analysisActive ? "analysis" : publicationActive ? "publication" : "terminal",
  });
}

function normalizePublicProgressOrThrow(payload, { publicRunToken } = {}) {
  const token = requiredText(publicRunToken, "publicRunToken", "invalid_public_progress");
  if (!isRecord(payload) || Array.isArray(payload)) {
    throw projectionError("invalid_public_progress", "本次监查进度格式异常，暂不展示进度。", "response");
  }
  const forbidden = findForbiddenKey(payload);
  if (forbidden) {
    throw projectionError("public_identity_forbidden", `本次监查进度包含不可公开身份：${forbidden}。`, forbidden);
  }
  const base = projectR7Progress(payload);
  if (base.kind !== "progress") {
    throw projectionError("invalid_public_progress", "本次监查进度格式异常，暂不展示进度。", "run_state");
  }
  const publicationState = optionalText(payload.publication_state)
    || (base.runState === "completed" ? "not_started" : "not_started");
  if (!R7_PUBLICATION_STATE_SET.has(publicationState)) {
    throw projectionError("invalid_public_progress", "本次监查结果整理状态格式异常，暂不展示进度。", "publication_state");
  }
  const resultAvailable = typeof payload.result_available === "boolean"
    ? payload.result_available
    : publicationState === "available";
  if (resultAvailable !== (publicationState === "available")) {
    throw projectionError("invalid_public_progress", "本次监查结果状态无法核对，暂不展示进度。", "result_available");
  }
  const publicationStatusText = optionalText(payload.publication_status_text)
    || (base.runState === "completed" && !resultAvailable ? R7_PUBLIC_RESULT_UNPUBLISHED_TEXT : "");
  return {
    ...base,
    kind: "public_progress",
    publicRunToken: token,
    publicationState,
    resultAvailable,
    publicationStatusText,
    poll: publicProgressPollDecision(base.runState, publicationState),
  };
}

export function normalizeR7PublicProgress(payload, expected = {}) {
  try {
    return normalizedResult(normalizePublicProgressOrThrow(payload, expected));
  } catch (error) {
    return invalidResult(error, "本次监查进度格式异常，暂不展示进度。");
  }
}

export function projectR7PublicProgress(payload, expected = {}) {
  const normalized = normalizeR7PublicProgress(payload, expected);
  if (!normalized.ok) return invalidResult({ code: normalized.code, message: normalized.error });
  return normalized.value;
}

export const projectR7PublicRunProgress = projectR7PublicProgress;
function publicErrorCode(error) {
  const detail = error && typeof error === "object" ? error.detail : null;
  if (detail && typeof detail === "object" && typeof detail.code === "string") return detail.code;
  return typeof error?.code === "string" ? error.code : "";
}

export function projectR7PublicProgressError(error) {
  const code = publicErrorCode(error);
  if (code === "public_run_not_found" || code === "run_binding_not_found") {
    return freeze({
      kind: "unavailable",
      code,
      text: "本次监查暂不可读取，请返回项目概览",
    });
  }
  if (code === "global_default_missing" || code === "invalid_snapshot") {
    return freeze({ kind: "refresh_options", code, text: R7_OPTIONS_REFRESH_TEXT });
  }
  const status = Number(error?.status) || 0;
  return freeze({
    kind: status === 403 ? "forbidden" : "error",
    code,
    text: status === 403 ? "当前账号不能查看本次监查" : "进度刷新失败",
  });
}

export function projectR7PublicResultError(error) {
  const code = publicErrorCode(error);
  if (code === "result_center_out_of_scope") {
    return freeze({
      kind: "unavailable",
      code,
      text: R7_PUBLIC_RESULT_CENTER_OUT_OF_SCOPE_TEXT,
    });
  }
  return freeze({
    kind: "unavailable",
    code,
    text: R7_PUBLIC_RESULT_UNAVAILABLE_TEXT,
  });
}

function normalizePublicResultEnvelopeOrThrow(payload, {
  projectId,
  resultContextToken,
  publicRunToken,
  view,
} = {}) {
  if (!isRecord(payload) || Array.isArray(payload)) {
    throw new MedicalMonitoringR7PublicEnvelopeError(
      "invalid_envelope",
      "本次结果暂不可查看，请返回进度页",
      "response",
    );
  }
  const topLevelKeys = Object.keys(payload);
  if (
    topLevelKeys.length !== R7_PUBLIC_RESULT_ENVELOPE_FIELDS.length
    || topLevelKeys.some((key) => !R7_RESULT_ENVELOPE_FIELD_SET.has(key))
  ) {
    throw new MedicalMonitoringR7PublicEnvelopeError(
      "public_envelope_fields_invalid",
      "本次结果暂不可查看，请返回进度页",
      "response",
    );
  }
  const forbidden = findForbiddenKey(payload);
  if (forbidden) {
    throw new MedicalMonitoringR7PublicEnvelopeError(
      "public_identity_forbidden",
      "本次结果暂不可查看，请返回进度页",
      forbidden,
    );
  }
  const identity = payload.identity;
  if (!isRecord(identity) || !isRecord(payload.projection)) {
    throw new MedicalMonitoringR7PublicEnvelopeError(
      "public_envelope_shape_invalid",
      "本次结果暂不可查看，请返回进度页",
      "identity",
    );
  }
  const identityKeys = Object.keys(identity);
  if (identityKeys.some((key) => !R7_RESULT_IDENTITY_FIELD_SET.has(key))) {
    throw new MedicalMonitoringR7PublicEnvelopeError(
      "public_identity_fields_invalid",
      "本次结果暂不可查看，请返回进度页",
      "identity",
    );
  }
  const projectRef = requiredText(identity.project_ref, "identity.project_ref", "public_identity_invalid");
  assertExpectedProject(projectRef, projectId, "本次结果项目身份不一致，已阻止展示结果。");
  const publicToken = requiredText(identity.public_run_token, "identity.public_run_token", "public_identity_invalid");
  const snapshotToken = requiredText(identity.snapshot_token, "identity.snapshot_token", "public_identity_invalid");
  const cutoffText = requiredText(identity.data_cutoff_text, "identity.data_cutoff_text", "public_identity_invalid");
  const identityView = requiredText(identity.view, "identity.view", "public_identity_invalid");
  if (!R7_RESULT_VIEW_SET.has(identityView)) {
    throw new MedicalMonitoringR7PublicEnvelopeError(
      "public_identity_invalid",
      "本次结果暂不可查看，请返回进度页",
      "identity.view",
    );
  }
  const expectedView = clean(view);
  if (expectedView && identityView !== expectedView) {
    throw new MedicalMonitoringR7PublicEnvelopeError(
      "public_identity_mismatch",
      "本次结果暂不可查看，请返回进度页",
      "identity.view",
    );
  }
  const token = requiredText(payload.result_context_token, "result_context_token", "public_identity_invalid");
  if (!token.startsWith(RESULT_CONTEXT_PREFIX)) {
    throw new MedicalMonitoringR7PublicEnvelopeError(
      "public_identity_invalid",
      "本次结果暂不可查看，请返回进度页",
      "result_context_token",
    );
  }
  if (clean(resultContextToken) && token !== clean(resultContextToken)) {
    throw new MedicalMonitoringR7PublicEnvelopeError(
      "public_identity_mismatch",
      "本次结果暂不可查看，请返回进度页",
      "result_context_token",
    );
  }
  if (clean(publicRunToken) && publicToken !== clean(publicRunToken)) {
    throw new MedicalMonitoringR7PublicEnvelopeError(
      "public_identity_mismatch",
      "本次结果暂不可查看，请返回进度页",
      "identity.public_run_token",
    );
  }
  const siteScopeText = optionalText(identity.site_scope_text);
  const siteOptions = identity.site_options;
  if (siteOptions !== undefined && (
    !Array.isArray(siteOptions)
    || siteOptions.some((item) => (
      !isRecord(item)
      || Object.keys(item).some((key) => !["site_ref", "site_label"].includes(key))
      || !clean(item.site_ref)
      || !clean(item.site_label)
    ))
  )) {
    throw new MedicalMonitoringR7PublicEnvelopeError(
      "public_identity_invalid",
      "本次结果暂不可查看，请返回进度页",
      "identity.site_options",
    );
  }
  if (!siteScopeText && !Array.isArray(siteOptions)) {
    throw new MedicalMonitoringR7PublicEnvelopeError(
      "public_identity_invalid",
      "本次结果暂不可查看，请返回进度页",
      "identity.site_scope_text",
    );
  }
  for (const field of ["mode_text"]) {
    requiredText(identity[field], `identity.${field}`, "public_identity_invalid");
  }
  if (typeof payload.response_digest !== "string" || !HEX_64.test(payload.response_digest)) {
    throw new MedicalMonitoringR7PublicEnvelopeError(
      "public_response_digest_invalid",
      "本次结果暂不可查看，请返回进度页",
      "response_digest",
    );
  }
  for (const key of R7_PUBLIC_RESULT_LOCATOR_FIELDS) {
    if (identity[key] !== undefined && (typeof identity[key] !== "string" || !identity[key].trim())) {
      throw new MedicalMonitoringR7PublicEnvelopeError(
        "public_locator_invalid",
        "本次结果暂不可查看，请返回进度页",
        `identity.${key}`,
      );
    }
  }
  const normalizedIdentity = {
    project_ref: projectRef,
    public_run_token: publicToken,
    snapshot_token: snapshotToken,
    data_cutoff_text: cutoffText,
    view: identityView,
    mode_text: clean(identity.mode_text),
    site_scope_text: siteScopeText,
  };
  for (const key of R7_PUBLIC_RESULT_LOCATOR_FIELDS) {
    if (identity[key] !== undefined) normalizedIdentity[key] = identity[key];
  }
  if (Array.isArray(siteOptions)) normalizedIdentity.site_options = clone(siteOptions);
  return {
    identity: normalizedIdentity,
    projection: clone(payload.projection),
    result_context_token: token,
    response_digest: payload.response_digest.toLowerCase(),
  };
}

export function normalizeR7PublicResultEnvelope(payload, expected = {}) {
  return freeze(normalizePublicResultEnvelopeOrThrow(payload, expected));
}

export function validateR7PublicResultEnvelope(payload, expected = {}) {
  return normalizeR7PublicResultEnvelope(payload, expected);
}

export function safeValidateR7PublicResultEnvelope(payload, expected = {}) {
  try {
    return normalizedResult(normalizePublicResultEnvelopeOrThrow(payload, expected));
  } catch (error) {
    return invalidResult(error, R7_PUBLIC_RESULT_UNAVAILABLE_TEXT);
  }
}

export const validateMedicalMonitoringR7PublicResultEnvelope = validateR7PublicResultEnvelope;
export const validateMedicalMonitoringR7PublicEnvelope = validateR7PublicResultEnvelope;
export const normalizeMedicalMonitoringR7PublicEnvelope = normalizeR7PublicResultEnvelope;

function canonicalize(value) {
  if (Array.isArray(value)) return value.map(canonicalize);
  if (isRecord(value)) {
    return Object.fromEntries(
      Object.keys(value).sort().map((key) => [key, canonicalize(value[key])]),
    );
  }
  return value;
}

export function canonicalR7PublicResultPayload(envelope) {
  const normalized = normalizeR7PublicResultEnvelope(envelope);
  return JSON.stringify(canonicalize({
    identity: normalized.identity,
    projection: normalized.projection,
  }));
}

export async function computeR7PublicResponseDigest(envelope) {
  if (!globalThis.crypto?.subtle || typeof TextEncoder !== "function") {
    throw new MedicalMonitoringR7PublicEnvelopeError(
      "public_digest_unavailable",
      "本次结果暂不可查看，请返回进度页",
      "response_digest",
    );
  }
  const bytes = new TextEncoder().encode(canonicalR7PublicResultPayload(envelope));
  const digest = await globalThis.crypto.subtle.digest("SHA-256", bytes);
  return [...new Uint8Array(digest)].map((value) => value.toString(16).padStart(2, "0")).join("");
}
export const computeMedicalMonitoringR7PublicResponseDigest = computeR7PublicResponseDigest;

export async function verifyR7PublicResultEnvelope(payload, expected = {}) {
  const normalized = normalizeR7PublicResultEnvelope(payload, expected);
  const actual = await computeR7PublicResponseDigest(normalized);
  if (actual !== normalized.response_digest) {
    throw new MedicalMonitoringR7PublicEnvelopeError(
      "public_response_digest_mismatch",
      R7_PUBLIC_RESULT_UNAVAILABLE_TEXT,
      "response_digest",
    );
  }
  return normalized;
}
export const validateR7PublicResultEnvelopeWithDigest = verifyR7PublicResultEnvelope;

export function projectR7ResultContext(payload, expected = {}) {
  try {
    const envelope = normalizeR7PublicResultEnvelope(payload, expected);
    return freeze({
      kind: "result",
      resultContextToken: envelope.result_context_token,
      identity: envelope.identity,
      projection: envelope.projection,
      view: envelope.identity.view,
      projectRef: envelope.identity.project_ref,
      publicRunToken: envelope.identity.public_run_token,
      modeText: envelope.identity.mode_text,
      dataCutoffText: envelope.identity.data_cutoff_text,
      siteScopeText: envelope.identity.site_scope_text,
    });
  } catch (error) {
    return invalidResult(error, R7_PUBLIC_RESULT_UNAVAILABLE_TEXT);
  }
}

export const projectR7PublicResultContext = projectR7ResultContext;
export const projectMedicalMonitoringR7PublicResult = projectR7ResultContext;
export const projectR7PublicResultEnvelope = projectR7ResultContext;

export function isR7ProductMode(value) {
  return R7_PRODUCT_MODE_SET.has(clean(value));
}

export function isR7InFlightRunState(value) {
  return R7_IN_FLIGHT_SET.has(clean(value));
}

export function isR7PublicResultView(value) {
  return R7_RESULT_VIEW_SET.has(clean(value));
}

export function publicResultContextTokenPrefix() {
  return RESULT_CONTEXT_PREFIX;
}
