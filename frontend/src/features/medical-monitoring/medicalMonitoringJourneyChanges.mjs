// R7 Slice-08C-3 pure functions: continuity-to-Journey same-identity
// same-window filtering, event/risk binding, the seven-kind change display
// model, multi-change marker/current-row selection and the drawer
// route-close patch. No DOM, no React, no route mutation.
//
// Contract sources (frozen):
// - context/medical_monitoring_r7_slice08c3_journey_changes_drawer_contract_20260829.md
// - reviews/medical_monitoring_r7_slice08c_chinese_continuity_visual_contract_v0_2_20260829.md (v0.2 wins)
//
// Boundaries honored here:
// - Only rows from an already verified continuity envelope may enter the
//   Journey; failures never fabricate markers (§3.4).
// - The axis window is taken only from the projection actually used for
//   drawing (temporalSpine), falling back to the route window only when the
//   server result does not provide it (§3.2).
// - Event binding prefers the exact event_ref, then a same-identity
//   risk_anchor_ref carried by an existing event, then a current risk by
//   risk_instance_ref; unbound rows never create virtual date nodes (§3.5).
// - The seven Lucide icon names are the frozen closed set (§4.3); the icon
//   exports were verified present in lucide-react 1.23.0. Tones are the
//   semantic color keys worker_02 maps to CSS; the exact hues stay in 08C-4.
// - Closing the drawer clears only event_ref/risk_instance_ref/risk_anchor_ref
//   /visit_ref and preserves the journey identity and view (§5.1).

import {
  R7_CONTINUITY_CHANGE_KIND_TEXTS,
  R7_CONTINUITY_CHANGE_KINDS,
  R7_CONTINUITY_FIRST_ANALYSIS_TEXT,
} from "./medicalMonitoringContinuityProjection.mjs";
import { r7ContinuityRowSeverityLabel } from "./medicalMonitoringContinuityFilter.mjs";

// The drawer clears exactly these four route keys (§5.1); everything else in
// the route is preserved.
export const R7_JOURNEY_DRAWER_KEYS = Object.freeze([
  "event_ref",
  "risk_instance_ref",
  "risk_anchor_ref",
  "visit_ref",
]);

// Semantic color keys for the change markers (§4.3 "语义色"). Closed set so
// worker_02 can map each key to CSS without inventing new tones.
export const R7_JOURNEY_CHANGE_TONES = Object.freeze([
  "danger",
  "warning",
  "success",
  "info",
  "neutral",
]);

// Fixed drawer section order (§5.2). The drawer must render in exactly this
// sequence, with the contract fallback texts for missing values.
export const R7_JOURNEY_DRAWER_SECTION_ORDER = Object.freeze([
  "title",
  "event_category",
  "risk_level",
  "change",
  "date",
  "before_after",
  "related_records",
  "query_draft",
  "source",
]);

// Fixed missing-value texts (§5.2): shown verbatim, never token/schema/log.
export const R7_JOURNEY_DRAWER_FALLBACK_TEXTS = Object.freeze({
  eventCategory: "类别待确认",
  riskLevel: "风险等级待确认",
  change: "本轮变化待确认",
  date: "日期待确认",
  beforeAfter: "本轮未提供前后比较依据",
  relatedRecords: "本轮未提供关联记录",
  queryDraft: "本轮未提供 Query 草稿",
  source: "原始记录位置待确认",
});

// Journey truncation hint (§3.6): fixed prompt shown under the shared axis
// title; axis markers only ever represent the returned row set.
export const R7_JOURNEY_TRUNCATION_PREFIX = "本轮变化较多，当前仅显示服务端已返回的前";
export const R7_JOURNEY_TRUNCATION_SUFFIX = "条；请返回项目或中心概览查看完整范围说明。";

const R7_JOURNEY_CHANGE_ICONS = Object.freeze({
  new: "CirclePlus",
  upgraded: "CircleArrowUp",
  continued: "CircleDot",
  downgraded: "CircleArrowDown",
  closed: "CircleCheck",
  reopened: "RotateCcw",
  needs_rejudgment: "CircleHelp",
});

const R7_JOURNEY_CHANGE_TONES_BY_KIND = Object.freeze({
  new: "info",
  upgraded: "danger",
  continued: "neutral",
  downgraded: "success",
  closed: "success",
  reopened: "danger",
  needs_rejudgment: "warning",
});

// Three-channel display model (§4.3): Lucide icon name, frozen Chinese word
// and semantic tone key per change kind. Labels are reused from the
// projection module so the journey wording can never drift from the closed
// seven-kind set.
export const R7_JOURNEY_CHANGE_KIND_VISUAL = Object.freeze(
  Object.fromEntries(
    R7_CONTINUITY_CHANGE_KINDS.map((kind) => [
      kind,
      Object.freeze({
        icon: R7_JOURNEY_CHANGE_ICONS[kind],
        label: R7_CONTINUITY_CHANGE_KIND_TEXTS[kind],
        tone: R7_JOURNEY_CHANGE_TONES_BY_KIND[kind],
      }),
    ]),
  ),
);

function clean(value, fallback = "") {
  if (value === null || value === undefined) return fallback;
  return String(value).trim() || fallback;
}

function freeze(value) {
  if (Array.isArray(value)) {
    value.forEach((item) => freeze(item));
  } else if (value !== null && typeof value === "object") {
    Object.values(value).forEach((item) => freeze(item));
  }
  return Object.freeze(value);
}

// Severity wording (§4.4): re-exported from the 08C-2 filter so the Journey
// surface keeps a single source for "高/中/低", "前等级 → 后等级",
// "前等级（已关闭）" and the "等级变化待确认" fallback.
export { r7ContinuityRowSeverityLabel as r7JourneySeverityLabel };

// Axis window resolution (§3.2): the window actually used for drawing is
// projection.temporalSpine.windowStart/windowEnd; only when the server result
// does not provide that axis window does the route window take over.
export function r7JourneyAxisWindow(resultPayload, route = {}) {
  const temporal = resultPayload?.projection?.temporalSpine;
  const spineStart = clean(temporal?.windowStart ?? temporal?.window_start);
  const spineEnd = clean(temporal?.windowEnd ?? temporal?.window_end);
  if (spineStart && spineEnd) {
    return Object.freeze({ windowStart: spineStart, windowEnd: spineEnd });
  }
  const routeStart = clean(route.window_start);
  const routeEnd = clean(route.window_end);
  if (routeStart && routeEnd) {
    return Object.freeze({ windowStart: routeStart, windowEnd: routeEnd });
  }
  return null;
}

// Closed-interval containment gate (§3.2): only rows whose
// [window_start, window_end] lies fully inside the axis window belong to the
// current axis; equal boundaries are valid. Partial overlap, disjoint
// windows and rows missing either date never enter the axis.
export function r7JourneyWindowContains(row, window) {
  if (!row || typeof row !== "object" || !window) return false;
  const start = clean(row.window_start);
  const end = clean(row.window_end);
  const axisStart = clean(window?.windowStart);
  const axisEnd = clean(window?.windowEnd);
  if (!start || !end || !axisStart || !axisEnd) return false;
  return start >= axisStart && end <= axisEnd;
}

// Same-identity same-window filter (§3.2): risk rows only, with the exact
// same site_ref/subject_ref (trim-normalized) and closed-interval containment
// inside the axis window. Filters only; the server-authoritative order is
// preserved and no row is ever reordered.
export function filterR7ContinuityRowsForJourney(
  rows,
  { siteRef = "", subjectRef = "", windowStart = "", windowEnd = "" } = {},
) {
  const site = clean(siteRef);
  const subject = clean(subjectRef);
  const window = windowStart && windowEnd
    ? Object.freeze({ windowStart: clean(windowStart), windowEnd: clean(windowEnd) })
    : null;
  return freeze((Array.isArray(rows) ? rows : []).filter((row) => {
    if (!row || typeof row !== "object") return false;
    if (clean(row.object_type) !== "risk") return false;
    if (!site || !subject) return false;
    if (clean(row.site_ref) !== site || clean(row.subject_ref) !== subject) return false;
    return r7JourneyWindowContains(row, window);
  }));
}

// Combined reader for the subject views (§3.2): resolves the axis window,
// then selects the same-identity same-window rows from a verified continuity
// envelope. Failures, unverified envelopes and unavailable comparisons never
// fabricate markers; they yield an empty set so the Journey stays intact.
export function r7JourneyContinuityRows(envelope, resultPayload, route = {}) {
  const value = envelope?.ok ? envelope.value : null;
  if (!value || value.kind !== "continuity") return [];
  const axis = r7JourneyAxisWindow(resultPayload, route);
  if (!axis) return [];
  return filterR7ContinuityRowsForJourney(value.comparison.rows, {
    siteRef: route.site_ref,
    subjectRef: route.subject_ref,
    windowStart: axis.windowStart,
    windowEnd: axis.windowEnd,
  });
}

// Event/risk binding (§3.5): each journey row binds, in priority order, to
// (1) an event with the exact same event_ref, (2) an event that already
// carries the row's risk_anchor_ref, (3) a current risk with the same
// risk_instance_ref, or (4) stays unbound. Unbound rows never create virtual
// date nodes. Every output list preserves the server-authoritative order.
export function bindR7ContinuityRowsToJourney(rows, events = [], risks = []) {
  const eventByRef = new Map();
  for (const event of Array.isArray(events) ? events : []) {
    const eventRef = clean(event?.eventRef ?? event?.event_ref);
    if (eventRef) eventByRef.set(eventRef, event);
  }
  const anchorEventRefs = new Map();
  for (const [eventRef, event] of eventByRef.entries()) {
    const anchors = Array.isArray(event.riskAnchorRefs)
      ? event.riskAnchorRefs
      : Array.isArray(event.risk_anchor_refs)
        ? event.risk_anchor_refs
        : [];
    for (const anchor of anchors) {
      const anchorRef = clean(anchor);
      if (anchorRef && !anchorEventRefs.has(anchorRef)) {
        anchorEventRefs.set(anchorRef, eventRef);
      }
    }
  }
  const riskByInstance = new Map();
  for (const risk of Array.isArray(risks) ? risks : []) {
    const instanceRef = clean(risk?.riskInstanceRef ?? risk?.risk_instance_ref);
    if (instanceRef && !riskByInstance.has(instanceRef)) {
      riskByInstance.set(instanceRef, risk);
    }
  }

  const byEvent = new Map();
  const byRisk = new Map();
  const unbound = [];
  for (const row of Array.isArray(rows) ? rows : []) {
    if (!row || typeof row !== "object") continue;
    const eventRef = clean(row.event_ref);
    if (eventRef && eventByRef.has(eventRef)) {
      if (!byEvent.has(eventRef)) byEvent.set(eventRef, []);
      byEvent.get(eventRef).push(row);
      continue;
    }
    const anchorRef = clean(row.risk_anchor_ref);
    const anchoredEventRef = anchorEventRefs.get(anchorRef);
    if (anchorRef && anchoredEventRef) {
      if (!byEvent.has(anchoredEventRef)) byEvent.set(anchoredEventRef, []);
      byEvent.get(anchoredEventRef).push(row);
      continue;
    }
    const instanceRef = clean(row.risk_instance_ref);
    if (instanceRef && riskByInstance.has(instanceRef)) {
      if (!byRisk.has(instanceRef)) byRisk.set(instanceRef, []);
      byRisk.get(instanceRef).push(row);
      continue;
    }
    unbound.push(row);
  }

  return freeze({
    events: [...byEvent.entries()].map(([eventRef, boundRows]) => (
      Object.freeze({ eventRef, rows: freeze(boundRows) })
    )),
    risks: [...byRisk.entries()].map(([riskInstanceRef, boundRows]) => (
      Object.freeze({ riskInstanceRef, rows: freeze(boundRows) })
    )),
    unbound: freeze(unbound),
  });
}

// Event lookup on a binding result (§3.5/§4.5): rows bound to one event, in
// server order; an empty list when the event carries no change rows.
export function r7EventChangeRows(binding, eventRef) {
  const events = Array.isArray(binding?.events) ? binding.events : [];
  const found = events.find((item) => clean(item.eventRef) === clean(eventRef));
  return found ? found.rows : [];
}

// Risk lookup on a binding result (§3.5): rows bound to one current risk by
// risk_instance_ref; an empty list when the risk carries no change rows.
export function r7RiskChangeRows(binding, riskInstanceRef) {
  const risks = Array.isArray(binding?.risks) ? binding.risks : [];
  const found = risks.find((item) => clean(item.riskInstanceRef) === clean(riskInstanceRef));
  return found ? found.rows : [];
}

// Primary node marker (§4.5): among an event's bound rows, the row with the
// smallest server ordinal is the node's primary marker. The accessible count
// suffix states how many changes the node carries. Returns null when no
// bound row has a displayable change kind.
export function r7EventChangeMarker(rows) {
  const source = Array.isArray(rows) ? rows.filter((row) => row && typeof row === "object") : [];
  if (!source.length) return null;
  const withOrdinal = source.filter((row) => Number.isInteger(row.ordinal));
  const ordered = withOrdinal.length
    ? [...withOrdinal].sort((left, right) => left.ordinal - right.ordinal)
    : source;
  const primary = ordered[0];
  const visual = r7JourneyChangeKindVisual(primary.change_kind);
  if (!visual) return null;
  const total = source.length;
  return freeze({
    row: primary,
    changeKind: clean(primary.change_kind),
    changeText: visual.label,
    icon: visual.icon,
    tone: visual.tone,
    total,
    countSuffix: total > 1 ? `，共 ${total} 条变化` : "",
  });
}

// Visual model lookup (§4.3): returns the frozen three-channel entry or null
// for kinds outside the closed seven-kind set.
export function r7JourneyChangeKindVisual(changeKind) {
  const entry = R7_JOURNEY_CHANGE_KIND_VISUAL[clean(changeKind)];
  return entry || null;
}

// Drawer current-row selection (§5.2): the currently displayed row prefers
// the route risk_instance_ref; otherwise the first bound row in server
// order. The row list itself stays in server-authoritative order.
export function r7JourneyDrawerCurrentRow(rows, route = {}) {
  const source = Array.isArray(rows) ? rows.filter((row) => row && typeof row === "object") : [];
  if (!source.length) return null;
  const routeInstance = clean(route.risk_instance_ref);
  if (routeInstance) {
    const matched = source.find((row) => clean(row.risk_instance_ref) === routeInstance);
    if (matched) return matched;
  }
  return source[0];
}

// Drawer route-close patch (§5.1): clears exactly the four drawer selection
// keys and preserves the project, result context, center, subject, spine,
// axis window and the current journey/profile/timeline view. The input route
// object is never mutated.
export function r7JourneyDrawerClosePatch(route = {}) {
  if (!route || typeof route !== "object") return Object.freeze({});
  const next = { ...route };
  for (const key of R7_JOURNEY_DRAWER_KEYS) next[key] = "";
  return freeze(next);
}

// Journey truncation hint (§3.6): fixed prompt under the shared axis title
// when the comparison is truncated; axis markers never imply fullness.
export function r7JourneyTruncationText(comparison) {
  if (!comparison || comparison.truncated !== true) return "";
  const shown = Number.isInteger(comparison.shown_count) ? comparison.shown_count : 0;
  return `${R7_JOURNEY_TRUNCATION_PREFIX} ${shown} ${R7_JOURNEY_TRUNCATION_SUFFIX}`;
}

// Before/after basis model (§6): explicitly separates the prior level/state,
// the current level/state and the change reason. A first analysis (no
// baseline) shows the frozen 首次全面分析 text; missing detail shows the
// fixed 未提供前后比较依据 text.
export function r7JourneyBeforeAfterModel(comparison, row) {
  if (comparison && comparison.comparison_text === R7_CONTINUITY_FIRST_ANALYSIS_TEXT) {
    return Object.freeze({ state: "first_analysis", text: R7_CONTINUITY_FIRST_ANALYSIS_TEXT });
  }
  if (!row || typeof row !== "object" || row.object_type !== "risk") {
    return Object.freeze({ state: "none", text: R7_JOURNEY_DRAWER_FALLBACK_TEXTS.beforeAfter });
  }
  const parts = [];
  const before = clean(row.severity_before_text);
  const after = clean(row.severity_after_text);
  if (before) parts.push(`上轮 ${before}`);
  if (after) parts.push(`本轮 ${after}`);
  const reason = clean(row.reason_text);
  if (reason) parts.push(`变化原因：${reason}`);
  if (!parts.length) {
    return Object.freeze({ state: "none", text: R7_JOURNEY_DRAWER_FALLBACK_TEXTS.beforeAfter });
  }
  return Object.freeze({
    state: "detail",
    before,
    after,
    reason,
    text: parts.join("；"),
  });
}

// Query draft extraction (§6): the drawer takes the draft only from the
// currently selected R5 risk's evidenceSummary.query_draft; missing or empty
// values yield "" so the drawer shows the fixed fallback text. Continuity
// query_draft object rows are never cross-guessed.
export function r7JourneyQueryDraft(risk) {
  if (!risk || typeof risk !== "object") return "";
  return clean(risk.evidenceSummary?.query_draft ?? risk.evidence_summary?.query_draft);
}
