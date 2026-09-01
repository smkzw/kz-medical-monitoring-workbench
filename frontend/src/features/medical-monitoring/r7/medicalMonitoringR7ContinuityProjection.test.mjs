import assert from "node:assert/strict";
import { createHash } from "node:crypto";

import {
  R7_CONTINUITY_ATTENTION_TEXTS,
  R7_CONTINUITY_CHANGE_COUNT_KEYS,
  R7_CONTINUITY_COMPARED_TEXT,
  R7_CONTINUITY_FIRST_ANALYSIS_TEXT,
  R7_CONTINUITY_ROW_FIELDS,
  R7_CONTINUITY_ROW_LIMIT,
  R7_CONTINUITY_UNAVAILABLE_TEXT,
  canonicalR7ContinuityPayload,
  computeR7ContinuityResponseDigest,
  normalizeR7ContinuityEnvelope,
  projectR7Continuity,
  projectR7ContinuityError,
  rebuildR7ContinuityChangeCounts,
  r7ContinuityRowSortKey,
  safeValidateR7ContinuityEnvelope,
  safeVerifyR7ContinuityEnvelope,
  verifyR7ContinuityEnvelope,
} from "./medicalMonitoringR7ContinuityProjection.mjs";

let passed = 0;
function check(condition, message) {
  assert.equal(Boolean(condition), true, message);
  passed += 1;
}

// Independent server-format digest: mirrors mm_r7.launch_registry.content_digest
// (sha256 over canonical JSON with sorted keys, compact separators, raw UTF-8).
function canonicalServer(value) {
  if (Array.isArray(value)) return value.map(canonicalServer);
  if (value !== null && typeof value === "object") {
    return Object.fromEntries(
      Object.keys(value).sort().map((key) => [key, canonicalServer(value[key])]),
    );
  }
  return value;
}
function serverDigest(identity, comparison) {
  return createHash("sha256")
    .update(JSON.stringify(canonicalServer({ identity, comparison })), "utf8")
    .digest("hex");
}

function row(overrides = {}) {
  return {
    row_ref: "continuity-row-1",
    object_type: "risk",
    object_type_text: "风险",
    ordinal: 1,
    change_kind: "new",
    change_text: "新增",
    disposition: "reuse_unchanged",
    disposition_text: "沿用不变",
    data_change_kind: "added",
    data_change_text: "新增数据",
    severity_before_text: "",
    severity_after_text: "高",
    title: "不良事件与记录一致性",
    reason_text: "本轮记录与上轮不一致，已重新分析。",
    attention_text: "",
    site_ref: "site/01",
    site_label: "中心一",
    subject_ref: "S/01",
    subject_label: "受试者 001",
    date_label: "2026-02-14",
    window_start: "2026-01-01",
    window_end: "2026-03-31",
    risk_ref: "s7-risk-ae-06021",
    risk_instance_ref: "s7-risk-ae-06021",
    risk_anchor_ref: "s7-anchor-ae-06021",
    event_ref: "s7-event-ae-06021",
    source_locator_ref: "s7-source-ae-06021",
    source_count: 1,
    ...overrides,
  };
}

function riskRow(ordinal, kind, before, after, subject, overrides = {}) {
  const kindTexts = {
    new: "新增",
    upgraded: "升级",
    continued: "持续",
    downgraded: "降级",
    closed: "关闭",
    reopened: "重开",
    needs_rejudgment: "需重新判断",
  };
  const disposition = kind === "closed" ? "close_with_evidence" : "reuse_unchanged";
  const dispositionText = kind === "closed" ? "已有证据支持关闭" : "沿用不变";
  const dataChange = kind === "continued" ? "unchanged" : "added";
  const dataText = kind === "continued" ? "无变化" : "新增数据";
  return row({
    row_ref: `continuity-row-${ordinal}`,
    ordinal,
    change_kind: kind,
    change_text: kindTexts[kind],
    disposition,
    disposition_text: dispositionText,
    data_change_kind: dataChange,
    data_change_text: dataText,
    severity_before_text: before,
    severity_after_text: after,
    subject_ref: subject,
    subject_label: `受试者 ${subject}`,
    risk_ref: `s7-risk-${ordinal}`,
    risk_instance_ref: `s7-risk-${ordinal}`,
    risk_anchor_ref: `s7-anchor-${ordinal}`,
    event_ref: `s7-event-${ordinal}`,
    source_locator_ref: `s7-source-${ordinal}`,
    source_count: 1,
    ...overrides,
  });
}

function queryRow(ordinal, overrides = {}) {
  return row({
    row_ref: `continuity-row-${ordinal}`,
    object_type: "query_draft",
    object_type_text: "Query 草稿",
    ordinal,
    change_kind: "new",
    change_text: "新增",
    severity_before_text: "",
    severity_after_text: "",
    title: "实验室复查 Query 草稿",
    subject_ref: "S/05",
    subject_label: "受试者 S/05",
    risk_ref: "",
    risk_instance_ref: "",
    risk_anchor_ref: "",
    event_ref: `s7-event-q-${ordinal}`,
    source_locator_ref: "",
    source_count: 0,
    attention_text: "原始记录位置待确认",
    ...overrides,
  });
}

function outputRow(ordinal, overrides = {}) {
  return row({
    row_ref: `continuity-row-${ordinal}`,
    object_type: "monitoring_output",
    object_type_text: "监查结果项",
    ordinal,
    change_kind: "continued",
    change_text: "持续",
    severity_before_text: "",
    severity_after_text: "",
    title: "监查发现跟踪项",
    subject_ref: "S/06",
    subject_label: "受试者 S/06",
    risk_ref: "",
    risk_instance_ref: "",
    risk_anchor_ref: "",
    event_ref: `s7-event-o-${ordinal}`,
    source_locator_ref: "s7-source-o-1",
    source_count: 1,
    ...overrides,
  });
}

const HAPPY_ROWS = Object.freeze([
  // Server order: (group, ordinal) ascending.
  riskRow(1, "new", "", "高", "S/01"),
  riskRow(2, "upgraded", "中", "高", "S/01"),
  riskRow(5, "reopened", "", "高", "S/03"),
  riskRow(4, "closed", "中", "", "S/02", {
    data_change_kind: "missing",
    data_change_text: "本轮未见对应记录",
    attention_text: "未见记录不代表风险已解除",
  }),
  riskRow(7, "downgraded", "高", "中", "S/04"),
  riskRow(3, "continued", "低", "低", "S/02"),
  riskRow(6, "needs_rejudgment", "", "", "S/03", {
    disposition: "re_evaluate_prior_uncertain",
    disposition_text: "上轮依据不足，本轮重新分析",
    data_change_kind: "cannot_compare",
    data_change_text: "无法直接比较",
    attention_text: "身份或数据不完整，需重新判断",
    source_locator_ref: "",
    source_count: 0,
  }),
  queryRow(8),
  outputRow(9),
]);

function envelope(rows, {
  siteRef,
  counts,
  shownCount,
  totalCount,
  truncated,
  digest = "0".repeat(64),
  identityOverrides = {},
  comparisonOverrides = {},
} = {}) {
  return {
    result_context_token: "result-context:01",
    identity: {
      project_ref: "project-a",
      public_run_token: "run:09",
      snapshot_token: "snapshot:09",
      data_cutoff_text: "2026-03-31",
      mode_text: "日常监查",
      site_scope_text: "中心一、中心二",
      ...(siteRef ? { site_ref: siteRef } : {}),
      ...identityOverrides,
    },
    comparison: {
      available: true,
      basis_text: "增量分析",
      comparison_text: R7_CONTINUITY_COMPARED_TEXT,
      source_run_text: "2026-03-01 监查批次",
      change_counts: counts || rebuildR7ContinuityChangeCounts(rows),
      rows,
      shown_count: shownCount ?? rows.length,
      total_count: totalCount ?? rows.length,
      truncated: truncated ?? false,
      ...comparisonOverrides,
    },
    response_digest: digest,
  };
}

const EXPECTED_TOP_KEYS = ["result_context_token", "identity", "comparison", "response_digest"];

// --- happy paths ---
const okEnvelope = envelope([...HAPPY_ROWS]);
const okNormalized = normalizeR7ContinuityEnvelope(okEnvelope);
check(okNormalized.kind === "continuity", "valid continuity response normalizes to the continuity kind");
check(okNormalized.resultContextToken === "result-context:01", "normalization preserves the public result context");
check(okNormalized.identity.project_ref === "project-a", "identity project ref is preserved");
check(okNormalized.comparison.rows.length === HAPPY_ROWS.length, "all rows survive normalization");
check(okNormalized.comparison.rows[0].change_kind === "new", "rows keep wire-format keys for the product layer");
check(
  Object.keys(okEnvelope).every((key) => EXPECTED_TOP_KEYS.includes(key)),
  "fixture matches the frozen top-level field set",
);
check(R7_CONTINUITY_ROW_FIELDS.length === 28, "row field set stays at the frozen 28 public fields");
check(R7_CONTINUITY_CHANGE_COUNT_KEYS.length === 9, "change counts stay at the frozen nine keys");
check(R7_CONTINUITY_ATTENTION_TEXTS.length === 5, "attention texts stay on the frozen five-value closed set");

const safeOk = safeValidateR7ContinuityEnvelope(okEnvelope, {
  projectId: "project-a",
  resultContextToken: "result-context:01",
  siteRef: "",
});
check(safeOk.ok === true && safeOk.value.kind === "continuity", "safe validation accepts a valid response with expected identity");

const projected = projectR7Continuity(envelope([...HAPPY_ROWS], { siteRef: "site/01" }), {
  projectId: "project-a",
  resultContextToken: "result-context:01",
  siteRef: "site/01",
});
check(projected.kind === "continuity" && projected.identity.site_ref === "site/01", "site-bound projection keeps the requested center identity");

const firstAnalysis = envelope([queryRow(1)], {
  counts: {
    new: 0, upgraded: 0, continued: 0, downgraded: 0, closed: 0,
    reopened: 0, needs_rejudgment: 0, mid_high_total: 0, changed_subject_count: 0,
  },
  comparisonOverrides: {
    basis_text: "全量分析",
    comparison_text: R7_CONTINUITY_FIRST_ANALYSIS_TEXT,
    source_run_text: "",
  },
});
check(normalizeR7ContinuityEnvelope(firstAnalysis).comparison.comparison_text === R7_CONTINUITY_FIRST_ANALYSIS_TEXT, "first-analysis copy passes with an empty source run text");

// --- rebuild: nine counts (v0.2 §16 口径) ---
const rebuilt = rebuildR7ContinuityChangeCounts(HAPPY_ROWS);
check(rebuilt.new === 1 && rebuilt.upgraded === 1 && rebuilt.continued === 1, "rebuild counts new/upgraded/continued");
check(rebuilt.downgraded === 1 && rebuilt.closed === 1 && rebuilt.reopened === 1 && rebuilt.needs_rejudgment === 1, "rebuild counts downgraded/closed/reopened/needs_rejudgment");
check(rebuilt.mid_high_total === 4, "rebuild counts mid/high current severities only");
check(rebuilt.changed_subject_count === 4, "rebuild counts distinct changed subjects and ignores continued-only subjects");
const continuedOnly = rebuildR7ContinuityChangeCounts([riskRow(1, "continued", "低", "低", "S/01")]);
check(continuedOnly.changed_subject_count === 0, "continued-only rows do not create changed subjects");
check(continuedOnly.mid_high_total === 0, "low-severity continued rows stay out of the mid/high total");
const dualInstance = rebuildR7ContinuityChangeCounts([
  riskRow(1, "new", "", "高", "S/01"),
  riskRow(2, "upgraded", "中", "高", "S/01", { risk_instance_ref: "s7-risk-1", risk_ref: "s7-risk-1", risk_anchor_ref: "s7-anchor-1", event_ref: "s7-event-1" }),
]);
check(dualInstance.new === 1 && dualInstance.upgraded === 1 && dualInstance.mid_high_total === 1, "shared risk_instance_ref rows count each change kind and unique mid/high once");
assert.throws(() => rebuildR7ContinuityChangeCounts([
  riskRow(1, "new", "", "高", "S/01", { risk_instance_ref: "" }),
]), "risk rows without a stable identity fail the count rebuild closed");
passed += 4;

// --- exact field sets ---
assert.throws(
  () => normalizeR7ContinuityEnvelope({ ...okEnvelope, extra_field: true }),
  "extra top-level fields fail closed",
);
assert.throws(
  () => normalizeR7ContinuityEnvelope(envelope(HAPPY_ROWS.map((r, i) => (
    i === 0 ? (({ disposition_text, ...rest }) => rest)(r) : r
  )))),
  "rows missing a public field fail closed",
);
assert.throws(
  () => normalizeR7ContinuityEnvelope(envelope(HAPPY_ROWS.map((r, i) => (
    i === 0 ? { ...r, internal_note: "x" } : r
  )))),
  "rows with extra fields fail closed",
);
assert.throws(
  () => normalizeR7ContinuityEnvelope(envelope([...HAPPY_ROWS], {
    identityOverrides: { site_ref: "site/01", extra_identity: "x" },
  })),
  "identity with unknown fields fails closed",
);
assert.throws(
  () => normalizeR7ContinuityEnvelope({
    ...okEnvelope,
    identity: { ...okEnvelope.identity, data_cutoff_text: undefined },
  }),
  "identity without the cutoff text fails closed",
);
passed += 6;

// --- internal-field gate ---
const forbiddenKeyPayload = envelope([...HAPPY_ROWS], {
  comparisonOverrides: { r5_authority_packet_id: "internal" },
});
let forbiddenKeyResult = safeValidateR7ContinuityEnvelope(forbiddenKeyPayload);
check(forbiddenKeyResult.ok === false && forbiddenKeyResult.code === "public_identity_forbidden", "internal identity keys fail closed with the public gate code");

const forbiddenValuePayload = envelope([
  { ...HAPPY_ROWS[0], title: "标题包含 run_id 泄露" },
  ...HAPPY_ROWS.slice(1),
]);
let forbiddenTextResult = safeValidateR7ContinuityEnvelope(forbiddenValuePayload);
check(forbiddenTextResult.ok === false && forbiddenTextResult.code === "public_text_forbidden", "label values carrying internal markers fail closed");

const secretValuePayload = envelope([
  { ...HAPPY_ROWS[0], reason_text: "详见 token=abc123" },
  ...HAPPY_ROWS.slice(1),
]);
check(safeValidateR7ContinuityEnvelope(secretValuePayload).ok === false, "secret-shaped public text fails closed");
passed += 3;

// --- Chinese closed sets ---
const ZERO_COUNTS = {
  new: 0, upgraded: 0, continued: 0, downgraded: 0, closed: 0,
  reopened: 0, needs_rejudgment: 0, mid_high_total: 0, changed_subject_count: 0,
};

// Mutations that touch rebuild-relevant fields must pass explicit counts so
// the fixture builder itself never throws before the validator runs.
function expectFail(label, mutate, counts) {
  let candidate;
  try {
    candidate = envelope(mutate([...HAPPY_ROWS]), counts ? { counts } : {});
  } catch {
    check(true, `${label} fails closed during fixture reconstruction`);
    return;
  }
  const result = safeValidateR7ContinuityEnvelope(candidate);
  check(result.ok === false, `${label} fails closed`);
}

expectFail("unknown change kind", (rows) => rows.map((r, i) => (i === 0 ? { ...r, change_kind: "escalated" } : r)), ZERO_COUNTS);
expectFail("mismatched change text", (rows) => rows.map((r, i) => (i === 0 ? { ...r, change_text: "新增了" } : r)));
expectFail("unknown object type", (rows) => rows.map((r, i) => (i === 0 ? { ...r, object_type: "signal" } : r)), ZERO_COUNTS);
expectFail("mismatched object type text", (rows) => rows.map((r, i) => (i === 0 ? { ...r, object_type_text: "信号" } : r)));
expectFail("unknown disposition", (rows) => rows.map((r, i) => (i === 0 ? { ...r, disposition: "pending_review" } : r)));
expectFail("mismatched disposition text", (rows) => rows.map((r, i) => (i === 0 ? { ...r, disposition_text: "待人工复核" } : r)));
expectFail("unknown data change kind", (rows) => rows.map((r, i) => (i === 0 ? { ...r, data_change_kind: "uncertain" } : r)));
expectFail("mismatched data change text", (rows) => rows.map((r, i) => (i === 0 ? { ...r, data_change_text: "数据存疑" } : r)));
expectFail("free-form attention text", (rows) => rows.map((r, i) => (i === 0 ? { ...r, attention_text: "请关注该受试者" } : r)));
expectFail("illegal severity wording", (rows) => rows.map((r, i) => (i === 0 ? { ...r, severity_after_text: "偏高" } : r)));
passed += 10;

const illegalBasis = envelope([queryRow(1)], {
  counts: {
    new: 0, upgraded: 0, continued: 0, downgraded: 0, closed: 0,
    reopened: 0, needs_rejudgment: 0, mid_high_total: 0, changed_subject_count: 0,
  },
  comparisonOverrides: { basis_text: "比较分析" },
});
check(safeValidateR7ContinuityEnvelope(illegalBasis).ok === false, "basis text outside the two-value closed set fails closed");
const illegalComparison = envelope([queryRow(1)], {
  counts: {
    new: 0, upgraded: 0, continued: 0, downgraded: 0, closed: 0,
    reopened: 0, needs_rejudgment: 0, mid_high_total: 0, changed_subject_count: 0,
  },
  comparisonOverrides: { comparison_text: "已与历史数据比较" },
});
check(safeValidateR7ContinuityEnvelope(illegalComparison).ok === false, "comparison text outside the closed set fails closed");
const pairedMismatch = envelope([queryRow(1)], {
  counts: {
    new: 0, upgraded: 0, continued: 0, downgraded: 0, closed: 0,
    reopened: 0, needs_rejudgment: 0, mid_high_total: 0, changed_subject_count: 0,
  },
  comparisonOverrides: { source_run_text: "" },
});
check(safeValidateR7ContinuityEnvelope(pairedMismatch).ok === false, "compared copy without a source run fails closed");
const pairedMismatch2 = envelope([queryRow(1)], {
  counts: {
    new: 0, upgraded: 0, continued: 0, downgraded: 0, closed: 0,
    reopened: 0, needs_rejudgment: 0, mid_high_total: 0, changed_subject_count: 0,
  },
  comparisonOverrides: {
    basis_text: "全量分析",
    comparison_text: R7_CONTINUITY_FIRST_ANALYSIS_TEXT,
    source_run_text: "2026-03-01 监查批次",
  },
});
check(safeValidateR7ContinuityEnvelope(pairedMismatch2).ok === false, "first-analysis copy with a source run fails closed");
passed += 4;

// --- severity shape rules (v0.2 §18) ---
expectFail("new risk carrying a prior severity", (rows) => rows.map((r, i) => (i === 0 ? { ...r, severity_before_text: "高" } : r)));
expectFail("closed risk carrying a current severity", (rows) => rows.map((r, i) => (i === 3 ? { ...r, severity_after_text: "中", data_change_kind: "unchanged", data_change_text: "无变化", attention_text: "" } : r)));
expectFail("upgrade without a higher rank", (rows) => rows.map((r, i) => (i === 1 ? { ...r, severity_before_text: "高", severity_after_text: "高" } : r)));
expectFail("downgrade with a rising direction", (rows) => rows.map((r, i) => (i === 4 ? { ...r, severity_before_text: "中", severity_after_text: "高" } : r)));
expectFail("continued with a changing rank", (rows) => rows.map((r, i) => (i === 5 ? { ...r, severity_before_text: "低", severity_after_text: "高" } : r)));
expectFail("directional change missing the prior severity", (rows) => rows.map((r, i) => (i === 1 ? { ...r, severity_before_text: "" } : r)));
expectFail("query draft carrying a risk severity", (rows) => rows.map((r, i) => (i === 7 ? { ...r, severity_after_text: "高" } : r)));
expectFail("monitoring output carrying a risk severity", (rows) => rows.map((r, i) => (i === 8 ? { ...r, severity_before_text: "低" } : r)));
expectFail("reopened risk missing the current severity", () => [
  riskRow(1, "reopened", "", "", "S/01", { attention_text: "等级变化待确认" }),
]);
passed += 9;

// --- missing-data attention coupling ---
expectFail("missing records without the required notice", (rows) => rows.map((r, i) => (i === 3 ? { ...r, attention_text: "" } : r)));
passed += 1;

// --- identity binding ---
const siteEnvelope = envelope([...HAPPY_ROWS], { siteRef: "site/01" });
check(normalizeR7ContinuityEnvelope(siteEnvelope, { siteRef: "site/01" }).identity.site_ref === "site/01", "requested center matches the identity site ref");
check(safeValidateR7ContinuityEnvelope(siteEnvelope, { siteRef: "site/02" }).ok === false, "center mismatch fails closed");
check(safeValidateR7ContinuityEnvelope(siteEnvelope, { siteRef: "" }).ok === false, "identity site ref without a request fails closed");
check(safeValidateR7ContinuityEnvelope(okEnvelope, { siteRef: "site/01" }).ok === false, "requested center without an identity site ref fails closed");
check(safeValidateR7ContinuityEnvelope(okEnvelope, { projectId: "project-b" }).code === "continuity_identity_mismatch", "project mismatch fails closed");
check(safeValidateR7ContinuityEnvelope(okEnvelope, { resultContextToken: "result-context:99" }).ok === false, "result-context mismatch fails closed");
const badTokenPrefix = envelope([...HAPPY_ROWS], { identityOverrides: {} });
check(
  safeValidateR7ContinuityEnvelope({ ...badTokenPrefix, result_context_token: "run:09" }).ok === false,
  "non result-context tokens fail closed",
);
passed += 7;

// --- counts, truncation, order ---
{
  const negative = envelope([...HAPPY_ROWS], {
    counts: { ...rebuildR7ContinuityChangeCounts(HAPPY_ROWS), new: -1 },
  });
  check(safeValidateR7ContinuityEnvelope(negative).ok === false, "negative counts fail closed");
  const fractional = envelope([...HAPPY_ROWS], {
    counts: { ...rebuildR7ContinuityChangeCounts(HAPPY_ROWS), upgraded: 1.5 },
  });
  check(safeValidateR7ContinuityEnvelope(fractional).ok === false, "non-integer counts fail closed");
  const missingKey = envelope([...HAPPY_ROWS], {
    counts: (({ reopened, ...rest }) => rest)(rebuildR7ContinuityChangeCounts(HAPPY_ROWS)),
  });
  check(safeValidateR7ContinuityEnvelope(missingKey).ok === false, "missing count keys fail closed");
  const extraKey = envelope([...HAPPY_ROWS], {
    counts: { ...rebuildR7ContinuityChangeCounts(HAPPY_ROWS), stale: 1 },
  });
  check(safeValidateR7ContinuityEnvelope(extraKey).ok === false, "extra count keys fail closed");
  const inflated = envelope([...HAPPY_ROWS], {
    counts: { ...rebuildR7ContinuityChangeCounts(HAPPY_ROWS), new: 2 },
  });
  check(safeValidateR7ContinuityEnvelope(inflated).ok === false, "counts that cannot be rebuilt from rows fail closed");
  const unavailable = envelope([...HAPPY_ROWS]);
  unavailable.comparison.available = false;
  check(safeValidateR7ContinuityEnvelope(unavailable).ok === false, "available=false never normalizes");
  passed += 6;
}

expectFail("order violation", (rows) => {
  const swapped = [...rows];
  [swapped[0], swapped[1]] = [swapped[1], swapped[0]];
  return swapped;
});
{
  const duplicatedRef = envelope([
    riskRow(1, "new", "", "高", "S/01"),
    riskRow(2, "new", "", "中", "S/02", { row_ref: "continuity-row-1" }),
  ], {
    counts: {
      new: 2, upgraded: 0, continued: 0, downgraded: 0, closed: 0,
      reopened: 0, needs_rejudgment: 0, mid_high_total: 2, changed_subject_count: 2,
    },
  });
  check(safeValidateR7ContinuityEnvelope(duplicatedRef).ok === false, "duplicate row refs fail closed");
  const duplicatedInstance = envelope([
    riskRow(1, "new", "", "高", "S/01"),
    riskRow(2, "upgraded", "中", "高", "S/02", { risk_instance_ref: "s7-risk-1", risk_ref: "s7-risk-1", risk_anchor_ref: "s7-anchor-1", event_ref: "s7-event-1" }),
  ], {
    counts: {
      new: 1, upgraded: 1, continued: 0, downgraded: 0, closed: 0,
      reopened: 0, needs_rejudgment: 0, mid_high_total: 1, changed_subject_count: 2,
    },
  });
  check(safeValidateR7ContinuityEnvelope(duplicatedInstance).ok === true, "shared risk_instance_ref dual-entry rows validate when counts match");
  passed += 3;
}

// truncation semantics
{
  const hidden = riskRow(300, "continued", "低", "低", "S/98", { title: "随访记录一致性" });
  const shown = [
    riskRow(200, "new", "", "高", "S/97", { title: "方案执行偏离" }),
    ...Array.from({ length: 199 }, (_, index) => riskRow(index + 1, "continued", "低", "低", `S/${index + 1}`, { title: `持续观察项 ${index + 1}` })),
  ];
  const fullCounts = rebuildR7ContinuityChangeCounts([...shown, hidden]);
  check(fullCounts.continued === 200, "truncation fixture rebuilds the hidden row into server counts");

  const truncatedOk = safeValidateR7ContinuityEnvelope(envelope(shown, {
    counts: fullCounts,
    shownCount: R7_CONTINUITY_ROW_LIMIT,
    totalCount: R7_CONTINUITY_ROW_LIMIT + 1,
    truncated: true,
  }));
  check(truncatedOk.ok === true, "truncated responses only require visible counts to be a subset of server counts");

  const truncatedMismatch = safeValidateR7ContinuityEnvelope(envelope(shown, {
    counts: fullCounts,
    shownCount: R7_CONTINUITY_ROW_LIMIT,
    totalCount: R7_CONTINUITY_ROW_LIMIT + 1,
    truncated: false,
  }));
  check(truncatedMismatch.ok === false, "untruncated responses must rebuild server counts exactly");

  const shownMismatch = safeValidateR7ContinuityEnvelope(envelope(shown, {
    counts: fullCounts,
    shownCount: R7_CONTINUITY_ROW_LIMIT - 1,
    totalCount: R7_CONTINUITY_ROW_LIMIT + 1,
    truncated: true,
  }));
  check(shownMismatch.ok === false, "shown_count must equal the visible row count");

  const truncatedFlagMismatch = safeValidateR7ContinuityEnvelope(envelope(shown, {
    counts: fullCounts,
    shownCount: R7_CONTINUITY_ROW_LIMIT,
    totalCount: R7_CONTINUITY_ROW_LIMIT,
    truncated: true,
  }));
  check(truncatedFlagMismatch.ok === false, "truncated must equal total_count > 200");

  const overLimit = safeValidateR7ContinuityEnvelope(envelope(
    [...shown, hidden],
    {
      shownCount: R7_CONTINUITY_ROW_LIMIT + 1,
      totalCount: R7_CONTINUITY_ROW_LIMIT + 1,
      truncated: false,
    },
  ));
  check(overLimit.ok === false, "responses beyond the 200-row limit fail closed");
  passed += 6;
}

// --- row-level invariants ---
expectFail("window start after window end", (rows) => rows.map((r, i) => (i === 0 ? { ...r, window_start: "2026-04-01" } : r)));
expectFail("non-ISO window date", (rows) => rows.map((r, i) => (i === 0 ? { ...r, window_start: "2026/01/01" } : r)));
expectFail("impossible calendar date", (rows) => rows.map((r, i) => (i === 0 ? { ...r, window_end: "2026-02-30" } : r)));
expectFail("blank title", (rows) => rows.map((r, i) => (i === 0 ? { ...r, title: "  " } : r)));
expectFail("blank site label", (rows) => rows.map((r, i) => (i === 0 ? { ...r, site_label: "" } : r)));
expectFail("negative ordinal", (rows) => rows.map((r, i) => (i === 0 ? { ...r, ordinal: -1 } : r)));
expectFail("fractional ordinal", (rows) => rows.map((r, i) => (i === 0 ? { ...r, ordinal: 1.5 } : r)));
expectFail("risk row without risk identity", (rows) => rows.map((r, i) => (i === 0 ? { ...r, risk_instance_ref: "" } : r)));
expectFail("query row without event ref", (rows) => rows.map((r, i) => (i === 7 ? { ...r, event_ref: "" } : r)));
expectFail("locator without count", (rows) => rows.map((r, i) => (i === 0 ? { ...r, source_count: 0 } : r)));
expectFail("count without locator", (rows) => rows.map((r, i) => (i === 6 ? { ...r, source_locator_ref: "s7-source-x" } : r)));
check(safeValidateR7ContinuityEnvelope(envelope([...HAPPY_ROWS], { digest: "deadbeef" })).ok === false, "short digests fail closed");
check(safeValidateR7ContinuityEnvelope(envelope([...HAPPY_ROWS], { digest: "ZZZZ" })).ok === false, "non-hex digests fail closed");
check(safeValidateR7ContinuityEnvelope(null).ok === false, "non-object payloads fail closed");
check(safeValidateR7ContinuityEnvelope([]).ok === false, "array payloads fail closed");
passed += 15;

// --- sort key ---
check(JSON.stringify(r7ContinuityRowSortKey(riskRow(1, "new", "", "高", "S/01"))) === JSON.stringify([0, 1, "continuity-row-1"]), "high-severity priority changes sort into group 0");
check(r7ContinuityRowSortKey(riskRow(2, "upgraded", "中", "高", "S/01"))[0] === 0, "high upgraded stays in group 0");
check(r7ContinuityRowSortKey(riskRow(3, "upgraded", "低", "中", "S/01"))[0] === 1, "mid-severity priority changes sort into group 1");
check(r7ContinuityRowSortKey(riskRow(4, "closed", "中", "", "S/01"))[0] === 2, "closed mid risks sort into group 2");
check(r7ContinuityRowSortKey(riskRow(5, "continued", "低", "低", "S/01"))[0] === 3, "low continued risks sort into group 3");
check(r7ContinuityRowSortKey(queryRow(6))[0] === 4, "query drafts sort into group 4");
check(r7ContinuityRowSortKey(outputRow(7))[0] === 5, "monitoring outputs sort into group 5");
check(r7ContinuityRowSortKey({ object_type: "unknown" })[0] === 6, "unknown objects sort into the fallback group");
passed += 8;

// --- digest verification ---
const digestTarget = envelope([...HAPPY_ROWS], { siteRef: "site/01" });
const digestExpected = { siteRef: "site/01" };
const computedDigest = await computeR7ContinuityResponseDigest(digestTarget, digestExpected);
check(computedDigest === serverDigest(digestTarget.identity, digestTarget.comparison), "frontend canonical digest matches the server content_digest format");
check(canonicalR7ContinuityPayload(digestTarget, digestExpected).includes('"change_counts"'), "canonical payload keeps wire-format keys");

const verified = await verifyR7ContinuityEnvelope(
  envelope([...HAPPY_ROWS], { siteRef: "site/01", digest: computedDigest }),
  { projectId: "project-a", resultContextToken: "result-context:01", siteRef: "site/01" },
);
check(verified.kind === "continuity" && verified.responseDigest === computedDigest, "honest responses pass digest verification");

const tampered = envelope([...HAPPY_ROWS], {
  siteRef: "site/01",
  digest: computedDigest,
  identityOverrides: { data_cutoff_text: "2026-04-30" },
});
const tamperedResult = await safeVerifyR7ContinuityEnvelope(tampered, { projectId: "project-a", resultContextToken: "result-context:01", siteRef: "site/01" });
check(tamperedResult.ok === false && tamperedResult.code === "continuity_response_digest_mismatch", "tampered identity fails digest verification closed");

const tamperedRow = envelope([...HAPPY_ROWS], { siteRef: "site/01", digest: computedDigest });
tamperedRow.comparison.rows[0] = { ...tamperedRow.comparison.rows[0], title: "被篡改的标题" };
const tamperedRowResult = await safeVerifyR7ContinuityEnvelope(tamperedRow, { projectId: "project-a", resultContextToken: "result-context:01", siteRef: "site/01" });
check(tamperedRowResult.ok === false && tamperedRowResult.code === "continuity_response_digest_mismatch", "tampered row content fails digest verification closed");

const wrongDigestEnvelope = envelope([...HAPPY_ROWS], { digest: "f".repeat(64) });
const wrongDigestResult = await safeVerifyR7ContinuityEnvelope(wrongDigestEnvelope);
check(wrongDigestResult.ok === false && wrongDigestResult.code === "continuity_response_digest_mismatch", "digest mismatch degrades to the unavailable result");
check(wrongDigestResult.text === R7_CONTINUITY_UNAVAILABLE_TEXT, "digest failures surface the contract unavailable text");
passed += 6;

// --- error projection ---
const unavailableError = projectR7ContinuityError({ detail: { code: "continuity_unavailable" } });
check(unavailableError.kind === "unavailable" && unavailableError.code === "continuity_unavailable", "continuity_unavailable maps to the unavailable kind");
check(unavailableError.text === R7_CONTINUITY_UNAVAILABLE_TEXT, "continuity errors surface the contract unavailable text");
check(projectR7ContinuityError(new Error("network down")).text === R7_CONTINUITY_UNAVAILABLE_TEXT, "transport errors surface the same unavailable text");
passed += 3;

console.log(`medicalMonitoringR7ContinuityProjection: ${passed} passed`);
