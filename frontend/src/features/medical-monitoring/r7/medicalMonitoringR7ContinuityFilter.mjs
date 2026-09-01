// R7 Slice-08C-2 continuity list filtering and same-identity routing helpers.
// Pure functions only: the component keeps filter state here as page-local
// state, filtering preserves the server-authoritative row order, and the
// Journey/source gates never fabricate identity from internal references.
// Contract sources:
// - context/medical_monitoring_r7_slice08c2_frontend_vertical_contract_20260829.md
// - reviews/medical_monitoring_r7_slice08c_chinese_continuity_visual_contract_v0_2_20260829.md (v0.2 wins)

import {
  R7_CONTINUITY_CHANGE_KIND_TEXTS,
  R7_CONTINUITY_CHANGE_KINDS,
  R7_CONTINUITY_OBJECT_TYPE_TEXTS,
  R7_CONTINUITY_OBJECT_TYPES,
  R7_CONTINUITY_ROW_LIMIT,
} from "./medicalMonitoringR7ContinuityProjection.mjs";

export const R7_CONTINUITY_SEVERITY_CONFIRM_TEXT = "等级变化待确认";

// Risk-level filter is a closed five-state set; the default view is
// "中高风险" (current severity 高/中). Non-risk rows never carry severity,
// so they only appear under "全部".
export const R7_CONTINUITY_SEVERITY_FILTERS = Object.freeze([
  { value: "mid_high", label: "中高风险" },
  { value: "all", label: "全部" },
  { value: "high", label: "高" },
  { value: "medium", label: "中" },
  { value: "low", label: "低" },
]);

// Change-kind filter is the frozen seven-kind closed set.
export const R7_CONTINUITY_CHANGE_FILTERS = Object.freeze([
  { value: "all", label: "全部变化" },
  ...R7_CONTINUITY_CHANGE_KINDS.map((value) => ({
    value,
    label: R7_CONTINUITY_CHANGE_KIND_TEXTS[value],
  })),
]);

// Object-category filter is the frozen three-type closed set.
export const R7_CONTINUITY_OBJECT_FILTERS = Object.freeze([
  { value: "all", label: "全部类别" },
  ...R7_CONTINUITY_OBJECT_TYPES.map((value) => ({
    value,
    label: R7_CONTINUITY_OBJECT_TYPE_TEXTS[value],
  })),
]);

export const R7_CONTINUITY_DEFAULT_FILTER = Object.freeze({
  severity: "mid_high",
  changeKind: "all",
  objectType: "all",
  needsRejudgmentOnly: false,
  subjectQuery: "",
});

export function createR7ContinuityFilterState() {
  return { ...R7_CONTINUITY_DEFAULT_FILTER };
}

function clean(value, fallback = "") {
  if (value === null || value === undefined) return fallback;
  return String(value).trim() || fallback;
}

function matchesSeverityFilter(row, severity) {
  const after = clean(row.severity_after_text);
  if (severity === "mid_high") return after === "高" || after === "中";
  if (severity === "high") return after === "高";
  if (severity === "medium") return after === "中";
  if (severity === "low") return after === "低";
  return true;
}

// Filters only; never reorders. Server order is authoritative and the
// projection validator guarantees it is already non-decreasing.
export function filterR7ContinuityRows(rows, filter = {}) {
  const source = filter && typeof filter === "object" ? filter : {};
  const severity = source.severity || "mid_high";
  const changeKind = source.changeKind || "all";
  const objectType = source.objectType || "all";
  const needsRejudgmentOnly = source.needsRejudgmentOnly === true;
  const subjectQuery = clean(source.subjectQuery).toLowerCase();
  return (Array.isArray(rows) ? rows : []).filter((row) => {
    if (!row || typeof row !== "object") return false;
    if (!matchesSeverityFilter(row, severity)) return false;
    if (changeKind !== "all" && row.change_kind !== changeKind) return false;
    if (objectType !== "all" && row.object_type !== objectType) return false;
    if (needsRejudgmentOnly && row.change_kind !== "needs_rejudgment") return false;
    if (subjectQuery) {
      const label = clean(row.subject_label).toLowerCase();
      const ref = clean(row.subject_ref).toLowerCase();
      if (!label.includes(subjectQuery) && !ref.includes(subjectQuery)) return false;
    }
    return true;
  });
}

// Per-change-kind severity display (v0.2 §18). The projection validator
// guarantees new/closed/reopened/directional shapes. The fallback remains a
// defensive display guard, but only needs_rejudgment may legitimately lack a
// current level after strict projection validation.
// Non-risk rows must never carry a level badge (contract §4).
export function r7ContinuityRowSeverityLabel(row) {
  if (!row || typeof row !== "object" || row.object_type !== "risk") return "";
  const kind = clean(row?.change_kind);
  const before = clean(row?.severity_before_text);
  const after = clean(row?.severity_after_text);
  if (kind === "new") return after || R7_CONTINUITY_SEVERITY_CONFIRM_TEXT;
  if (kind === "closed") return before ? `${before}（已关闭）` : R7_CONTINUITY_SEVERITY_CONFIRM_TEXT;
  if (kind === "upgraded" || kind === "downgraded" || kind === "continued") {
    return before && after ? `${before} → ${after}` : R7_CONTINUITY_SEVERITY_CONFIRM_TEXT;
  }
  if (kind === "reopened" || kind === "needs_rejudgment") {
    return after || R7_CONTINUITY_SEVERITY_CONFIRM_TEXT;
  }
  return "";
}

// Journey gate (frozen contract §2.4, v0.1 §7.2): a risk row may enter the
// Patient Journey only when the current R5 result projection confirms the
// same subject/site/spine and exposes a usable Journey window containing the
// risk row window. The narrower risk window remains the route window. Never
// fabricates subject/site Chinese names from internal references.
export function r7ContinuityRowJourneyTarget(row, resultPayload) {
  if (!row || typeof row !== "object") return null;
  if (row.object_type !== "risk") return null;
  const subjectRef = clean(row.subject_ref);
  const siteRef = clean(row.site_ref);
  const windowStart = clean(row.window_start);
  const windowEnd = clean(row.window_end);
  if (!subjectRef || !siteRef || !windowStart || !windowEnd) return null;

  const subjects = resultPayload?.projection?.subjects;
  if (!Array.isArray(subjects)) return null;
  const subject = subjects.find(
    (item) => clean(item?.subject_ref || item?.subject_id) === subjectRef,
  );
  if (!subject) return null;

  const subjectSite = clean(subject.site_ref || subject.site_id);
  if (!subjectSite || subjectSite !== siteRef) return null;

  const spineRef = clean(
    subject.spine_ref || subject.spineRef || subject.spine_id,
  );
  if (!spineRef) return null;

  const subjectFlow = resultPayload?.projection?.subjectFlow;
  if (!subjectFlow || subjectFlow.availability !== "available") return null;
  if (subjectFlow.reconciliation?.state !== "matched") return null;
  const flowRows = Array.isArray(subjectFlow.subjects)
    ? subjectFlow.subjects
    : Array.isArray(subjectFlow.rows)
      ? subjectFlow.rows
      : [];
  const flow = flowRows.find(
    (item) => clean(item?.subject_ref || item?.subjectRef || item?.subject_id) === subjectRef,
  );
  if (!flow) return null;
  const flowSite = clean(flow.site_ref || flow.siteRef || flow.site_id);
  const flowSpine = clean(flow.spine_ref || flow.spineRef || flow.spine_id);
  if (flowSite !== siteRef || flowSpine !== spineRef) return null;
  if (flow.journey_jump_enabled === false || flow.journeyJumpEnabled === false) return null;
  const flowStart = clean(
    flow.jump_window_start || flow.jumpWindowStart || flow.window_start || flow.windowStart,
  );
  const flowEnd = clean(
    flow.jump_window_end || flow.jumpWindowEnd || flow.window_end || flow.windowEnd,
  );
  if (!flowStart || !flowEnd) return null;
  if (windowStart < flowStart || windowEnd > flowEnd) return null;

  return {
    site_ref: siteRef,
    subject_ref: subjectRef,
    spine_ref: spineRef,
    window_start: windowStart,
    window_end: windowEnd,
    risk_instance_ref: clean(row.risk_instance_ref),
    risk_anchor_ref: clean(row.risk_anchor_ref),
    event_ref: clean(row.event_ref),
  };
}

// Source gate (frozen contract §2.5, v0.1 §4.5): enabled only when the row
// carries a usable risk_instance_ref + source_locator_ref pair; reuses the
// existing public source route. Empty-source rows stay disabled with the
// "原始记录位置待确认" hint and never perform an empty jump.
export function r7ContinuityRowSourceTarget(row) {
  if (!row || typeof row !== "object") return null;
  const riskInstanceRef = clean(row.risk_instance_ref);
  const sourceLocatorRef = clean(row.source_locator_ref);
  if (!riskInstanceRef || !sourceLocatorRef) return null;
  return { risk_instance_ref: riskInstanceRef, source_locator_ref: sourceLocatorRef };
}

// Truncation hint (v0.1 §6): explicit "共 N 条，当前显示前 M 条" wording.
export function r7ContinuityTruncationText(comparison) {
  if (!comparison || comparison.truncated !== true) return "";
  const total = Number.isInteger(comparison.total_count) ? comparison.total_count : 0;
  const shown = Number.isInteger(comparison.shown_count) ? comparison.shown_count : 0;
  return `变化较多，共 ${total} 条，当前显示前 ${shown} 条（服务端最多返回 ${R7_CONTINUITY_ROW_LIMIT} 条）。`;
}
