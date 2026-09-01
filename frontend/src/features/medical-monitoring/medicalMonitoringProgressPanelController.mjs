// Interaction store for the live monitoring progress panel. Holds no display
// authority: every fact shown comes from the server progress payload through
// the pure projection. Polling only re-reads facts; nothing here invents
// progress, parses Chinese copy to decide polling, or sends stop requests on
// unload.

import { createMedicalMonitoringProgressApi } from "./medicalMonitoringProgressApi.mjs";
import {
  MONITORING_NO_RUN_TEXT,
  MONITORING_REFRESH_FAILED_TEXT,
  createMonitoringProgressGate,
  projectMonitoringProgress,
  projectMonitoringProgressError,
  monitoringProgressRequestContext,
  monitoringRefreshBackoffMs,
} from "./medicalMonitoringProgressProjection.mjs";

export const MONITORING_STOP_CONFIRM_TIMEOUT_MS = 8000;

export const MONITORING_PANEL_TEXT = Object.freeze({
  title: "本次监查进度",
  loading: "正在读取本次监查进度",
  latestUpdatesEmpty: "暂无最新进展",
  confirmStopAction: "确认停止",
  confirmStopHint: "停止后不再开始下一项；当前正在分析的内容可能完成",
  refreshAction: "重新读取进度",
  actionFailed: "本次操作未完成，进度保持不变",
  stageGroup: "阶段分布",
  currentWorkGroup: "当前工作",
  latestUpdatesGroup: "最近进展",
  actionsGroup: "本次监查运行操作",
  refreshFailedAt: (timeText) => `进度刷新失败，最后读取于 ${timeText}`,
  moreCurrentWork: (count) => `另有 ${count} 项`,
});

const ACTION_METHODS = Object.freeze({
  start: "startExecution",
  cancel: "cancelExecution",
  resume: "resumeExecution",
});

function pad2(value) {
  return String(value).padStart(2, "0");
}

export function monitoringPanelTimeText(epochMs) {
  const date = new Date(epochMs);
  if (!Number.isFinite(date.getTime())) return "";
  return `${pad2(date.getHours())}:${pad2(date.getMinutes())}`;
}

function defaultVisibility() {
  const doc = globalThis.document;
  if (!doc || typeof doc.addEventListener !== "function") {
    return Object.freeze({ isVisible: () => true, subscribe: () => () => {} });
  }
  return Object.freeze({
    isVisible: () => doc.visibilityState !== "hidden",
    subscribe(listener) {
      doc.addEventListener("visibilitychange", listener);
      return () => doc.removeEventListener("visibilitychange", listener);
    },
  });
}

export function createMonitoringProgressPanelStore({
  api = createMedicalMonitoringProgressApi(),
  now = () => Date.now(),
  schedule = (fn, ms) => setTimeout(fn, ms),
  unschedule = (handle) => clearTimeout(handle),
  visibility = defaultVisibility(),
  confirmTimeoutMs = MONITORING_STOP_CONFIRM_TIMEOUT_MS,
} = {}) {
  if (typeof schedule !== "function") throw new TypeError("schedule must be a function");
  if (typeof unschedule !== "function") throw new TypeError("unschedule must be a function");
  if (typeof now !== "function") throw new TypeError("now must be a function");
  if (!visibility || typeof visibility.isVisible !== "function" || typeof visibility.subscribe !== "function") {
    throw new TypeError("visibility must expose isVisible() and subscribe()");
  }

  const gate = createMonitoringProgressGate();
  const listeners = new Set();
  const inFlight = new Set();

  let destroyed = false;
  let shownOnce = false;
  let identity = null;
  let actionEpoch = 0;
  let pollTimer = null;
  let confirmTimer = null;
  let consecutiveFailures = 0;
  let lastReadAt = 0;

  let fields = {
    view: null,
    empty: null,
    notice: null,
    actionsHidden: false,
    pendingAction: null,
    confirmStop: false,
  };
  let snapshot = Object.freeze({ ...fields });

  function emit() {
    snapshot = Object.freeze({ ...fields });
    for (const listener of listeners) listener();
  }

  function clearPollTimer() {
    if (pollTimer !== null) {
      unschedule(pollTimer);
      pollTimer = null;
    }
  }

  function clearConfirmTimer() {
    if (confirmTimer !== null) {
      unschedule(confirmTimer);
      confirmTimer = null;
    }
  }

  function setConfirmStop(next) {
    clearConfirmTimer();
    fields.confirmStop = next;
    if (next) {
      confirmTimer = schedule(() => {
        confirmTimer = null;
        if (fields.confirmStop) {
          fields.confirmStop = false;
          emit();
        }
      }, confirmTimeoutMs);
    }
  }

  function wantsPolling() {
    return !fields.view || fields.view.poll.active;
  }

  function scheduleNextLoad(ms) {
    clearPollTimer();
    if (!ms || ms <= 0) return;
    pollTimer = schedule(() => {
      pollTimer = null;
      if (destroyed || !identity) return;
      // While the page is hidden polling stops; becoming visible refreshes
      // immediately through the visibility listener.
      if (!visibility.isVisible()) return;
      void load();
    }, ms);
  }

  function handleReadFailure() {
    consecutiveFailures += 1;
    const timeText = lastReadAt ? monitoringPanelTimeText(lastReadAt) : "";
    fields = {
      ...fields,
      notice: Object.freeze({
        kind: "refresh_failed",
        text: timeText ? MONITORING_PANEL_TEXT.refreshFailedAt(timeText) : MONITORING_REFRESH_FAILED_TEXT,
      }),
    };
    emit();
    scheduleNextLoad(wantsPolling() ? monitoringRefreshBackoffMs(consecutiveFailures) : 0);
  }

  async function load() {
    if (destroyed || !identity) return;
    const current = identity;
    const ticket = gate.begin(current);
    const controller = new AbortController();
    inFlight.add(controller);
    try {
      const payload = await api.getProgress(current.projectRef, current.runRef, { signal: controller.signal });
      if (destroyed || !gate.accept(ticket)) return;
      const view = projectMonitoringProgress(payload);
      if (view.kind === "progress") {
        lastReadAt = now();
        consecutiveFailures = 0;
        fields = { ...fields, view, empty: null, notice: null };
        emit();
        scheduleNextLoad(view.poll.active ? view.poll.intervalMs : 0);
        return;
      }
      // An unparsable payload is a read failure: keep the last facts.
      handleReadFailure();
    } catch (error) {
      if (controller.signal.aborted || destroyed || !gate.accept(ticket)) return;
      const mapped = projectMonitoringProgressError(error);
      if (mapped.kind === "empty") {
        consecutiveFailures = 0;
        fields = {
          ...fields,
          view: null,
          empty: Object.freeze({ reason: mapped.emptyReason, text: mapped.text }),
          notice: null,
        };
        emit();
        scheduleNextLoad(0);
        return;
      }
      if (mapped.kind === "forbidden") {
        consecutiveFailures = 0;
        fields = {
          ...fields,
          notice: Object.freeze({ kind: "forbidden", text: mapped.text }),
          actionsHidden: true,
        };
        emit();
        scheduleNextLoad(0);
        return;
      }
      handleReadFailure();
    } finally {
      inFlight.delete(controller);
    }
  }

  function show(canonicalRoute) {
    if (destroyed) {
      // React StrictMode mounts, unmounts, and remounts in development: the
      // simulated unmount runs destroy(), then the remount effect calls
      // show() again on the same store instance. Revive the store instead of
      // leaving the panel deadlocked on the loading text.
      destroyed = false;
      shownOnce = false;
      identity = null;
      unsubscribeVisibility = visibility.subscribe(handleVisibility);
    }
    const context = monitoringProgressRequestContext(canonicalRoute);
    const key = context ? `${context.projectRef}‱${context.runRef}` : "";
    const currentKey = identity ? `${identity.projectRef}‱${identity.runRef}` : "";
    if (shownOnce && key === currentKey) return;
    shownOnce = true;
    identity = context;
    actionEpoch += 1;
    consecutiveFailures = 0;
    lastReadAt = 0;
    clearPollTimer();
    setConfirmStop(false);
    fields = {
      view: null,
      empty: context ? null : Object.freeze({ reason: "no_run", text: MONITORING_NO_RUN_TEXT }),
      notice: null,
      actionsHidden: false,
      pendingAction: null,
      confirmStop: false,
    };
    emit();
    if (context) void load();
  }

  function refresh() {
    if (destroyed || !identity) return;
    consecutiveFailures = 0;
    void load();
  }

  function beginStopConfirm() {
    if (destroyed || fields.pendingAction) return;
    if (fields.confirmStop) return;
    setConfirmStop(true);
    emit();
  }

  function cancelStopConfirm() {
    if (!fields.confirmStop) return;
    setConfirmStop(false);
    emit();
  }

  async function pressAction(action) {
    if (destroyed || !identity || fields.pendingAction || !ACTION_METHODS[action]) return;
    // 停止 requires the inline confirm step first; while the confirm is
    // showing, every other action stays locked out.
    if (action === "cancel" && !fields.confirmStop) return;
    if (action !== "cancel" && fields.confirmStop) return;
    const current = identity;
    const epoch = actionEpoch;
    setConfirmStop(false);
    fields.pendingAction = action;
    emit();
    const controller = new AbortController();
    inFlight.add(controller);
    try {
      await api[ACTION_METHODS[action]](current.projectRef, current.runRef, { signal: controller.signal });
      if (controller.signal.aborted || destroyed || epoch !== actionEpoch) return;
      fields = { ...fields, pendingAction: null };
      emit();
      // After the action response, re-read the progress facts.
      await load();
    } catch (error) {
      if (controller.signal.aborted || destroyed || epoch !== actionEpoch) return;
      const mapped = projectMonitoringProgressError(error);
      fields = { ...fields, pendingAction: null };
      if (mapped.kind === "forbidden") {
        fields.notice = Object.freeze({ kind: "forbidden", text: mapped.text });
        fields.actionsHidden = true;
      } else {
        const status = Number(error?.status) || 0;
        const serverText = status > 0 ? String(error?.message || "").trim() : "";
        fields.notice = Object.freeze({
          kind: "action_failed",
          text: serverText || MONITORING_PANEL_TEXT.actionFailed,
        });
      }
      emit();
    } finally {
      inFlight.delete(controller);
    }
  }

  function handleVisibility() {
    if (destroyed) return;
    if (visibility.isVisible()) {
      if (identity) {
        consecutiveFailures = 0;
        void load();
      }
    } else {
      clearPollTimer();
    }
  }

  let unsubscribeVisibility = visibility.subscribe(handleVisibility);

  function destroy() {
    if (destroyed) return;
    destroyed = true;
    actionEpoch += 1;
    gate.reset();
    clearPollTimer();
    clearConfirmTimer();
    // Unloading never sends a stop request; in-flight reads are only aborted
    // locally and their late responses are dropped by the gate.
    for (const controller of inFlight) controller.abort();
    inFlight.clear();
    unsubscribeVisibility();
    // Keep subscribers. React 19 StrictMode re-runs the show/destroy
    // effects on the same store while useSyncExternalStore is still
    // attached; clearing listeners here leaves the panel stuck on the
    // loading text after show() revives the instance.
  }

  return Object.freeze({
    subscribe(listener) {
      listeners.add(listener);
      return () => listeners.delete(listener);
    },
    getSnapshot: () => snapshot,
    show,
    refresh,
    pressAction,
    beginStopConfirm,
    cancelStopConfirm,
    destroy,
  });
}
