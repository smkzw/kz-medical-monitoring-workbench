// Patient Journey change markers and right-side detail drawer. The marker and
// drawer render only when a result context is present.
//
// Boundaries honored here:
// - The drawer and markers never fabricate data: sections come from the
//   current event/risk facts and a verified continuity row only (§6).
// - The overlay/push decision is a shared threshold constant used by the
//   offline tests and later 08C-4 real-browser verification (§5.3).
// - Overlay traps focus and locks body scroll; push stays non-modal and
//   allows direct switching (§5.3). Escape/close restore focus to the trigger
//   element or the shared axis title (§5.1).
// - The fixed section order and the fixed missing-value texts come from
//   worker_01's frozen model (MONITORING_JOURNEY_DRAWER_SECTION_ORDER /
//   MONITORING_JOURNEY_DRAWER_FALLBACK_TEXTS), never from this file.

import { useCallback, useEffect, useLayoutEffect, useRef } from "react";
import {
  CirclePlus,
  CircleArrowUp,
  CircleDot,
  CircleArrowDown,
  CircleCheck,
  RotateCcw,
  CircleHelp,
} from "lucide-react";
import { MONITORING_JOURNEY_DRAWER_SECTION_ORDER } from "./medicalMonitoringJourneyChanges.mjs";
import {
  MONITORING_JOURNEY_AXIS_TITLE_ID,
  MONITORING_JOURNEY_DRAWER_FOCUSABLE_SELECTOR,
  MONITORING_JOURNEY_DRAWER_LIVE_ID,
  MONITORING_JOURNEY_DRAWER_TITLE_ID,
  monitoringJourneyDrawerKeyAction,
  monitoringJourneyFocusStep,
  monitoringJourneyRestoreTarget,
  monitoringJourneyDrawerSections,
} from "./medicalMonitoringJourneyDrawerModel.mjs";
import "./medicalMonitoringJourneyDrawer.css";

// Re-exported so the workspace and offline tests share one import surface.
export {
  MONITORING_JOURNEY_AXIS_TITLE_ID,
  MONITORING_JOURNEY_CONTENT_MIN_WIDTH,
  MONITORING_JOURNEY_DRAWER_FOCUSABLE_SELECTOR,
  MONITORING_JOURNEY_DRAWER_GAP,
  MONITORING_JOURNEY_DRAWER_LIVE_ID,
  MONITORING_JOURNEY_DRAWER_TITLE_ID,
  MONITORING_JOURNEY_DRAWER_WIDTH,
  MONITORING_JOURNEY_DEFAULT_DOMAIN_LABELS,
  MONITORING_JOURNEY_OVERLAY_DRAWER_MAX_WIDTH,
  MONITORING_JOURNEY_VIEWPORT_PUSH_MIN,
  monitoringJourneyDrawerKeyAction,
  monitoringJourneyDrawerLayoutMode,
  monitoringJourneyDrawerSections,
  monitoringJourneyFocusStep,
  monitoringJourneyRestoreTarget,
} from "./medicalMonitoringJourneyDrawerModel.mjs";

// The frozen seven-kind Lucide icon set (§4.3). Verified present in
// lucide-react 1.23.0; only this closed mapping may feed the marker render.
const MONITORING_JOURNEY_MARKER_ICONS = Object.freeze({
  CirclePlus,
  CircleArrowUp,
  CircleDot,
  CircleArrowDown,
  CircleCheck,
  RotateCcw,
  CircleHelp,
});

/**
 * Compact three-channel change marker (§4.3): Lucide icon + frozen Chinese
 * change word + semantic tone class. aria-hidden: the parent button's
 * accessible name carries the change wording and the total count (§4.5).
 */
export function MonitoringJourneyChangeMarker({ marker, className = "" }) {
  if (!marker || typeof marker !== "object") return null;
  const Icon = MONITORING_JOURNEY_MARKER_ICONS[marker.icon] || CircleHelp;
  return (
    <span
      className={`monitoring-journey-marker monitoring-journey-tone-${marker.tone || "neutral"}${className ? ` ${className}` : ""}`}
      data-change-kind={marker.changeKind}
      data-change-marker="true"
      aria-hidden="true"
    >
      <Icon size={10} strokeWidth={2.25} aria-hidden="true" />
      <span>{marker.changeText}</span>
    </span>
  );
}

const DRAWER_SECTION_LABELS = Object.freeze({
  event_category: "事件类别",
  risk_level: "风险等级",
  change: "本轮变化",
  date: "日期",
  before_after: "前后依据",
  related_records: "关联记录",
  query_draft: "Query 草稿",
});

// Maps the frozen wire section keys to the camelCase fields the section
// model produces, so the drawer renders exactly the §5.2 order.
const DRAWER_SECTION_FIELDS = Object.freeze({
  title: "title",
  event_category: "eventCategory",
  risk_level: "riskLevel",
  change: "change",
  date: "date",
  before_after: "beforeAfter",
  related_records: "relatedRecords",
  query_draft: "queryDraft",
  source: "sourceText",
});

function JourneyDrawerSections({ sections, changeRows = [], currentRowIndex = -1, onSelectRow }) {
  return (
    <dl className="monitoring-journey-sections" data-journey-sections>
      {MONITORING_JOURNEY_DRAWER_SECTION_ORDER.filter((key) => key !== "title" && key !== "source").map((key) => (
        <div data-drawer-section={key} key={key}>
          <dt>{DRAWER_SECTION_LABELS[key]}</dt>
          <dd>{sections[DRAWER_SECTION_FIELDS[key]]}</dd>
          {key === "change" && changeRows.length > 1 ? (
            <div className="monitoring-journey-change-switcher" role="group" aria-label="本轮变化切换">
              {changeRows.map((row, index) => (
                <button
                  type="button"
                  key={row.row_ref || index}
                  data-change-row={String(index)}
                  className={index === currentRowIndex ? "is-active" : ""}
                  aria-pressed={index === currentRowIndex}
                  onClick={() => onSelectRow?.(row)}
                >
                  <span>{`${index + 1}/${changeRows.length}`}</span>
                  <span>{row.change_text}</span>
                </button>
              ))}
            </div>
          ) : null}
        </div>
      ))}
    </dl>
  );
}

/**
 * Detail drawer. `mode` comes from the shared threshold function;
 * the parent supplies the section model, the server-ordered change rows and
 * the close/switch/source callbacks.
 */
export function MedicalMonitoringJourneyDrawer({
  mode = "overlay",
  sections = null,
  changeRows = [],
  currentRowIndex = -1,
  onSelectRow,
  onClose,
  onSource,
  closeLabel = "关闭详情",
  titleId = MONITORING_JOURNEY_DRAWER_TITLE_ID,
  liveId = MONITORING_JOURNEY_DRAWER_LIVE_ID,
}) {
  const containerRef = useRef(null);
  const closeRef = useRef(null);
  const triggerRef = useRef(null);

  // Capture the triggering element on open (click/keyboard activation keeps
  // focus on the button; deep links fall back to the axis title).
  useLayoutEffect(() => {
    if (typeof document === "undefined") return;
    if (document.activeElement && document.activeElement !== document.body) {
      triggerRef.current = document.activeElement;
    }
  }, []);

  // Overlay body vertical scroll lock (§5.3); restored on unmount.
  useEffect(() => {
    if (mode !== "overlay" || typeof document === "undefined") return undefined;
    const previous = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    return () => {
      document.body.style.overflow = previous;
    };
  }, [mode]);

  // Overlay initial focus on the visible close button (§5.3).
  useEffect(() => {
    if (mode !== "overlay" || typeof document === "undefined") return undefined;
    const frame = window.requestAnimationFrame(() => {
      closeRef.current?.focus?.();
    });
    return () => window.cancelAnimationFrame(frame);
  }, [mode]);

  // Push: keep the drawer chrome in the viewport without jumping the page (§5.3).
  useLayoutEffect(() => {
    if (mode !== "push" || typeof document === "undefined") return undefined;
    const frame = window.requestAnimationFrame(() => {
      containerRef.current?.scrollIntoView?.({ block: "nearest", inline: "nearest" });
    });
    return () => window.cancelAnimationFrame(frame);
  }, [mode, sections?.title]);

  const handleClose = useCallback(() => {
    const trigger = triggerRef.current;
    const triggerConnected = Boolean(trigger && typeof trigger.isConnected === "boolean" && trigger.isConnected);
    onClose?.();
    if (typeof window === "undefined" || typeof document === "undefined") return;
    window.requestAnimationFrame(() => {
      const axisTitle = document.getElementById(MONITORING_JOURNEY_AXIS_TITLE_ID);
      const target = monitoringJourneyRestoreTarget({
        triggerConnected,
        axisTitleExists: Boolean(axisTitle),
      });
      if (target === "trigger") trigger.focus?.();
      else if (target === "axis_title") axisTitle?.focus?.();
    });
  }, [onClose]);

  // Escape closes in both modes (§5.3).
  useEffect(() => {
    if (typeof document === "undefined") return undefined;
    const handleKey = (event) => {
      if (monitoringJourneyDrawerKeyAction({ key: event.key, shiftKey: event.shiftKey, mode }) === "close") {
        event.preventDefault();
        handleClose();
      }
    };
    document.addEventListener("keydown", handleKey);
    return () => document.removeEventListener("keydown", handleKey);
  }, [handleClose, mode]);

  const handleContainerKeyDown = (event) => {
    if (mode !== "overlay" || event.key !== "Tab") return;
    const focusables = Array.from(containerRef.current?.querySelectorAll(MONITORING_JOURNEY_DRAWER_FOCUSABLE_SELECTOR) || [])
      .filter((element) => !element.hasAttribute("disabled"));
    if (!focusables.length) {
      event.preventDefault();
      return;
    }
    const current = typeof document !== "undefined" ? focusables.indexOf(document.activeElement) : -1;
    const next = monitoringJourneyFocusStep(focusables.length, current, { forward: !event.shiftKey });
    event.preventDefault();
    focusables[next]?.focus?.();
  };

  const isOverlay = mode === "overlay";
  const sectionKeys = MONITORING_JOURNEY_DRAWER_SECTION_ORDER.filter((key) => key !== "title" && key !== "source");
  const liveText = sections
    ? `${sections.title} · ${sections.riskLevel} · ${sections.change}`
    : "";
  const drawer = (
    <aside
      ref={containerRef}
      className={isOverlay ? "monitoring-journey-drawer" : "monitoring-journey-drawer monitoring-journey-drawer-push"}
      data-journey-drawer="true"
      data-journey-drawer-mode={mode}
      aria-labelledby={titleId}
      {...(isOverlay ? { role: "dialog", "aria-modal": "true" } : {})}
      onKeyDown={handleContainerKeyDown}
    >
      <header className="monitoring-journey-drawer-head">
        <div>
          <span className="monitoring-eyebrow">风险定位</span>
          <h2 id={titleId}>{sections?.title || "本轮变化详情"}</h2>
        </div>
        <button type="button" className="monitoring-icon-button" data-journey-close="true" aria-label={closeLabel} ref={closeRef} onClick={handleClose}>关闭</button>
      </header>
      {sections ? (
        <>
          <div className="monitoring-journey-drawer-body">
            {sectionKeys.length ? (
              <JourneyDrawerSections
                sections={sections}
                changeRows={changeRows}
                currentRowIndex={currentRowIndex}
                onSelectRow={onSelectRow}
              />
            ) : null}
            {liveText ? (
              <p className="monitoring-journey-live" id={liveId} data-journey-live aria-live="polite">{liveText}</p>
            ) : null}
          </div>
          <div className="monitoring-journey-source" data-drawer-section="source">
            <button
              type="button"
              className="monitoring-source-button"
              data-journey-source="true"
              disabled={!sections.sourceEnabled}
              onClick={onSource}
            >
              {sections.sourceText}
            </button>
          </div>
        </>
      ) : null}
    </aside>
  );

  if (isOverlay) {
    return (
      <div className="monitoring-journey-overlay" data-journey-overlay="true" role="presentation">
        <div className="monitoring-journey-backdrop" data-journey-backdrop="true" aria-hidden="true" onClick={handleClose} />
        {drawer}
      </div>
    );
  }
  return drawer;
}

export default MedicalMonitoringJourneyDrawer;
