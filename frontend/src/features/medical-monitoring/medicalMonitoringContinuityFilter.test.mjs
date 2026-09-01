// R7 Slice-08C-2 pure-function tests: closed filter option sets, list
// filtering (server order preserved, default mid_high), severity label
// display, and the same-identity Journey/source gates (contract §2.4/§2.5,
// §4, §6.3). No DOM: these are the functions the panel binds to.
//
// Contract source:
// - context/medical_monitoring_r7_slice08c2_frontend_vertical_contract_20260829.md
// - reviews/medical_monitoring_r7_slice08c_chinese_continuity_visual_contract_v0_2_20260829.md (v0.2 wins)

import assert from "node:assert/strict";

import {
  R7_CONTINUITY_CHANGE_FILTERS,
  R7_CONTINUITY_DEFAULT_FILTER,
  R7_CONTINUITY_OBJECT_FILTERS,
  R7_CONTINUITY_SEVERITY_CONFIRM_TEXT,
  R7_CONTINUITY_SEVERITY_FILTERS,
  createR7ContinuityFilterState,
  filterR7ContinuityRows,
  r7ContinuityRowJourneyTarget,
  r7ContinuityRowSeverityLabel,
  r7ContinuityRowSourceTarget,
  r7ContinuityTruncationText,
} from "./medicalMonitoringContinuityFilter.mjs";
import {
  R7_CONTINUITY_CHANGE_KIND_TEXTS,
  R7_CONTINUITY_CHANGE_KINDS,
  R7_CONTINUITY_OBJECT_TYPE_TEXTS,
  R7_CONTINUITY_OBJECT_TYPES,
  R7_CONTINUITY_ROW_LIMIT,
} from "./medicalMonitoringContinuityProjection.mjs";

let passed = 0;
function check(condition, message) {
  assert.equal(Boolean(condition), true, message);
  passed += 1;
}

// --- minimal row builders (the full 28-field shape is the validator's
// contract, covered by the projection suite; these functions only read the
// fields they need) ---

function riskRow(overrides = {}) {
  return {
    object_type: "risk",
    change_kind: "new",
    severity_before_text: "",
    severity_after_text: "高",
    site_ref: "site/01",
    subject_ref: "S/01",
    subject_label: "受试者 001",
    window_start: "2026-01-01",
    window_end: "2026-03-31",
    risk_instance_ref: "risk-i-1",
    risk_anchor_ref: "risk-a-1",
    event_ref: "event-1",
    source_locator_ref: "source-1",
    ...overrides,
  };
}

function queryRow(overrides = {}) {
  return {
    object_type: "query_draft",
    change_kind: "new",
    severity_before_text: "",
    severity_after_text: "",
    site_ref: "site/01",
    subject_ref: "S/05",
    subject_label: "受试者 005",
    risk_instance_ref: "",
    risk_anchor_ref: "",
    event_ref: "event-q-5",
    source_locator_ref: "",
    ...overrides,
  };
}

function outputRow(overrides = {}) {
  return {
    object_type: "monitoring_output",
    change_kind: "continued",
    severity_before_text: "",
    severity_after_text: "",
    site_ref: "site/01",
    subject_ref: "S/06",
    subject_label: "受试者 006",
    risk_instance_ref: "",
    risk_anchor_ref: "",
    event_ref: "event-o-6",
    source_locator_ref: "source-o-6",
    ...overrides,
  };
}

// --- closed filter option sets (contract §4) ---
{
  check(
    JSON.stringify(R7_CONTINUITY_SEVERITY_FILTERS.map((option) => option.value))
      === JSON.stringify(["mid_high", "all", "high", "medium", "low"]),
    "severity filter is the closed five-state set",
  );
  check(R7_CONTINUITY_SEVERITY_FILTERS[0].label === "中高风险", "default severity option is 中高风险");
  check(R7_CONTINUITY_SEVERITY_FILTERS[1].label === "全部", "severity set exposes 全部");
  check(
    JSON.stringify(R7_CONTINUITY_CHANGE_FILTERS.map((option) => option.value))
      === JSON.stringify(["all", ...R7_CONTINUITY_CHANGE_KINDS]),
    "change filter is the frozen seven-kind closed set plus 全部变化",
  );
  check(R7_CONTINUITY_CHANGE_FILTERS[0].label === "全部变化", "change set exposes 全部变化");
  check(
    R7_CONTINUITY_CHANGE_FILTERS.every((option) => option.value === "all" || R7_CONTINUITY_CHANGE_KIND_TEXTS[option.value] === option.label),
    "change option labels are the frozen Chinese texts",
  );
  check(
    JSON.stringify(R7_CONTINUITY_OBJECT_FILTERS.map((option) => option.value))
      === JSON.stringify(["all", ...R7_CONTINUITY_OBJECT_TYPES]),
    "object filter is the closed three-type set plus 全部类别",
  );
  check(
    R7_CONTINUITY_OBJECT_FILTERS.every((option) => option.value === "all" || R7_CONTINUITY_OBJECT_TYPE_TEXTS[option.value] === option.label),
    "object option labels are the frozen Chinese texts",
  );
  check(
    JSON.stringify(createR7ContinuityFilterState()) === JSON.stringify(R7_CONTINUITY_DEFAULT_FILTER),
    "createR7ContinuityFilterState returns the frozen default",
  );
  passed += 8;
}

// --- filtering: default mid_high, closed sets, subject search, no reorder ---
{
  const ROWS = [
    riskRow({ change_kind: "new", severity_after_text: "高", subject_label: "受试者 001" }),
    riskRow({ change_kind: "upgraded", severity_before_text: "中", severity_after_text: "高", subject_ref: "S/02", subject_label: "受试者 002" }),
    riskRow({ change_kind: "needs_rejudgment", severity_after_text: "中", subject_ref: "S/03", subject_label: "受试者 003", source_locator_ref: "" }),
    riskRow({ change_kind: "closed", severity_before_text: "中", severity_after_text: "", subject_ref: "S/02", subject_label: "受试者 002", data_change_text: "本轮未见对应记录" }),
    riskRow({ change_kind: "continued", severity_before_text: "低", severity_after_text: "低", subject_ref: "S/02", subject_label: "受试者 002" }),
    queryRow({ subject_label: "受试者 005" }),
    outputRow({ subject_label: "受试者 006" }),
  ];

  const byRef = (rows) => rows.map((item) => item.row_ref ?? item.subject_ref);

  check(
    JSON.stringify(byRef(filterR7ContinuityRows(ROWS))) === JSON.stringify(byRef([ROWS[0], ROWS[1], ROWS[2]])),
    "default filter shows only current-severity 高/中 risk rows",
  );
  check(
    filterR7ContinuityRows(ROWS, {}).length === 3,
    "empty filter object falls back to the default mid_high view",
  );
  check(filterR7ContinuityRows(ROWS, { severity: "all" }).length === 7, "全部 severity reveals every row");
  check(filterR7ContinuityRows(ROWS, { severity: "high" }).length === 2, "高 filters to current 高 risk rows");
  check(filterR7ContinuityRows(ROWS, { severity: "medium" }).length === 1, "中 filters to current 中 risk rows");
  check(filterR7ContinuityRows(ROWS, { severity: "low" }).length === 1, "低 filters to current 低 risk rows");
  check(
    JSON.stringify(byRef(filterR7ContinuityRows(ROWS, { severity: "all", changeKind: "closed" }))) === JSON.stringify(byRef([ROWS[3]])),
    "change-kind filter uses the frozen kind values",
  );
  check(
    JSON.stringify(byRef(filterR7ContinuityRows(ROWS, { changeKind: "needs_rejudgment" }))) === JSON.stringify(byRef([ROWS[2]])),
    "needs_rejudgment filter works under the default severity",
  );
  check(
    filterR7ContinuityRows(ROWS, { severity: "all", changeKind: "continued" }).length === 2,
    "continued rows span risk and monitoring output under 全部",
  );
  check(
    JSON.stringify(byRef(filterR7ContinuityRows(ROWS, { severity: "all", objectType: "query_draft" }))) === JSON.stringify(byRef([ROWS[5]])),
    "object filter isolates Query 草稿",
  );
  check(
    JSON.stringify(byRef(filterR7ContinuityRows(ROWS, { severity: "all", objectType: "monitoring_output" }))) === JSON.stringify(byRef([ROWS[6]])),
    "object filter isolates 监查结果项",
  );
  check(
    JSON.stringify(byRef(filterR7ContinuityRows(ROWS, { needsRejudgmentOnly: true }))) === JSON.stringify(byRef([ROWS[2]])),
    "仅看需重新判断 isolates needs_rejudgment rows",
  );
  check(
    filterR7ContinuityRows(ROWS, { severity: "all", subjectQuery: "受试者 002" }).length === 3,
    "subject search matches the public subject label",
  );
  check(
    filterR7ContinuityRows(ROWS, { severity: "all", subjectQuery: "s/02" }).length === 3,
    "subject search matches subject_ref case-insensitively",
  );
  check(
    filterR7ContinuityRows(ROWS, { severity: "all", subjectQuery: "不存在" }).length === 0,
    "subject search with no match yields an empty list",
  );
  check(
    JSON.stringify(byRef(filterR7ContinuityRows(ROWS, { severity: "all" })))
      === JSON.stringify(byRef(ROWS)),
    "filtering never reorders the server-authoritative sequence",
  );
  check(filterR7ContinuityRows(null).length === 0, "null rows filter to an empty list");
  check(filterR7ContinuityRows("x").length === 0, "non-array rows filter to an empty list");
  check(
    filterR7ContinuityRows([null, "x", ROWS[0]], { severity: "all" }).length === 1,
    "malformed rows are dropped without throwing",
  );
  passed += 17;
}

// --- severity display labels (v0.2 §18; non-risk rows never carry a badge) ---
{
  check(r7ContinuityRowSeverityLabel(riskRow({ change_kind: "new", severity_after_text: "高" })) === "高", "new shows the current level");
  check(
    r7ContinuityRowSeverityLabel(riskRow({ change_kind: "new", severity_after_text: "" })) === R7_CONTINUITY_SEVERITY_CONFIRM_TEXT,
    "new without a level falls back to 等级变化待确认",
  );
  check(
    r7ContinuityRowSeverityLabel(riskRow({ change_kind: "closed", severity_before_text: "中", severity_after_text: "" })) === "中（已关闭）",
    "closed shows the prior level with a closed suffix",
  );
  check(
    r7ContinuityRowSeverityLabel(riskRow({ change_kind: "closed", severity_before_text: "", severity_after_text: "" })) === R7_CONTINUITY_SEVERITY_CONFIRM_TEXT,
    "closed without a prior level falls back",
  );
  check(
    r7ContinuityRowSeverityLabel(riskRow({ change_kind: "upgraded", severity_before_text: "中", severity_after_text: "高" })) === "中 → 高",
    "upgraded shows before → after",
  );
  check(
    r7ContinuityRowSeverityLabel(riskRow({ change_kind: "downgraded", severity_before_text: "高", severity_after_text: "中" })) === "高 → 中",
    "downgraded shows before → after",
  );
  check(
    r7ContinuityRowSeverityLabel(riskRow({ change_kind: "continued", severity_before_text: "低", severity_after_text: "低" })) === "低 → 低",
    "continued shows before → after",
  );
  check(
    r7ContinuityRowSeverityLabel(riskRow({ change_kind: "reopened", severity_after_text: "高" })) === "高",
    "reopened shows the current level",
  );
  check(
    r7ContinuityRowSeverityLabel(riskRow({ change_kind: "reopened", severity_after_text: "" })) === R7_CONTINUITY_SEVERITY_CONFIRM_TEXT,
    "reopened without a level falls back",
  );
  check(
    r7ContinuityRowSeverityLabel(riskRow({ change_kind: "needs_rejudgment", severity_after_text: "中" })) === "中",
    "needs_rejudgment shows the current level when present",
  );
  check(
    r7ContinuityRowSeverityLabel(riskRow({ change_kind: "needs_rejudgment", severity_after_text: "" })) === R7_CONTINUITY_SEVERITY_CONFIRM_TEXT,
    "needs_rejudgment without a level falls back",
  );
  check(r7ContinuityRowSeverityLabel(queryRow()) === "", "Query 草稿 never carries a severity badge");
  check(r7ContinuityRowSeverityLabel(outputRow()) === "", "监查结果项 never carries a severity badge");
  check(r7ContinuityRowSeverityLabel({ change_kind: "unknown", severity_after_text: "高" }) === "", "unknown change kinds render no badge");
  check(r7ContinuityRowSeverityLabel(null) === "", "null rows render no badge");
  passed += 15;
}

// --- Journey gate (contract §2.4): same subject/site/spine plus a containing
// R5 Journey window; the narrower risk window remains the route window ---
{
  const projection = {
    projection: {
      subjects: [
        { subject_ref: "S/01", site_ref: "site/01", spine_ref: "spine/01" },
        { subject_id: "S/02", site_id: "site/02", spine_id: "spine/02" },
        { subject_ref: "S/03", site_ref: "site/03", spineRef: "spine/03" },
      ],
      subjectFlow: {
        availability: "available",
        reconciliation: { state: "matched" },
        subjects: [
          { subject_ref: "S/01", site_ref: "site/01", spine_ref: "spine/01", journey_jump_enabled: true, jump_window_start: "2025-12-01", jump_window_end: "2026-04-30" },
          { subjectRef: "S/02", siteRef: "site/02", spineRef: "spine/02", journeyJumpEnabled: true, jumpWindowStart: "2025-12-01", jumpWindowEnd: "2026-04-30" },
          { subject_ref: "S/03", site_ref: "site/03", spine_ref: "spine/03", journey_jump_enabled: true, jump_window_start: "2025-12-01", jump_window_end: "2026-04-30" },
        ],
      },
    },
  };
  const targetRow = riskRow();

  check(r7ContinuityRowJourneyTarget(null, projection) === null, "null rows fail the journey gate closed");
  check(r7ContinuityRowJourneyTarget("x", projection) === null, "non-object rows fail the journey gate closed");
  check(r7ContinuityRowJourneyTarget(queryRow(), projection) === null, "non-risk rows never enter the Patient Journey");
  check(r7ContinuityRowJourneyTarget(outputRow(), projection) === null, "monitoring outputs never enter the Patient Journey");
  check(r7ContinuityRowJourneyTarget(riskRow({ subject_ref: "" }), projection) === null, "missing subject_ref fails closed");
  check(r7ContinuityRowJourneyTarget(riskRow({ site_ref: "" }), projection) === null, "missing site_ref fails closed");
  check(r7ContinuityRowJourneyTarget(riskRow({ window_start: "" }), projection) === null, "missing window_start fails closed");
  check(r7ContinuityRowJourneyTarget(riskRow({ window_end: "" }), projection) === null, "missing window_end fails closed");
  check(r7ContinuityRowJourneyTarget(targetRow, null) === null, "missing result payload fails closed");
  check(r7ContinuityRowJourneyTarget(targetRow, { projection: {} }) === null, "missing projection.subjects fails closed");
  check(r7ContinuityRowJourneyTarget(targetRow, { projection: { subjects: "x" } }) === null, "non-array subjects fail closed");
  check(
    r7ContinuityRowJourneyTarget(riskRow({ subject_ref: "S/99" }), projection) === null,
    "subjects absent from the current R5 projection fail closed",
  );
  check(
    r7ContinuityRowJourneyTarget(riskRow({ subject_ref: "S/01", site_ref: "site/99" }), projection) === null,
    "site mismatch between row and projection subject fails closed",
  );
  check(
    r7ContinuityRowJourneyTarget(riskRow({ subject_ref: "S/03", site_ref: "site/99" }), projection) === null,
    "site mismatch is checked for camelCase projection subjects too",
  );
  const projectionWithoutSpine = {
    projection: {
      subjects: [{ subject_ref: "S/01", site_ref: "site/01" }],
    },
  };
  check(
    r7ContinuityRowJourneyTarget(targetRow, projectionWithoutSpine) === null,
    "projection subject without a spine fails closed",
  );
  check(
    r7ContinuityRowJourneyTarget(targetRow, { projection: { subjects: projection.projection.subjects } }) === null,
    "missing R5 subject flow fails closed",
  );
  check(
    r7ContinuityRowJourneyTarget(targetRow, { projection: { ...projection.projection, subjectFlow: { ...projection.projection.subjectFlow, reconciliation: { state: "blocked" } } } }) === null,
    "unreconciled R5 subject flow fails closed",
  );
  check(
    r7ContinuityRowJourneyTarget(targetRow, { projection: { ...projection.projection, subjectFlow: { ...projection.projection.subjectFlow, subjects: [{ subject_ref: "S/01", site_ref: "site/01", spine_ref: "spine/99", jump_window_start: "2025-12-01", jump_window_end: "2026-04-30" }] } } }) === null,
    "flow spine mismatch fails closed",
  );
  check(
    r7ContinuityRowJourneyTarget(targetRow, { projection: { ...projection.projection, subjectFlow: { ...projection.projection.subjectFlow, subjects: [{ subject_ref: "S/01", site_ref: "site/01", spine_ref: "spine/01", jump_window_start: "2026-02-01", jump_window_end: "2026-04-30" }] } } }) === null,
    "risk window outside the R5 Journey window fails closed",
  );
  check(
    r7ContinuityRowJourneyTarget(targetRow, { projection: { ...projection.projection, subjectFlow: { ...projection.projection.subjectFlow, subjects: [{ subject_ref: "S/01", site_ref: "site/01", spine_ref: "spine/01", journey_jump_enabled: false, jump_window_start: "2025-12-01", jump_window_end: "2026-04-30" }] } } }) === null,
    "R5-disabled Journey rows stay closed",
  );
  const direct = r7ContinuityRowJourneyTarget(targetRow, projection);
  check(
    JSON.stringify(direct)
      === JSON.stringify({
        site_ref: "site/01",
        subject_ref: "S/01",
        spine_ref: "spine/01",
        window_start: "2026-01-01",
        window_end: "2026-03-31",
        risk_instance_ref: "risk-i-1",
        risk_anchor_ref: "risk-a-1",
        event_ref: "event-1",
      }),
    "journey target uses the projection-bound spine and the contained risk window",
  );
  check(direct.risk_instance_ref === "risk-i-1", "journey target forwards the risk instance ref");
  const idVariant = r7ContinuityRowJourneyTarget(
    riskRow({ subject_ref: "S/02", site_ref: "site/02" }),
    projection,
  );
  check(
    idVariant && idVariant.spine_ref === "spine/02" && idVariant.subject_ref === "S/02",
    "journey target accepts subject_id/site_id/spine_id projection variants",
  );
  const camelVariant = r7ContinuityRowJourneyTarget(
    riskRow({ subject_ref: "S/03", site_ref: "site/03" }),
    projection,
  );
  check(camelVariant && camelVariant.spine_ref === "spine/03", "journey target accepts the camelCase spineRef variant");
  const emptyOptional = r7ContinuityRowJourneyTarget(
    riskRow({ risk_instance_ref: "", risk_anchor_ref: "", event_ref: "" }),
    projection,
  );
  check(
    emptyOptional && emptyOptional.risk_instance_ref === "" && emptyOptional.risk_anchor_ref === "" && emptyOptional.event_ref === "",
    "optional refs degrade to empty strings instead of fabricated values",
  );
  passed += 23;
}

// --- Source gate (contract §2.5): usable risk_instance_ref + source_locator_ref
// pair only; empty sources stay closed ---
{
  check(
    JSON.stringify(r7ContinuityRowSourceTarget(riskRow()))
      === JSON.stringify({ risk_instance_ref: "risk-i-1", source_locator_ref: "source-1" }),
    "source target enables on the usable pair",
  );
  check(r7ContinuityRowSourceTarget(riskRow({ source_locator_ref: "" })) === null, "missing source_locator_ref stays disabled");
  check(r7ContinuityRowSourceTarget(riskRow({ risk_instance_ref: "" })) === null, "missing risk_instance_ref stays disabled");
  check(r7ContinuityRowSourceTarget(riskRow({ source_locator_ref: "  " })) === null, "whitespace-only locator stays disabled");
  check(r7ContinuityRowSourceTarget(riskRow({ risk_instance_ref: "  " })) === null, "whitespace-only instance stays disabled");
  check(r7ContinuityRowSourceTarget(queryRow()) === null, "Query 草稿 rows without the pair stay disabled");
  check(r7ContinuityRowSourceTarget(null) === null, "null rows stay disabled");
  passed += 7;
}

// --- truncation hint (v0.1 §6) ---
{
  const truncationText = `变化较多，共 201 条，当前显示前 200 条（服务端最多返回 ${R7_CONTINUITY_ROW_LIMIT} 条）。`;
  check(
    r7ContinuityTruncationText({ truncated: true, total_count: 201, shown_count: 200 }) === truncationText,
    "truncated comparisons render the frozen 共 N/前 M wording",
  );
  check(r7ContinuityTruncationText({ truncated: false, total_count: 201, shown_count: 200 }) === "", "untruncated comparisons render no hint");
  check(r7ContinuityTruncationText(null) === "", "missing comparisons render no hint");
  check(
    r7ContinuityTruncationText({ truncated: true, total_count: 1.5, shown_count: "x" }) === `变化较多，共 0 条，当前显示前 0 条（服务端最多返回 ${R7_CONTINUITY_ROW_LIMIT} 条）。`,
    "malformed counts degrade to zero instead of leaking raw values",
  );
  passed += 4;
}

console.log(`medicalMonitoringContinuityFilter: ${passed} passed`);
