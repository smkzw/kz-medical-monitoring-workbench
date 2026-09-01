// Continuity public projection: strict frontend validator.
// Any field-set, closed-set, count, order, or identity violation fails the
// whole response closed; callers must then show only
// MONITORING_CONTINUITY_UNAVAILABLE_TEXT and keep the existing result boards intact.

export const MONITORING_CONTINUITY_UNAVAILABLE_TEXT = "本轮变化暂不可查看";
export const MONITORING_CONTINUITY_ROW_LIMIT = 200;

export const MONITORING_CONTINUITY_TOP_LEVEL_FIELDS = Object.freeze([
  "result_context_token",
  "identity",
  "comparison",
  "response_digest",
]);

export const MONITORING_CONTINUITY_IDENTITY_FIELDS = Object.freeze([
  "project_ref",
  "public_run_token",
  "snapshot_token",
  "data_cutoff_text",
  "mode_text",
  "site_scope_text",
]);

export const MONITORING_CONTINUITY_IDENTITY_OPTIONAL_FIELDS = Object.freeze([
  "site_ref",
]);

export const MONITORING_CONTINUITY_COMPARISON_FIELDS = Object.freeze([
  "available",
  "basis_text",
  "comparison_text",
  "source_run_text",
  "change_counts",
  "rows",
  "shown_count",
  "total_count",
  "truncated",
]);

export const MONITORING_CONTINUITY_ROW_FIELDS = Object.freeze([
  "row_ref",
  "object_type",
  "object_type_text",
  "ordinal",
  "change_kind",
  "change_text",
  "disposition",
  "disposition_text",
  "data_change_kind",
  "data_change_text",
  "severity_before_text",
  "severity_after_text",
  "title",
  "reason_text",
  "attention_text",
  "site_ref",
  "site_label",
  "subject_ref",
  "subject_label",
  "date_label",
  "window_start",
  "window_end",
  "risk_ref",
  "risk_instance_ref",
  "risk_anchor_ref",
  "event_ref",
  "source_locator_ref",
  "source_count",
]);

export const MONITORING_CONTINUITY_CHANGE_COUNT_KEYS = Object.freeze([
  "new",
  "upgraded",
  "continued",
  "downgraded",
  "closed",
  "reopened",
  "needs_rejudgment",
  "mid_high_total",
  "changed_subject_count",
]);

export const MONITORING_CONTINUITY_OBJECT_TYPES = Object.freeze([
  "risk",
  "query_draft",
  "monitoring_output",
]);
export const MONITORING_CONTINUITY_OBJECT_TYPE_TEXTS = Object.freeze({
  risk: "风险",
  query_draft: "Query 草稿",
  monitoring_output: "监查结果项",
});

export const MONITORING_CONTINUITY_CHANGE_KINDS = Object.freeze([
  "new",
  "upgraded",
  "continued",
  "downgraded",
  "closed",
  "reopened",
  "needs_rejudgment",
]);
export const MONITORING_CONTINUITY_CHANGE_KIND_TEXTS = Object.freeze({
  new: "新增",
  upgraded: "升级",
  continued: "持续",
  downgraded: "降级",
  closed: "关闭",
  reopened: "重开",
  needs_rejudgment: "需重新判断",
});

export const MONITORING_CONTINUITY_DISPOSITIONS = Object.freeze([
  "reuse_unchanged",
  "re_evaluate_changed_data",
  "re_evaluate_rule_change",
  "re_evaluate_prior_uncertain",
  "close_with_evidence",
  "blocked_incompatible",
]);
export const MONITORING_CONTINUITY_DISPOSITION_TEXTS = Object.freeze({
  reuse_unchanged: "沿用不变",
  re_evaluate_changed_data: "数据变化，已重新分析",
  re_evaluate_rule_change: "规则变化，已重新分析",
  re_evaluate_prior_uncertain: "上轮依据不足，本轮重新分析",
  close_with_evidence: "已有证据支持关闭",
  blocked_incompatible: "前后版本不可直接比较",
});

export const MONITORING_CONTINUITY_DATA_CHANGE_KINDS = Object.freeze([
  "unchanged",
  "added",
  "revised",
  "deleted",
  "cannot_compare",
  "missing",
]);
export const MONITORING_CONTINUITY_DATA_CHANGE_TEXTS = Object.freeze({
  unchanged: "无变化",
  added: "新增数据",
  revised: "数据修订",
  deleted: "数据删除",
  cannot_compare: "无法直接比较",
  missing: "本轮未见对应记录",
});

export const MONITORING_CONTINUITY_ATTENTION_TEXTS = Object.freeze([
  "",
  "未见记录不代表风险已解除",
  "身份或数据不完整，需重新判断",
  "等级变化待确认",
  "原始记录位置待确认",
]);
export const MONITORING_CONTINUITY_MISSING_DATA_ATTENTION_TEXT = "未见记录不代表风险已解除";

export const MONITORING_CONTINUITY_SEVERITY_TEXTS = Object.freeze(["", "高", "中", "低"]);
export const MONITORING_CONTINUITY_SEVERITY_RANK = Object.freeze({ 高: 3, 中: 2, 低: 1 });

export const MONITORING_CONTINUITY_BASIS_TEXTS = Object.freeze([
  "全量分析",
  "增量分析",
]);
export const MONITORING_CONTINUITY_COMPARED_TEXT = "已与上次监查结果比较";
export const MONITORING_CONTINUITY_FIRST_ANALYSIS_TEXT = "本轮为首次全面分析，无比较基线";
export const MONITORING_CONTINUITY_COMPARISON_TEXTS = Object.freeze([
  MONITORING_CONTINUITY_COMPARED_TEXT,
  MONITORING_CONTINUITY_FIRST_ANALYSIS_TEXT,
]);

const MONITORING_CONTINUITY_TOP_LEVEL_FIELD_SET = new Set(MONITORING_CONTINUITY_TOP_LEVEL_FIELDS);
const MONITORING_CONTINUITY_IDENTITY_FIELD_SET = new Set(MONITORING_CONTINUITY_IDENTITY_FIELDS);
const MONITORING_CONTINUITY_IDENTITY_ALLOWED_FIELD_SET = new Set([
  ...MONITORING_CONTINUITY_IDENTITY_FIELDS,
  ...MONITORING_CONTINUITY_IDENTITY_OPTIONAL_FIELDS,
]);
const MONITORING_CONTINUITY_COMPARISON_FIELD_SET = new Set(MONITORING_CONTINUITY_COMPARISON_FIELDS);
const MONITORING_CONTINUITY_ROW_FIELD_SET = new Set(MONITORING_CONTINUITY_ROW_FIELDS);
const MONITORING_CONTINUITY_CHANGE_COUNT_KEY_SET = new Set(MONITORING_CONTINUITY_CHANGE_COUNT_KEYS);
const MONITORING_CONTINUITY_OBJECT_TYPE_SET = new Set(MONITORING_CONTINUITY_OBJECT_TYPES);
const MONITORING_CONTINUITY_CHANGE_KIND_SET = new Set(MONITORING_CONTINUITY_CHANGE_KINDS);
const MONITORING_CONTINUITY_DISPOSITION_SET = new Set(MONITORING_CONTINUITY_DISPOSITIONS);
const MONITORING_CONTINUITY_DATA_CHANGE_KIND_SET = new Set(MONITORING_CONTINUITY_DATA_CHANGE_KINDS);
const MONITORING_CONTINUITY_ATTENTION_TEXT_SET = new Set(MONITORING_CONTINUITY_ATTENTION_TEXTS);
const MONITORING_CONTINUITY_SEVERITY_TEXT_SET = new Set(MONITORING_CONTINUITY_SEVERITY_TEXTS);
const MONITORING_CONTINUITY_BASIS_TEXT_SET = new Set(MONITORING_CONTINUITY_BASIS_TEXTS);
const MONITORING_CONTINUITY_COMPARISON_TEXT_SET = new Set(MONITORING_CONTINUITY_COMPARISON_TEXTS);
const MONITORING_CONTINUITY_CHANGED_KIND_SET = new Set([
  "new",
  "upgraded",
  "downgraded",
  "closed",
  "reopened",
  "needs_rejudgment",
]);
const MONITORING_CONTINUITY_DIRECTIONAL_KIND_SET = new Set([
  "upgraded",
  "downgraded",
  "continued",
]);

// Internal-identity gate: key names that must never appear in a public
// continuity response, mirroring the product envelope gate.
const CONTINUITY_KEY_EXACT_FORBIDDEN = new Set([
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
const CONTINUITY_KEY_PREFIX_FORBIDDEN = ["authority_", "receipt_", "s4_", "r5_"];

// Public text gate: mirrors the server `_public_continuity_text` marker list
// plus its secret-value pattern. Honest server responses never contain these,
// so the frontend gate can only reject tampered or leaked payloads.
const CONTINUITY_TEXT_FORBIDDEN_MARKERS = [
  "run_id",
  "run_ref",
  "snapshot_ref",
  "cutoff_ref",
  "packet_digest",
  "authority_hash",
  "artifact_member",
  "source_snapshot_sha256",
  ["file", "://"].join(""),
  "/users/",
  "traceback",
  "stdout",
  "stderr",
];
const CONTINUITY_SECRET_VALUE_PATTERN = /(sk-[a-z0-9]{8,}|bearer\s+\S+|api_key=|password=|token=)/i;

const HEX_64 = /^[0-9a-f]{64}$/i;
const ISO_DATE = /^\d{4}-\d{2}-\d{2}$/;
const RESULT_CONTEXT_PREFIX = "result-context:";

export class MedicalMonitoringContinuityProjectionError extends Error {
  constructor(code, message, field = "") {
    super(message);
    this.name = "MedicalMonitoringContinuityProjectionError";
    this.code = code;
    this.field = field;
  }
}

function isRecord(value) {
  return value !== null && typeof value === "object" && !Array.isArray(value);
}

function clean(value) {
  return typeof value === "string" ? value.trim() : "";
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

function continuityError(code, message, field = "") {
  return new MedicalMonitoringContinuityProjectionError(code, message, field);
}

function invalidResult(error, fallback = MONITORING_CONTINUITY_UNAVAILABLE_TEXT) {
  const code = error?.code || "invalid_continuity";
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

function requiredText(value, field, code = "invalid_continuity") {
  const text = clean(value);
  if (!text) {
    throw continuityError(code, `${field} 缺失，本轮变化暂不展示。`, field);
  }
  return text;
}

function optionalText(value, field) {
  if (value === undefined || value === null) return "";
  if (typeof value !== "string") {
    throw continuityError("invalid_continuity", `${field} 格式异常，本轮变化暂不展示。`, field);
  }
  return value.trim();
}

function nonNegativeInt(value, field) {
  if (!Number.isInteger(value) || value < 0) {
    throw continuityError("invalid_continuity", `${field} 计数异常，本轮变化暂不展示。`, field);
  }
  return value;
}

function assertExpectedProject(actual, expected) {
  const expectedProject = clean(expected);
  if (expectedProject && actual !== expectedProject) {
    throw continuityError(
      "continuity_identity_mismatch",
      "本轮变化项目身份不一致，已阻止展示。",
      "identity.project_ref",
    );
  }
}

function keyIsForbidden(key) {
  const lowered = String(key).toLowerCase();
  if (CONTINUITY_KEY_EXACT_FORBIDDEN.has(lowered)) return true;
  if (CONTINUITY_KEY_PREFIX_FORBIDDEN.some((prefix) => lowered.startsWith(prefix))) return true;
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

function textIsForbidden(value) {
  const lowered = value.toLowerCase();
  if (CONTINUITY_TEXT_FORBIDDEN_MARKERS.some((marker) => lowered.includes(marker))) return true;
  return CONTINUITY_SECRET_VALUE_PATTERN.test(value);
}

function findForbiddenText(value, path = "") {
  if (typeof value === "string") {
    return textIsForbidden(value) ? path : null;
  }
  if (Array.isArray(value)) {
    for (let index = 0; index < value.length; index += 1) {
      const found = findForbiddenText(value[index], `${path}[${index}]`);
      if (found) return found;
    }
    return null;
  }
  if (!isRecord(value)) return null;
  for (const [key, item] of Object.entries(value)) {
    const currentPath = path ? `${path}.${key}` : key;
    const found = findForbiddenText(item, currentPath);
    if (found) return found;
  }
  return null;
}

function isoDate(value, field) {
  const text = requiredText(value, field);
  const parsed = new Date(`${text}T00:00:00Z`);
  if (
    !ISO_DATE.test(text)
    || !Number.isFinite(parsed.getTime())
    || parsed.toISOString().slice(0, 10) !== text
  ) {
    throw continuityError("invalid_continuity", `${field} 日期异常，本轮变化暂不展示。`, field);
  }
  return text;
}

function exactFields(value, allowedSet, expectedCount, code, message, field) {
  const keys = Object.keys(value);
  if (
    keys.length !== expectedCount
    || keys.some((key) => !allowedSet.has(key))
  ) {
    throw continuityError(code, message, field);
  }
}

function severityRank(text) {
  return MONITORING_CONTINUITY_SEVERITY_RANK[text] || 0;
}

function severityText(value, field) {
  const text = optionalText(value, field);
  if (!MONITORING_CONTINUITY_SEVERITY_TEXT_SET.has(text)) {
    throw continuityError(
      "invalid_continuity",
      `${field} 风险等级不在公开范围内，本轮变化暂不展示。`,
      field,
    );
  }
  return text;
}

function validateSeverityShape(row, index) {
  const label = `comparison.rows[${index}]`;
  const before = row.severity_before_text;
  const after = row.severity_after_text;
  const isRisk = row.object_type === "risk";

  if (!isRisk) {
    // Query 草稿与监查结果项不得伪造风险等级。
    if (before || after) {
      throw continuityError(
        "invalid_continuity",
        `${label} 非风险行不得携带风险等级，本轮变化暂不展示。`,
        `${label}.severity_after_text`,
      );
    }
    return;
  }

  if (row.change_kind === "new") {
    if (before || !MONITORING_CONTINUITY_SEVERITY_TEXT_SET.has(after)) {
      throw continuityError(
        "invalid_continuity",
        `${label} 新增风险等级形态异常，本轮变化暂不展示。`,
        `${label}.severity_after_text`,
      );
    }
    return;
  }
  if (row.change_kind === "closed") {
    if (after || !MONITORING_CONTINUITY_SEVERITY_TEXT_SET.has(before)) {
      throw continuityError(
        "invalid_continuity",
        `${label} 关闭风险等级形态异常，本轮变化暂不展示。`,
        `${label}.severity_before_text`,
      );
    }
    return;
  }
  if (row.change_kind === "reopened") {
    if (!after || !MONITORING_CONTINUITY_SEVERITY_TEXT_SET.has(after)) {
      throw continuityError(
        "invalid_continuity",
        `${label} 重开风险缺少当前等级，本轮变化暂不展示。`,
        `${label}.severity_after_text`,
      );
    }
    return;
  }
  if (MONITORING_CONTINUITY_DIRECTIONAL_KIND_SET.has(row.change_kind)) {
    const hasBefore = before && MONITORING_CONTINUITY_SEVERITY_TEXT_SET.has(before);
    const hasAfter = after && MONITORING_CONTINUITY_SEVERITY_TEXT_SET.has(after);
    if (!hasBefore || !hasAfter) {
      throw continuityError(
        "invalid_continuity",
        `${label} 等级变化缺少前后等级，本轮变化暂不展示。`,
        `${label}.severity_after_text`,
      );
    }
    const rankBefore = severityRank(before);
    const rankAfter = severityRank(after);
    if (
      (row.change_kind === "upgraded" && rankAfter <= rankBefore)
      || (row.change_kind === "downgraded" && rankAfter >= rankBefore)
      || (row.change_kind === "continued" && rankAfter !== rankBefore)
    ) {
      throw continuityError(
        "invalid_continuity",
        `${label} 等级变化方向与变化类型不符，本轮变化暂不展示。`,
        `${label}.severity_after_text`,
      );
    }
  }
  // needs_rejudgment：after 可为空并回退“等级变化待确认”提示。
}

function normalizeContinuityRow(value, index) {
  if (!isRecord(value)) {
    throw continuityError(
      "invalid_continuity",
      `第 ${index + 1} 条本轮变化格式异常，本轮变化暂不展示。`,
      `comparison.rows[${index}]`,
    );
  }
  const label = `comparison.rows[${index}]`;
  exactFields(
    value,
    MONITORING_CONTINUITY_ROW_FIELD_SET,
    MONITORING_CONTINUITY_ROW_FIELDS.length,
    "invalid_continuity",
    `${label} 字段不完整，本轮变化暂不展示。`,
    label,
  );

  const row = {
    row_ref: requiredText(value.row_ref, `${label}.row_ref`),
    object_type: requiredText(value.object_type, `${label}.object_type`),
    object_type_text: requiredText(value.object_type_text, `${label}.object_type_text`),
    ordinal: nonNegativeInt(value.ordinal, `${label}.ordinal`),
    change_kind: requiredText(value.change_kind, `${label}.change_kind`),
    change_text: requiredText(value.change_text, `${label}.change_text`),
    disposition: requiredText(value.disposition, `${label}.disposition`),
    disposition_text: requiredText(value.disposition_text, `${label}.disposition_text`),
    data_change_kind: requiredText(value.data_change_kind, `${label}.data_change_kind`),
    data_change_text: requiredText(value.data_change_text, `${label}.data_change_text`),
    severity_before_text: severityText(value.severity_before_text, `${label}.severity_before_text`),
    severity_after_text: severityText(value.severity_after_text, `${label}.severity_after_text`),
    title: requiredText(value.title, `${label}.title`),
    reason_text: optionalText(value.reason_text, `${label}.reason_text`),
    attention_text: optionalText(value.attention_text, `${label}.attention_text`),
    site_ref: requiredText(value.site_ref, `${label}.site_ref`),
    site_label: requiredText(value.site_label, `${label}.site_label`),
    subject_ref: requiredText(value.subject_ref, `${label}.subject_ref`),
    subject_label: requiredText(value.subject_label, `${label}.subject_label`),
    date_label: optionalText(value.date_label, `${label}.date_label`),
    window_start: "",
    window_end: "",
    risk_ref: optionalText(value.risk_ref, `${label}.risk_ref`),
    risk_instance_ref: optionalText(value.risk_instance_ref, `${label}.risk_instance_ref`),
    risk_anchor_ref: optionalText(value.risk_anchor_ref, `${label}.risk_anchor_ref`),
    event_ref: optionalText(value.event_ref, `${label}.event_ref`),
    source_locator_ref: optionalText(value.source_locator_ref, `${label}.source_locator_ref`),
    source_count: nonNegativeInt(value.source_count, `${label}.source_count`),
  };

  if (!MONITORING_CONTINUITY_OBJECT_TYPE_SET.has(row.object_type)) {
    throw continuityError(
      "invalid_continuity",
      `${label} 对象类别不在公开范围内，本轮变化暂不展示。`,
      `${label}.object_type`,
    );
  }
  if (row.object_type_text !== MONITORING_CONTINUITY_OBJECT_TYPE_TEXTS[row.object_type]) {
    throw continuityError(
      "invalid_continuity",
      `${label} 对象类别中文不一致，本轮变化暂不展示。`,
      `${label}.object_type_text`,
    );
  }
  if (!MONITORING_CONTINUITY_CHANGE_KIND_SET.has(row.change_kind)) {
    throw continuityError(
      "invalid_continuity",
      `${label} 变化类型不在公开闭集内，本轮变化暂不展示。`,
      `${label}.change_kind`,
    );
  }
  if (row.change_text !== MONITORING_CONTINUITY_CHANGE_KIND_TEXTS[row.change_kind]) {
    throw continuityError(
      "invalid_continuity",
      `${label} 变化类型中文不一致，本轮变化暂不展示。`,
      `${label}.change_text`,
    );
  }
  if (!MONITORING_CONTINUITY_DISPOSITION_SET.has(row.disposition)) {
    throw continuityError(
      "invalid_continuity",
      `${label} 处置不在公开闭集内，本轮变化暂不展示。`,
      `${label}.disposition`,
    );
  }
  if (row.disposition_text !== MONITORING_CONTINUITY_DISPOSITION_TEXTS[row.disposition]) {
    throw continuityError(
      "invalid_continuity",
      `${label} 处置中文不一致，本轮变化暂不展示。`,
      `${label}.disposition_text`,
    );
  }
  if (!MONITORING_CONTINUITY_DATA_CHANGE_KIND_SET.has(row.data_change_kind)) {
    throw continuityError(
      "invalid_continuity",
      `${label} 数据变化不在公开闭集内，本轮变化暂不展示。`,
      `${label}.data_change_kind`,
    );
  }
  if (row.data_change_text !== MONITORING_CONTINUITY_DATA_CHANGE_TEXTS[row.data_change_kind]) {
    throw continuityError(
      "invalid_continuity",
      `${label} 数据变化中文不一致，本轮变化暂不展示。`,
      `${label}.data_change_text`,
    );
  }
  if (!MONITORING_CONTINUITY_ATTENTION_TEXT_SET.has(row.attention_text)) {
    throw continuityError(
      "invalid_continuity",
      `${label} 提示文本不在公开闭集内，本轮变化暂不展示。`,
      `${label}.attention_text`,
    );
  }
  if (
    row.data_change_kind === "missing"
    && row.attention_text !== MONITORING_CONTINUITY_MISSING_DATA_ATTENTION_TEXT
  ) {
    throw continuityError(
      "invalid_continuity",
      `${label} 本轮未见对应记录时必须同时提示风险未解除，本轮变化暂不展示。`,
      `${label}.attention_text`,
    );
  }

  row.window_start = isoDate(value.window_start, `${label}.window_start`);
  row.window_end = isoDate(value.window_end, `${label}.window_end`);
  if (row.window_start > row.window_end) {
    throw continuityError(
      "invalid_continuity",
      `${label} 时间窗起止倒置，本轮变化暂不展示。`,
      `${label}.window_start`,
    );
  }

  validateSeverityShape(row, index);

  if (row.object_type === "risk") {
    if (!row.risk_instance_ref) {
      throw continuityError(
        "invalid_continuity",
        `${label} 风险行缺少稳定风险身份，本轮变化暂不展示。`,
        `${label}.risk_instance_ref`,
      );
    }
  } else if (!row.event_ref) {
    throw continuityError(
      "invalid_continuity",
      `${label} 非风险行缺少事件定位，本轮变化暂不展示。`,
      `${label}.event_ref`,
    );
  }

  if ((row.source_locator_ref === "") !== (row.source_count === 0)) {
    throw continuityError(
      "invalid_continuity",
      `${label} 来源定位与来源计数不一致，本轮变化暂不展示。`,
      `${label}.source_count`,
    );
  }

  return freeze(row);
}

// Server-frozen continuity order (router `_continuity_row_sort_key`):
// the frontend may filter but must never reorder, so the received sequence
// must already be non-decreasing under this key.
export function monitoringContinuityRowSortKey(row) {
  const objectType = clean(row?.object_type);
  const changeKind = clean(row?.change_kind);
  const severityAfter = clean(row?.severity_after_text);
  const severityBefore = clean(row?.severity_before_text);
  const ordinal = Number.isInteger(row?.ordinal) ? row.ordinal : 0;
  const rowRef = clean(row?.row_ref);

  const priorityKinds = new Set(["upgraded", "new", "reopened", "needs_rejudgment"]);
  let group;
  if (objectType === "risk") {
    if (severityAfter === "高" && priorityKinds.has(changeKind)) group = 0;
    else if (severityAfter === "中" && priorityKinds.has(changeKind)) group = 1;
    else if (
      severityAfter === "高"
      || severityAfter === "中"
      || (changeKind === "closed" && (severityBefore === "高" || severityBefore === "中"))
    ) group = 2;
    else group = 3;
  } else if (objectType === "query_draft") group = 4;
  else if (objectType === "monitoring_output") group = 5;
  else group = 6;
  return [group, ordinal, rowRef];
}

function compareSortKeys(a, b) {
  if (a[0] !== b[0]) return a[0] - b[0];
  if (a[1] !== b[1]) return a[1] - b[1];
  return a[2] < b[2] ? -1 : a[2] > b[2] ? 1 : 0;
}

// Rebuild the nine change_counts from rows (v0.2 §16 口径). Multiple
// continuity rows may share one risk_instance_ref for Journey dual-entry
// switchers; mid/high totals still count unique risk instances once.
export function rebuildMonitoringContinuityChangeCounts(rows) {
  const counts = {
    new: 0,
    upgraded: 0,
    continued: 0,
    downgraded: 0,
    closed: 0,
    reopened: 0,
    needs_rejudgment: 0,
    mid_high_total: 0,
    changed_subject_count: 0,
  };
  const changedSubjects = new Set();
  const midHighInstances = new Set();
  for (const row of rows) {
    if (!isRecord(row) || !MONITORING_CONTINUITY_OBJECT_TYPE_SET.has(clean(row.object_type))) {
      throw continuityError(
        "invalid_continuity",
        "本轮变化行格式异常，无法核对摘要计数。",
        "comparison.rows",
      );
    }
    if (row.object_type !== "risk") continue;
    if (!MONITORING_CONTINUITY_CHANGE_KIND_SET.has(row.change_kind)) {
      throw continuityError(
        "invalid_continuity",
        "本轮变化行变化类型异常，无法核对摘要计数。",
        "comparison.change_counts",
      );
    }
    if (!clean(row.risk_instance_ref)) {
      throw continuityError(
        "invalid_continuity",
        "风险行缺少稳定风险身份，无法核对摘要计数。",
        "comparison.rows",
      );
    }
    counts[row.change_kind] += 1;
    if (row.severity_after_text === "高" || row.severity_after_text === "中") {
      midHighInstances.add(row.risk_instance_ref);
    }
    if (MONITORING_CONTINUITY_CHANGED_KIND_SET.has(row.change_kind) && clean(row.subject_ref)) {
      changedSubjects.add(row.subject_ref);
    }
  }
  counts.mid_high_total = midHighInstances.size;
  counts.changed_subject_count = changedSubjects.size;
  return Object.freeze(counts);
}

function normalizeContinuityIdentity(value, expected) {
  if (!isRecord(value)) {
    throw continuityError(
      "invalid_continuity",
      "本轮变化身份格式异常，本轮变化暂不展示。",
      "identity",
    );
  }
  const keys = Object.keys(value);
  if (
    keys.length < MONITORING_CONTINUITY_IDENTITY_FIELDS.length
    || keys.length > MONITORING_CONTINUITY_IDENTITY_ALLOWED_FIELD_SET.size
    || keys.some((key) => !MONITORING_CONTINUITY_IDENTITY_ALLOWED_FIELD_SET.has(key))
    || MONITORING_CONTINUITY_IDENTITY_FIELDS.some((key) => !(key in value))
  ) {
    throw continuityError(
      "invalid_continuity",
      "本轮变化身份字段不完整，本轮变化暂不展示。",
      "identity",
    );
  }
  const identity = {
    project_ref: requiredText(value.project_ref, "identity.project_ref"),
    public_run_token: requiredText(value.public_run_token, "identity.public_run_token"),
    snapshot_token: requiredText(value.snapshot_token, "identity.snapshot_token"),
    data_cutoff_text: requiredText(value.data_cutoff_text, "identity.data_cutoff_text"),
    mode_text: requiredText(value.mode_text, "identity.mode_text"),
    site_scope_text: optionalText(value.site_scope_text, "identity.site_scope_text"),
  };
  if ("site_ref" in value) {
    identity.site_ref = requiredText(value.site_ref, "identity.site_ref");
  }

  assertExpectedProject(identity.project_ref, expected.projectId);

  const expectedSiteRef = clean(expected.siteRef);
  if (expectedSiteRef) {
    if (identity.site_ref !== expectedSiteRef) {
      throw continuityError(
        "continuity_identity_mismatch",
        "本轮变化中心身份不一致，已阻止展示。",
        "identity.site_ref",
      );
    }
  } else if ("site_ref" in identity) {
    throw continuityError(
      "continuity_identity_mismatch",
      "本轮变化返回了未请求的中心范围，已阻止展示。",
      "identity.site_ref",
    );
  }
  return identity;
}

function normalizeContinuityComparison(value) {
  if (!isRecord(value)) {
    throw continuityError(
      "invalid_continuity",
      "本轮变化比较内容格式异常，本轮变化暂不展示。",
      "comparison",
    );
  }
  exactFields(
    value,
    MONITORING_CONTINUITY_COMPARISON_FIELD_SET,
    MONITORING_CONTINUITY_COMPARISON_FIELDS.length,
    "invalid_continuity",
    "本轮变化比较字段不完整，本轮变化暂不展示。",
    "comparison",
  );

  if (value.available !== true) {
    throw continuityError(
      "invalid_continuity",
      "本轮变化比较状态异常，本轮变化暂不展示。",
      "comparison.available",
    );
  }
  const basisText = requiredText(value.basis_text, "comparison.basis_text");
  if (!MONITORING_CONTINUITY_BASIS_TEXT_SET.has(basisText)) {
    throw continuityError(
      "invalid_continuity",
      "本轮变化执行基础不在公开闭集内，本轮变化暂不展示。",
      "comparison.basis_text",
    );
  }
  const comparisonText = requiredText(value.comparison_text, "comparison.comparison_text");
  if (!MONITORING_CONTINUITY_COMPARISON_TEXT_SET.has(comparisonText)) {
    throw continuityError(
      "invalid_continuity",
      "本轮变化比较说明不在公开闭集内，本轮变化暂不展示。",
      "comparison.comparison_text",
    );
  }
  const sourceRunText = optionalText(value.source_run_text, "comparison.source_run_text");
  if ((sourceRunText === "") !== (comparisonText === MONITORING_CONTINUITY_FIRST_ANALYSIS_TEXT)) {
    throw continuityError(
      "invalid_continuity",
      "本轮变化比较说明与上次批次不一致，本轮变化暂不展示。",
      "comparison.comparison_text",
    );
  }

  const countsValue = value.change_counts;
  if (!isRecord(countsValue)) {
    throw continuityError(
      "invalid_continuity",
      "本轮变化摘要计数格式异常，本轮变化暂不展示。",
      "comparison.change_counts",
    );
  }
  exactFields(
    countsValue,
    MONITORING_CONTINUITY_CHANGE_COUNT_KEY_SET,
    MONITORING_CONTINUITY_CHANGE_COUNT_KEYS.length,
    "invalid_continuity",
    "本轮变化摘要计数字段不完整，本轮变化暂不展示。",
    "comparison.change_counts",
  );
  const changeCounts = {};
  for (const key of MONITORING_CONTINUITY_CHANGE_COUNT_KEYS) {
    changeCounts[key] = nonNegativeInt(countsValue[key], `comparison.change_counts.${key}`);
  }

  if (!Array.isArray(value.rows)) {
    throw continuityError(
      "invalid_continuity",
      "本轮变化列表格式异常，本轮变化暂不展示。",
      "comparison.rows",
    );
  }
  if (value.rows.length > MONITORING_CONTINUITY_ROW_LIMIT) {
    throw continuityError(
      "invalid_continuity",
      "本轮变化列表超出返回上限，本轮变化暂不展示。",
      "comparison.rows",
    );
  }
  const rows = value.rows.map(normalizeContinuityRow);

  const seenRowRefs = new Set();
  for (const row of rows) {
    if (seenRowRefs.has(row.row_ref)) {
      throw continuityError(
        "invalid_continuity",
        "本轮变化行引用重复，本轮变化暂不展示。",
        "comparison.rows",
      );
    }
    seenRowRefs.add(row.row_ref);
  }
  for (let index = 1; index < rows.length; index += 1) {
    if (compareSortKeys(monitoringContinuityRowSortKey(rows[index - 1]), monitoringContinuityRowSortKey(rows[index])) > 0) {
      throw continuityError(
        "invalid_continuity",
        "本轮变化列表顺序与服务端权威顺序不一致，本轮变化暂不展示。",
        "comparison.rows",
      );
    }
  }

  const shownCount = nonNegativeInt(value.shown_count, "comparison.shown_count");
  const totalCount = nonNegativeInt(value.total_count, "comparison.total_count");
  if (typeof value.truncated !== "boolean") {
    throw continuityError(
      "invalid_continuity",
      "本轮变化截断状态异常，本轮变化暂不展示。",
      "comparison.truncated",
    );
  }
  const truncated = value.truncated;
  if (
    rows.length !== shownCount
    || shownCount !== Math.min(totalCount, MONITORING_CONTINUITY_ROW_LIMIT)
    || truncated !== (totalCount > MONITORING_CONTINUITY_ROW_LIMIT)
    || totalCount < rows.length
  ) {
    throw continuityError(
      "invalid_continuity",
      "本轮变化展示数量与截断状态不一致，本轮变化暂不展示。",
      "comparison.shown_count",
    );
  }

  const rebuilt = rebuildMonitoringContinuityChangeCounts(rows);
  for (const key of MONITORING_CONTINUITY_CHANGE_COUNT_KEYS) {
    if (rebuilt[key] > changeCounts[key] || (!truncated && rebuilt[key] !== changeCounts[key])) {
      throw continuityError(
        "invalid_continuity",
        "本轮变化摘要计数无法与列表重建一致，本轮变化暂不展示。",
        `comparison.change_counts.${key}`,
      );
    }
  }

  // Wire-format keys are preserved verbatim: the response digest is computed
  // by the server over exactly these field names, so the frontend canonical
  // payload must reuse them without renaming.
  return {
    available: true,
    basis_text: basisText,
    comparison_text: comparisonText,
    source_run_text: sourceRunText,
    change_counts: freeze(changeCounts),
    rows: freeze(rows),
    shown_count: shownCount,
    total_count: totalCount,
    truncated,
  };
}

function normalizeContinuityEnvelopeOrThrow(payload, expected = {}) {
  if (!isRecord(payload) || Array.isArray(payload)) {
    throw continuityError(
      "invalid_continuity",
      MONITORING_CONTINUITY_UNAVAILABLE_TEXT,
      "response",
    );
  }
  exactFields(
    payload,
    MONITORING_CONTINUITY_TOP_LEVEL_FIELD_SET,
    MONITORING_CONTINUITY_TOP_LEVEL_FIELDS.length,
    "invalid_continuity",
    "本轮变化响应字段不完整，本轮变化暂不展示。",
    "response",
  );
  const forbiddenKey = findForbiddenKey(payload);
  if (forbiddenKey) {
    throw continuityError(
      "public_identity_forbidden",
      `本轮变化响应包含不可公开字段：${forbiddenKey}。`,
      forbiddenKey,
    );
  }
  const forbiddenText = findForbiddenText(payload);
  if (forbiddenText) {
    throw continuityError(
      "public_text_forbidden",
      `本轮变化响应包含不可公开文本：${forbiddenText}。`,
      forbiddenText,
    );
  }

  const resultContextToken = requiredText(payload.result_context_token, "result_context_token");
  if (!resultContextToken.startsWith(RESULT_CONTEXT_PREFIX)) {
    throw continuityError(
      "invalid_continuity",
      "本轮变化结果上下文异常，本轮变化暂不展示。",
      "result_context_token",
    );
  }
  const expectedToken = clean(expected.resultContextToken);
  if (expectedToken && resultContextToken !== expectedToken) {
    throw continuityError(
      "continuity_identity_mismatch",
      "本轮变化结果上下文不一致，已阻止展示。",
      "result_context_token",
    );
  }

  const identity = normalizeContinuityIdentity(payload.identity, expected || {});
  const comparison = normalizeContinuityComparison(payload.comparison);

  if (typeof payload.response_digest !== "string" || !HEX_64.test(payload.response_digest)) {
    throw continuityError(
      "invalid_continuity",
      "本轮变化响应摘要格式异常，本轮变化暂不展示。",
      "response_digest",
    );
  }

  return {
    kind: "continuity",
    resultContextToken,
    identity: freeze(identity),
    comparison: freeze(comparison),
    responseDigest: payload.response_digest.toLowerCase(),
  };
}

export function normalizeMonitoringContinuityEnvelope(payload, expected = {}) {
  return freeze(normalizeContinuityEnvelopeOrThrow(payload, expected));
}

export const validateMonitoringContinuityEnvelope = normalizeMonitoringContinuityEnvelope;

export function safeValidateMonitoringContinuityEnvelope(payload, expected = {}) {
  try {
    return normalizedResult(normalizeContinuityEnvelopeOrThrow(payload, expected));
  } catch (error) {
    return invalidResult(error);
  }
}

export function projectMonitoringContinuity(payload, expected = {}) {
  try {
    return freeze(normalizeContinuityEnvelopeOrThrow(payload, expected));
  } catch (error) {
    return invalidResult(error);
  }
}

function canonicalize(value) {
  if (Array.isArray(value)) return value.map(canonicalize);
  if (isRecord(value)) {
    return Object.fromEntries(
      Object.keys(value).sort().map((key) => [key, canonicalize(value[key])]),
    );
  }
  return value;
}

export function canonicalMonitoringContinuityPayload(envelope, expected = {}) {
  const normalized = envelope?.kind === "continuity"
    ? envelope
    : normalizeMonitoringContinuityEnvelope(envelope, expected);
  return JSON.stringify(canonicalize({
    identity: normalized.identity,
    comparison: normalized.comparison,
  }));
}

export async function computeMonitoringContinuityResponseDigest(envelope, expected = {}) {
  if (!globalThis.crypto?.subtle || typeof TextEncoder !== "function") {
    throw continuityError(
      "continuity_digest_unavailable",
      MONITORING_CONTINUITY_UNAVAILABLE_TEXT,
      "response_digest",
    );
  }
  const bytes = new TextEncoder().encode(canonicalMonitoringContinuityPayload(envelope, expected));
  const digest = await globalThis.crypto.subtle.digest("SHA-256", bytes);
  return [...new Uint8Array(digest)].map((value) => value.toString(16).padStart(2, "0")).join("");
}

export async function verifyMonitoringContinuityEnvelope(payload, expected = {}) {
  const normalized = normalizeMonitoringContinuityEnvelope(payload, expected);
  const actual = await computeMonitoringContinuityResponseDigest(normalized, expected);
  if (actual !== normalized.responseDigest) {
    throw continuityError(
      "continuity_response_digest_mismatch",
      MONITORING_CONTINUITY_UNAVAILABLE_TEXT,
      "response_digest",
    );
  }
  return normalized;
}

export async function safeVerifyMonitoringContinuityEnvelope(payload, expected = {}) {
  try {
    return normalizedResult(await verifyMonitoringContinuityEnvelope(payload, expected));
  } catch (error) {
    return invalidResult(error);
  }
}

function continuityErrorCode(error) {
  const detail = error && typeof error === "object" ? error.detail : null;
  if (detail && typeof detail === "object" && typeof detail.code === "string") return detail.code;
  return typeof error?.code === "string" ? error.code : "";
}

// Contract §5: continuity_unavailable and frontend validation failures both
// degrade to a single unavailable text; the existing result boards stay.
export function projectMonitoringContinuityError(error) {
  return freeze({
    kind: "unavailable",
    code: continuityErrorCode(error),
    text: MONITORING_CONTINUITY_UNAVAILABLE_TEXT,
  });
}
