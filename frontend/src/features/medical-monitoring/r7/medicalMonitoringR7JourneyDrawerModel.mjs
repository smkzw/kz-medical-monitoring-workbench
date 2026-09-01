// R7 Slice-08C-3 pure drawer model: shared overlay/push thresholds, focus
// trap step, keyboard decision, focus-restore decision and the fixed drawer
// section model. No DOM, no React, no JSX. The drawer component and the
// offline interaction tests both bind to this module so 08C-4 real-browser
// checks reuse the exact same constants and rules.
//
// Contract sources (frozen):
// - context/medical_monitoring_r7_slice08c3_journey_changes_drawer_contract_20260829.md
// - reviews/medical_monitoring_r7_slice08c_chinese_continuity_visual_contract_v0_2_20260829.md (v0.2 wins)

import {
  R7_JOURNEY_DRAWER_FALLBACK_TEXTS,
  r7JourneyBeforeAfterModel,
  r7JourneyQueryDraft,
  r7JourneySeverityLabel,
} from "./medicalMonitoringR7JourneyChanges.mjs";

// Shared overlay/push thresholds (§5.3): viewport <1440px is always overlay;
// at >=1440px the drawer may push only when the host content keeps a readable
// main column (host width minus the 420px drawer and 16px gap still >=760px).
export const R7_JOURNEY_VIEWPORT_PUSH_MIN = 1440;
export const R7_JOURNEY_DRAWER_WIDTH = 420;
export const R7_JOURNEY_DRAWER_GAP = 16;
export const R7_JOURNEY_CONTENT_MIN_WIDTH = 760;
export const R7_JOURNEY_OVERLAY_DRAWER_MAX_WIDTH = 480;

// Stable accessible ids shared by the overlay dialog and the push aside.
export const R7_JOURNEY_DRAWER_TITLE_ID = "r7-journey-drawer-title";
export const R7_JOURNEY_DRAWER_LIVE_ID = "r7-journey-drawer-live";

// Focus-restore fallback target (§5.1): the shared horizontal timeline title.
export const R7_JOURNEY_AXIS_TITLE_ID = "r5-journey-axis-title";

// Focusable controls inside the drawer; the overlay focus trap cycles through
// exactly these. Close button + change switcher + source entry.
export const R7_JOURNEY_DRAWER_FOCUSABLE_SELECTOR = [
  "button[data-journey-close]",
  "button[data-change-row]",
  "button[data-journey-source]",
].join(",");

function clean(value, fallback = "") {
  if (value === null || value === undefined) return fallback;
  return String(value).trim() || fallback;
}

// Default domain labels mirror the R5 page labels; the R5 page passes its own
// DOMAIN_LABELS so the journey category wording never drifts.
export const R7_JOURNEY_DEFAULT_DOMAIN_LABELS = Object.freeze({
  ae: "AE",
  mh: "MH",
  cm: "合并用药",
  ip: "试验用药",
  lab_exam: "检验检查",
  hospital_procedure: "诊疗操作",
  symptom_efficacy: "疗效/症状",
  protocol_compliance: "方案执行",
});

/**
 * Overlay/push decision (§5.3). Pure and shared: offline tests and the 08C-4
 * real-browser check both bind to the same constants.
 * @param {{ viewportWidth?: number, hostContentWidth?: number }} size
 * @returns {"overlay" | "push"}
 */
export function r7JourneyDrawerLayoutMode({ viewportWidth, hostContentWidth }) {
  const viewport = Number(viewportWidth);
  const host = Number(hostContentWidth);
  if (!Number.isFinite(viewport) || !Number.isFinite(host)) return "overlay";
  if (viewport < R7_JOURNEY_VIEWPORT_PUSH_MIN) return "overlay";
  return host - R7_JOURNEY_DRAWER_WIDTH - R7_JOURNEY_DRAWER_GAP >= R7_JOURNEY_CONTENT_MIN_WIDTH
    ? "push"
    : "overlay";
}

/**
 * Focus trap step (§5.3 overlay): next index with wrap. Returns -1 when there
 * is nothing to focus.
 */
export function r7JourneyFocusStep(count, currentIndex, { forward = true } = {}) {
  if (!Number.isInteger(count) || count <= 0) return -1;
  const index = Number.isInteger(currentIndex) && currentIndex >= 0 ? currentIndex : -1;
  if (index < 0) return forward ? 0 : count - 1;
  return (index + (forward ? 1 : -1) + count) % count;
}

/**
 * Keyboard decision model (§5.3): Escape closes in both modes; Tab is trapped
 * in overlay only, push lets the browser tab order pass through natively.
 */
export function r7JourneyDrawerKeyAction({ key = "", shiftKey = false, mode = "overlay" }) {
  if (key === "Escape") return "close";
  if (mode === "overlay" && key === "Tab") return shiftKey ? "prev_focus" : "next_focus";
  return null;
}

/**
 * Focus-restore decision (§5.1): the close action returns focus to the
 * triggering element when it still exists; otherwise to the shared axis title;
 * otherwise no restore target exists.
 */
export function r7JourneyRestoreTarget({ triggerConnected = false, axisTitleExists = false }) {
  if (triggerConnected) return "trigger";
  if (axisTitleExists) return "axis_title";
  return null;
}

/**
 * Drawer section model (§5.2/§6): fixed order with the frozen fallback texts.
 * The current event keeps providing category/date/visit and the source count;
 * the current continuity row drives the risk level, this-round change,
 * before/after basis, related records, Query draft and source entry.
 */
export function r7JourneyDrawerSections({
  event = null,
  risk = null,
  currentRow = null,
  comparison = null,
  domainLabels = R7_JOURNEY_DEFAULT_DOMAIN_LABELS,
  fallback = R7_JOURNEY_DRAWER_FALLBACK_TEXTS,
} = {}) {
  const labels = domainLabels && typeof domainLabels === "object" ? domainLabels : R7_JOURNEY_DEFAULT_DOMAIN_LABELS;
  const row = currentRow && typeof currentRow === "object" ? currentRow : null;
  const riskInstance = clean(row?.risk_instance_ref) || clean(risk?.riskInstanceRef || risk?.risk_instance_ref);
  const sourceLocator = clean(row?.source_locator_ref) || clean(risk?.sourceLocatorRef || risk?.source_locator_ref);
  const sourceEnabled = Boolean(riskInstance && sourceLocator);
  const beforeAfter = r7JourneyBeforeAfterModel(comparison, row);
  const category = event
    ? clean(labels[event.domain] || event.domainEncoding?.shortLabel || "")
    : risk?.domainEncoding?.shortLabel
      ? clean(risk.domainEncoding.shortLabel)
      : "";
  const eventDate = event
    ? event.dateState === "exact" ? clean(event.start) : clean(event.dateLabel)
    : "";
  const visitLabel = clean(event?.visitLabel || event?.visit_label);
  const date = [eventDate || clean(risk?.dateLabel) || clean(row?.date_label), visitLabel].filter(Boolean).join(" · ");
  const recordCount = Number.isInteger(row?.source_count)
    ? row.source_count
    : event && Array.isArray(event.sourceLocatorRefs)
      ? event.sourceLocatorRefs.length
      : 0;
  return Object.freeze({
    title: clean(event?.eventLabel) || clean(risk?.riskType) || clean(row?.title) || "本轮变化详情",
    eventCategory: category || fallback.eventCategory,
    riskLevel: r7JourneySeverityLabel(row) || clean(risk?.severityLabel) || fallback.riskLevel,
    change: clean(row?.change_text) || fallback.change,
    date: date || fallback.date,
    beforeAfter: beforeAfter.text || fallback.beforeAfter,
    relatedRecords: recordCount > 0 ? `关联原始记录 ${recordCount} 条` : fallback.relatedRecords,
    queryDraft: r7JourneyQueryDraft(risk) || fallback.queryDraft,
    sourceText: sourceEnabled ? "查看来源证据" : fallback.source,
    sourceEnabled,
  });
}
