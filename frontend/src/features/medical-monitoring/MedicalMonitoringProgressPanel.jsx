import { useEffect, useRef, useState, useSyncExternalStore } from "react";
import {
  R7_PANEL_TEXT,
  createR7ProgressPanelStore,
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

export function R7ProgressPanelView({
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
      className="r7-progress"
      data-r7-state={view?.runState || "none"}
      aria-label={R7_PANEL_TEXT.title}
    >
      <div className="r7-progress-head">
        <div className="r7-progress-heading">
          <h2>{R7_PANEL_TEXT.title}</h2>
          {view && scopeLine(view.scope) ? <p className="r7-progress-scope">{scopeLine(view.scope)}</p> : null}
        </div>
        {showActions ? (
          <div
            className="r7-progress-actions"
            role="group"
            aria-label={R7_PANEL_TEXT.actionsGroup}
            onKeyDown={(event) => {
              if (event.key === "Escape") onCancelStopConfirm?.();
            }}
          >
            {confirming ? (
              <>
                <button
                  type="button"
                  className="r7-progress-action is-confirm"
                  ref={confirmButtonRef}
                  disabled={busy}
                  onClick={() => onAction?.("cancel")}
                >
                  {R7_PANEL_TEXT.confirmStopAction}
                </button>
                <span className="r7-progress-confirm-hint">{R7_PANEL_TEXT.confirmStopHint}</span>
              </>
            ) : (
              actions.map((action) => (
                <button
                  key={action.action}
                  type="button"
                  className={`r7-progress-action ${action.action === "cancel" ? "is-stop" : "is-primary"}`}
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
        <div className="r7-progress-body">
          <div className="r7-progress-main">
            <div className="r7-progress-summary">
              <span className="r7-progress-big">{view.progressText}</span>
              {view.outcomeLabel ? (
                <span className="r7-progress-outcome">{view.outcomeLabel}</span>
              ) : null}
            </div>
            <div
              className="r7-progress-track"
              role="progressbar"
              aria-valuenow={Math.round(view.percent)}
              aria-valuemin={0}
              aria-valuemax={100}
              aria-valuetext={view.progressText || `${Math.round(view.percent)}%`}
            >
              <div className="r7-progress-fill" style={{ width: `${view.percent}%` }} />
            </div>
            <p className="r7-progress-status" aria-live="polite">{view.runStatusText}</p>
          </div>
          <div className="r7-progress-detail">
            {view.stageProgress.length > 0 ? (
              <section className="r7-progress-block" aria-label={R7_PANEL_TEXT.stageGroup}>
                <h3>{R7_PANEL_TEXT.stageGroup}</h3>
                <ul className="r7-progress-stages">
                  {view.stageProgress.map((stage, index) => (
                    <li key={`${stage.stage}-${index}`}>
                      <span className="r7-stage-name">{stage.stage}</span>
                      <span className="r7-stage-count">{stage.progressText || `${stage.processed}/${stage.total}`}</span>
                    </li>
                  ))}
                </ul>
              </section>
            ) : null}
            {view.currentWork.length > 0 || view.currentWorkEmptyText ? (
              <section className="r7-progress-block" aria-label={R7_PANEL_TEXT.currentWorkGroup}>
                <h3>{R7_PANEL_TEXT.currentWorkGroup}</h3>
                {view.currentWork.length > 0 ? (
                  <ul className="r7-progress-current">
                    {view.currentWork.map((item, index) => (
                      <li key={`${item.label}-${index}`}>
                        <span className="r7-cw-label">{item.label}</span>
                        <span className="r7-cw-meta">{[item.stateLabel, item.elapsedText].filter(Boolean).join(" · ")}</span>
                      </li>
                    ))}
                    {view.currentWorkRemaining > 0 ? (
                      <li className="r7-cw-more">{R7_PANEL_TEXT.moreCurrentWork(view.currentWorkRemaining)}</li>
                    ) : null}
                  </ul>
                ) : (
                  <p className="r7-progress-minor">{view.currentWorkEmptyText}</p>
                )}
              </section>
            ) : null}
            <section className="r7-progress-block" aria-label={R7_PANEL_TEXT.latestUpdatesGroup}>
              <h3>{R7_PANEL_TEXT.latestUpdatesGroup}</h3>
              {view.latestUpdates.length > 0 ? (
                <ul className="r7-progress-updates">
                  {view.latestUpdates.map((update, index) => (
                    <li
                      key={`${update.timeText}-${index}`}
                      className={update.historical ? "is-history" : undefined}
                    >
                      <span className="r7-up-time">{update.timeText}</span>
                      <span className="r7-up-label">{update.label}</span>
                      <span className="r7-up-state">
                        {update.historical ? `过程记录 · ${update.stateLabel}` : update.stateLabel}
                      </span>
                    </li>
                  ))}
                </ul>
              ) : (
                <p className="r7-progress-minor">{R7_PANEL_TEXT.latestUpdatesEmpty}</p>
              )}
            </section>
          </div>
        </div>
      ) : null}

      {!view && empty ? <p className="r7-progress-empty">{empty.text}</p> : null}
      {!view && !empty && !notice ? (
        <p className="r7-progress-loading" role="status">{R7_PANEL_TEXT.loading}</p>
      ) : null}

      {notice ? (
        <div
          className={`r7-progress-notice${notice.kind === "forbidden" ? " is-forbidden" : ""}`}
          role="alert"
        >
          <span>{notice.text}</span>
          {notice.kind !== "forbidden" ? (
            <button type="button" className="r7-progress-refresh" onClick={() => onRefresh?.()}>
              {R7_PANEL_TEXT.refreshAction}
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
    const next = createR7ProgressPanelStore(api ? { api } : {});
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
    <R7ProgressPanelView
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
