import { useEffect, useRef, useState, useSyncExternalStore } from "react";
import {
  MONITORING_PANEL_TEXT,
  createMonitoringProgressPanelStore,
} from "./medicalMonitoringProgressPanelController.mjs";
import "./medicalMonitoringProgressPanel.css";

const IDLE_PANEL = Object.freeze({
  view: null,
  empty: null,
  notice: null,
  actionsHidden: false,
  pendingAction: null,
  confirmStop: false,
});

function subscribeIdle() {
  return () => {};
}

function getIdleSnapshot() {
  return IDLE_PANEL;
}

function scopeLine(scope) {
  return [scope.modeText, scope.basisText, scope.dataCutoffText, scope.scopeVersionText]
    .filter(Boolean)
    .join(" · ");
}

export function MonitoringProgressPanelView({
  panel,
  onAction,
  onRefresh,
  onBeginStopConfirm,
  onCancelStopConfirm,
  confirmButtonRef,
}) {
  const view = panel?.view || null;
  const empty = panel?.empty || null;
  const notice = panel?.notice || null;
  const actions = view?.actions || [];
  const showActions = Boolean(view) && !panel?.actionsHidden && actions.length > 0;
  const busy = Boolean(panel?.pendingAction);
  const confirming = Boolean(panel?.confirmStop);

  return (
    <section
      className="monitoring-progress"
      data-monitoring-state={view?.runState || "none"}
      aria-label={MONITORING_PANEL_TEXT.title}
    >
      <div className="monitoring-progress-head">
        <div className="monitoring-progress-heading">
          <h2>{MONITORING_PANEL_TEXT.title}</h2>
          {view && scopeLine(view.scope) ? <p className="monitoring-progress-scope">{scopeLine(view.scope)}</p> : null}
        </div>
        {showActions ? (
          <div
            className="monitoring-progress-actions"
            role="group"
            aria-label={MONITORING_PANEL_TEXT.actionsGroup}
            onKeyDown={(event) => {
              if (event.key === "Escape") onCancelStopConfirm?.();
            }}
          >
            {confirming ? (
              <>
                <button
                  type="button"
                  className="monitoring-progress-action is-confirm"
                  ref={confirmButtonRef}
                  disabled={busy}
                  onClick={() => onAction?.("cancel")}
                >
                  {MONITORING_PANEL_TEXT.confirmStopAction}
                </button>
                <span className="monitoring-progress-confirm-hint">{MONITORING_PANEL_TEXT.confirmStopHint}</span>
              </>
            ) : (
              actions.map((action) => (
                <button
                  key={action.action}
                  type="button"
                  className={`monitoring-progress-action ${action.action === "cancel" ? "is-stop" : "is-primary"}`}
                  disabled={busy}
                  onClick={() => (action.action === "cancel" ? onBeginStopConfirm?.() : onAction?.(action.action))}
                >
                  {action.label}
                </button>
              ))
            )}
          </div>
        ) : null}
      </div>

      {view ? (
        <div className="monitoring-progress-body">
          <div className="monitoring-progress-main">
            <div className="monitoring-progress-summary">
              <span className="monitoring-progress-big">{view.progressText}</span>
              {view.outcomeLabel ? (
                <span className="monitoring-progress-outcome">{view.outcomeLabel}</span>
              ) : null}
            </div>
            <div
              className="monitoring-progress-track"
              role="progressbar"
              aria-valuenow={Math.round(view.percent)}
              aria-valuemin={0}
              aria-valuemax={100}
              aria-valuetext={view.progressText || `${Math.round(view.percent)}%`}
            >
              <div className="monitoring-progress-fill" style={{ width: `${view.percent}%` }} />
            </div>
            <p className="monitoring-progress-status" aria-live="polite">{view.runStatusText}</p>
          </div>
          <div className="monitoring-progress-detail">
            {view.stageProgress.length > 0 ? (
              <section className="monitoring-progress-block" aria-label={MONITORING_PANEL_TEXT.stageGroup}>
                <h3>{MONITORING_PANEL_TEXT.stageGroup}</h3>
                <ul className="monitoring-progress-stages">
                  {view.stageProgress.map((stage, index) => (
                    <li key={`${stage.stage}-${index}`}>
                      <span className="monitoring-stage-name">{stage.stage}</span>
                      <span className="monitoring-stage-count">{stage.progressText || `${stage.processed}/${stage.total}`}</span>
                    </li>
                  ))}
                </ul>
              </section>
            ) : null}
            {view.currentWork.length > 0 || view.currentWorkEmptyText ? (
              <section className="monitoring-progress-block" aria-label={MONITORING_PANEL_TEXT.currentWorkGroup}>
                <h3>{MONITORING_PANEL_TEXT.currentWorkGroup}</h3>
                {view.currentWork.length > 0 ? (
                  <ul className="monitoring-progress-current">
                    {view.currentWork.map((item, index) => (
                      <li key={`${item.label}-${index}`}>
                        <span className="monitoring-cw-label">{item.label}</span>
                        <span className="monitoring-cw-meta">{[item.stateLabel, item.elapsedText].filter(Boolean).join(" · ")}</span>
                      </li>
                    ))}
                    {view.currentWorkRemaining > 0 ? (
                      <li className="monitoring-cw-more">{MONITORING_PANEL_TEXT.moreCurrentWork(view.currentWorkRemaining)}</li>
                    ) : null}
                  </ul>
                ) : (
                  <p className="monitoring-progress-minor">{view.currentWorkEmptyText}</p>
                )}
              </section>
            ) : null}
            <section className="monitoring-progress-block" aria-label={MONITORING_PANEL_TEXT.latestUpdatesGroup}>
              <h3>{MONITORING_PANEL_TEXT.latestUpdatesGroup}</h3>
              {view.latestUpdates.length > 0 ? (
                <ul className="monitoring-progress-updates">
                  {view.latestUpdates.map((update, index) => (
                    <li
                      key={`${update.timeText}-${index}`}
                      className={update.historical ? "is-history" : undefined}
                    >
                      <span className="monitoring-up-time">{update.timeText}</span>
                      <span className="monitoring-up-label">{update.label}</span>
                      <span className="monitoring-up-state">
                        {update.historical ? `过程记录 · ${update.stateLabel}` : update.stateLabel}
                      </span>
                    </li>
                  ))}
                </ul>
              ) : (
                <p className="monitoring-progress-minor">{MONITORING_PANEL_TEXT.latestUpdatesEmpty}</p>
              )}
            </section>
          </div>
        </div>
      ) : null}

      {!view && empty ? <p className="monitoring-progress-empty">{empty.text}</p> : null}
      {!view && !empty && !notice ? (
        <p className="monitoring-progress-loading" role="status">{MONITORING_PANEL_TEXT.loading}</p>
      ) : null}

      {notice ? (
        <div
          className={`monitoring-progress-notice${notice.kind === "forbidden" ? " is-forbidden" : ""}`}
          role="alert"
        >
          <span>{notice.text}</span>
          {notice.kind !== "forbidden" ? (
            <button type="button" className="monitoring-progress-refresh" onClick={() => onRefresh?.()}>
              {MONITORING_PANEL_TEXT.refreshAction}
            </button>
          ) : null}
        </div>
      ) : null}
    </section>
  );
}

export function MedicalMonitoringProgressPanel({ routeCanonical, api }) {
  const [store, setStore] = useState(null);
  const projectRef = routeCanonical?.project_ref || "";
  const runRef = routeCanonical?.run_ref || "";

  useEffect(() => {
    // Create and destroy the store in the same effect so React StrictMode's
    // extra setup/cleanup cycle cannot leave a destroyed store bound to
    // useSyncExternalStore without a subscriber.
    const next = createMonitoringProgressPanelStore(api ? { api } : {});
    setStore(next);
    next.show({ project_ref: projectRef, run_ref: runRef });
    return () => next.destroy();
  }, [api, projectRef, runRef]);

  const panel = useSyncExternalStore(
    store ? store.subscribe : subscribeIdle,
    store ? store.getSnapshot : getIdleSnapshot,
  );
  const confirmButtonRef = useRef(null);

  useEffect(() => {
    // Keep keyboard focus inside the action area while the inline stop
    // confirmation is shown.
    if (panel.confirmStop) confirmButtonRef.current?.focus();
  }, [panel.confirmStop]);

  return (
    <MonitoringProgressPanelView
      panel={panel}
      confirmButtonRef={confirmButtonRef}
      onAction={(action) => store?.pressAction(action)}
      onRefresh={() => store?.refresh()}
      onBeginStopConfirm={() => store?.beginStopConfirm()}
      onCancelStopConfirm={() => store?.cancelStopConfirm()}
    />
  );
}

export default MedicalMonitoringProgressPanel;
