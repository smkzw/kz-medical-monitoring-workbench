import assert from "node:assert/strict";
import {
  R7_PANEL_TEXT,
  R7_STOP_CONFIRM_TIMEOUT_MS,
  createR7ProgressPanelStore,
  r7PanelTimeText,
} from "./medicalMonitoringR7ProgressPanelController.mjs";
import {
  R7_NO_RUN_TEXT,
  R7_NOT_PREPARED_TEXT,
  R7_FORBIDDEN_ACCOUNT_TEXT,
  findR7ForbiddenTerms,
} from "./medicalMonitoringR7ProgressProjection.mjs";

let passed = 0;
function check(condition, message) {
  assert.ok(condition, message);
  passed += 1;
}

async function flush(rounds = 8) {
  for (let i = 0; i < rounds; i += 1) await Promise.resolve();
}

function deferred() {
  let resolve;
  let reject;
  const promise = new Promise((res, rej) => {
    resolve = res;
    reject = rej;
  });
  return { promise, resolve, reject };
}

function createTimers() {
  let nextId = 0;
  const tasks = new Map();
  return {
    schedule(fn, ms) {
      const id = ++nextId;
      tasks.set(id, { fn, ms });
      return id;
    },
    unschedule(id) {
      tasks.delete(id);
    },
    pending() {
      return [...tasks.values()].map((task) => task.ms);
    },
    async fire(ms) {
      const due = [...tasks.entries()].filter(([, task]) => task.ms === ms).map(([id]) => id);
      for (const id of due) {
        const task = tasks.get(id);
        if (task) {
          tasks.delete(id);
          task.fn();
        }
      }
      await flush();
    },
  };
}

function createVisibility() {
  let visible = true;
  const listeners = new Set();
  return {
    setVisible(next) {
      visible = next;
      for (const listener of listeners) listener();
    },
    visibility: {
      isVisible: () => visible,
      subscribe(listener) {
        listeners.add(listener);
        return () => listeners.delete(listener);
      },
    },
  };
}

const NOW = new Date(2026, 7, 28, 14, 5).getTime();
check(r7PanelTimeText(NOW) === "14:05", "time text renders HH:MM");

function httpError(status, code, message) {
  const error = new Error(message);
  error.status = status;
  error.detail = code ? { code, message } : { message };
  return error;
}

function progressPayload(overrides = {}) {
  return {
    scope_version_text: "第 2 版监查范围",
    mode_text: "日常监查",
    basis_text: "增量",
    data_cutoff_text: "2026-08-28",
    completed: 3,
    total: 8,
    percent: 37.5,
    progress_text: "已处理 3/8 项（37.5%）",
    stage_progress: [
      { stage: "数据核查", processed: 2, total: 3, progress_text: "已处理 2/3 项" },
      { stage: "医学审阅", processed: 1, total: 5, progress_text: "已处理 1/5 项" },
    ],
    current_work: [
      { stage: "医学审阅", label: "审阅实验室异常", state_label: "进行中", elapsed_text: "约 2 分钟", message: "正在进行：审阅实验室异常" },
    ],
    latest_updates: [
      { time_text: "10:31", stage: "数据核查", label: "核查入排标准", state_label: "已完成", message: "已完成：核查入排标准" },
    ],
    run_status_text: "医学监查进行中",
    available_actions: ["停止"],
    run_state: "running",
    ...overrides,
  };
}

// Sticky-last handler queues: each queued handler runs once, and the final
// handler repeats for any further calls so tests only queue what they assert.
function createFakeApi() {
  const calls = [];
  const progressHandlers = [];
  const actionHandlers = { start: [], cancel: [], resume: [] };
  function take(queue, label) {
    if (!queue.length) throw new Error(`unexpected ${label} call`);
    return queue.length > 1 ? queue.shift() : queue[0];
  }
  return {
    calls,
    queueProgress(...handlers) {
      progressHandlers.push(...handlers);
    },
    queueAction(action, ...handlers) {
      actionHandlers[action].push(...handlers);
    },
    api: {
      getProgress(projectRef, runRef, { signal } = {}) {
        calls.push({ method: "getProgress", projectRef, runRef, signal });
        return take(progressHandlers, "getProgress")();
      },
      startExecution(projectRef, runRef, { signal } = {}) {
        calls.push({ method: "startExecution", projectRef, runRef, signal });
        return take(actionHandlers.start, "startExecution")();
      },
      cancelExecution(projectRef, runRef, { signal } = {}) {
        calls.push({ method: "cancelExecution", projectRef, runRef, signal });
        return take(actionHandlers.cancel, "cancelExecution")();
      },
      resumeExecution(projectRef, runRef, { signal } = {}) {
        calls.push({ method: "resumeExecution", projectRef, runRef, signal });
        return take(actionHandlers.resume, "resumeExecution")();
      },
    },
  };
}

function createHarness({ now = () => NOW } = {}) {
  const fake = createFakeApi();
  const timers = createTimers();
  const vis = createVisibility();
  const store = createR7ProgressPanelStore({
    api: fake.api,
    now,
    schedule: timers.schedule,
    unschedule: timers.unschedule,
    visibility: vis.visibility,
  });
  return { fake, timers, vis, store };
}

const ROUTE = { project_ref: "synthetic-project-r7-s07a", run_ref: "synthetic-run-r7-20260828" };

// 1. Missing run_ref: neutral empty state, no request.
{
  const { fake, store } = createHarness();
  store.show({ project_ref: "synthetic-project-r7-s07a" });
  await flush();
  check(store.getSnapshot().empty?.text === R7_NO_RUN_TEXT, "missing run_ref shows neutral empty state");
  check(fake.calls.length === 0, "missing run_ref sends no progress request");
  store.destroy();
}

// 2. waiting_start: facts render, start action available, no polling.
{
  const { fake, timers, store } = createHarness();
  fake.queueProgress(() => Promise.resolve(progressPayload({
    completed: 0,
    percent: 0,
    progress_text: "已处理 0/8 项（0%）",
    current_work: [],
    latest_updates: [],
    run_status_text: "等待开始医学监查",
    available_actions: ["开始"],
    run_state: "waiting_start",
  })));
  store.show(ROUTE);
  await flush();
  const snap = store.getSnapshot();
  check(snap.view?.runState === "waiting_start", "waiting_start view retained");
  check(snap.view.actions.map((a) => a.action).join(",") === "start", "start action projected");
  check(timers.pending().length === 0, "waiting_start does not poll");
  store.destroy();
}

// 3. running: polls every 2s.
{
  const { fake, timers, store } = createHarness();
  fake.queueProgress(() => Promise.resolve(progressPayload()));
  store.show(ROUTE);
  await flush();
  check(timers.pending().join(",") === "2000", "running schedules a 2s poll");
  await timers.fire(2000);
  check(fake.calls.filter((c) => c.method === "getProgress").length === 2, "poll re-reads progress");
  store.destroy();
}

// 4. completed: no polling.
{
  const { timers, fake, store } = createHarness();
  fake.queueProgress(() => Promise.resolve(progressPayload({
    completed: 8,
    percent: 100,
    progress_text: "已处理 8/8 项（100%）",
    current_work: [],
    run_status_text: "本次监查已完成",
    available_actions: [],
    run_state: "completed",
  })));
  store.show(ROUTE);
  await flush();
  check(store.getSnapshot().view?.runState === "completed", "completed view retained");
  check(timers.pending().length === 0, "completed does not poll");
  store.destroy();
}

// 5. stopping: keeps polling, facts retained.
{
  const { fake, timers, store } = createHarness();
  fake.queueProgress(() => Promise.resolve(progressPayload({
    run_status_text: "正在停止…",
    available_actions: [],
    run_state: "stopping",
  })));
  store.show(ROUTE);
  await flush();
  check(store.getSnapshot().view?.runState === "stopping", "stopping view retained");
  check(store.getSnapshot().view?.progressText === "已处理 3/8 项（37.5%）", "stopping keeps completed facts");
  check(timers.pending().join(",") === "2000", "stopping keeps polling");
  store.destroy();
}

// 6. Refresh failure: facts retained, last-read time shown, 2→5→10→30s backoff.
{
  const { fake, timers, store } = createHarness();
  fake.queueProgress(
    () => Promise.resolve(progressPayload()),
    () => Promise.reject(httpError(500, "", "ignored")),
  );
  store.show(ROUTE);
  await flush();
  check(store.getSnapshot().view?.progressText === "已处理 3/8 项（37.5%）", "facts present before failure");
  await timers.fire(2000); // first poll fails
  let snap = store.getSnapshot();
  check(snap.view?.progressText === "已处理 3/8 项（37.5%）", "failure keeps last facts");
  check(snap.notice?.kind === "refresh_failed", "failure notice kind");
  check(snap.notice?.text === "进度刷新失败，最后读取于 14:05", "failure shows last-read time");
  check(timers.pending().join(",") === "2000", "first failure backs off 2s");
  await timers.fire(2000);
  check(timers.pending().join(",") === "5000", "second failure backs off 5s");
  await timers.fire(5000);
  check(timers.pending().join(",") === "10000", "third failure backs off 10s");
  await timers.fire(10000);
  check(timers.pending().join(",") === "30000", "fourth failure backs off 30s");
  await timers.fire(30000);
  check(timers.pending().join(",") === "30000", "backoff stays capped at 30s");
  snap = store.getSnapshot();
  check(snap.view?.runState === "running", "facts still retained after repeated failures");
  store.destroy();
}

// 7. First-read failure: loading replaced by failure notice, retry scheduled.
{
  const { fake, timers, store } = createHarness();
  fake.queueProgress(() => Promise.reject(httpError(500, "", "ignored")));
  store.show(ROUTE);
  await flush();
  const snap = store.getSnapshot();
  check(snap.view === null, "first-read failure shows no facts");
  check(snap.notice?.text === "进度刷新失败", "first-read failure shows plain failure copy");
  check(timers.pending().join(",") === "2000", "first-read failure retries with backoff");
  store.destroy();
}

// 8/9. Machine-code empty states.
{
  const { fake, timers, store } = createHarness();
  fake.queueProgress(() => Promise.reject(httpError(404, "run_binding_not_found", R7_NO_RUN_TEXT)));
  store.show(ROUTE);
  await flush();
  check(store.getSnapshot().empty?.reason === "no_run", "run_binding_not_found maps to no_run empty");
  check(store.getSnapshot().empty?.text === R7_NO_RUN_TEXT, "no_run copy");
  check(timers.pending().length === 0, "empty state does not poll");
  store.destroy();
}
{
  const { fake, store } = createHarness();
  fake.queueProgress(() => Promise.reject(httpError(409, "execution_not_prepared", R7_NOT_PREPARED_TEXT)));
  store.show(ROUTE);
  await flush();
  check(store.getSnapshot().empty?.reason === "not_prepared", "execution_not_prepared maps to not_prepared empty");
  check(store.getSnapshot().empty?.text === R7_NOT_PREPARED_TEXT, "not_prepared copy");
  store.destroy();
}

// 10. 403 on load: forbidden notice, actions hidden.
{
  const { fake, store } = createHarness();
  fake.queueProgress(() => Promise.reject(httpError(403, "", "denied")));
  store.show(ROUTE);
  await flush();
  const snap = store.getSnapshot();
  check(snap.notice?.kind === "forbidden", "403 maps to forbidden notice");
  check(snap.notice?.text === R7_FORBIDDEN_ACCOUNT_TEXT, "forbidden copy");
  check(snap.actionsHidden === true, "403 hides actions for this load cycle");
  store.destroy();
}

// 11. Invalid payload: treated as read failure, never renders invented facts.
{
  const { fake, store } = createHarness();
  fake.queueProgress(
    () => Promise.resolve(progressPayload()),
    () => Promise.resolve({ completed: 99, total: 100 }), // run_state missing
  );
  store.show(ROUTE);
  await flush();
  store.refresh();
  await flush();
  const snap = store.getSnapshot();
  check(snap.view?.progressText === "已处理 3/8 项（37.5%）", "invalid payload keeps last facts");
  check(snap.notice?.kind === "refresh_failed", "invalid payload maps to refresh failure");
  store.destroy();
}

// 12. Late responses are rejected by the gate.
{
  const { fake, store } = createHarness();
  const first = deferred();
  fake.queueProgress(
    () => first.promise,
    () => Promise.resolve(progressPayload({ progress_text: "已处理 4/8 项（50%）", percent: 50, completed: 4 })),
  );
  store.show(ROUTE);
  store.refresh();
  await flush();
  check(store.getSnapshot().view?.progressText === "已处理 4/8 项（50%）", "newer response lands");
  first.resolve(progressPayload({ progress_text: "已处理 9/9 项（100%）" }));
  await flush();
  check(store.getSnapshot().view?.progressText === "已处理 4/8 项（50%）", "late stale response is rejected");
  store.destroy();
}

// 13. Start action: one POST, duplicate press ignored, progress re-read.
{
  const { fake, store } = createHarness();
  fake.queueProgress(() => Promise.resolve(progressPayload({
    run_state: "waiting_start",
    available_actions: ["开始"],
    run_status_text: "等待开始医学监查",
    current_work: [],
  })));
  fake.queueAction("start", () => Promise.resolve({ run_status_text: "医学监查进行中", available_actions: ["停止"] }));
  store.show(ROUTE);
  await flush();
  const pending = store.pressAction("start");
  check(store.getSnapshot().pendingAction === "start", "pending action exposed while in flight");
  store.pressAction("start"); // duplicate press
  await pending;
  await flush();
  const starts = fake.calls.filter((c) => c.method === "startExecution");
  check(starts.length === 1, "duplicate start press is ignored");
  check(starts[0].projectRef === ROUTE.project_ref && starts[0].runRef === ROUTE.run_ref, "start posts to the bound run");
  const sequence = fake.calls.map((c) => c.method).join(",");
  check(sequence === "getProgress,startExecution,getProgress", "progress re-read after action response");
  check(store.getSnapshot().pendingAction === null, "pending cleared after action");
  store.destroy();
}

// 14. Stop: requires inline confirm; confirm posts cancel.
{
  const { fake, timers, store } = createHarness();
  fake.queueProgress(() => Promise.resolve(progressPayload()));
  fake.queueAction("cancel", () => Promise.resolve({ run_status_text: "正在停止…", available_actions: [] }));
  store.show(ROUTE);
  await flush();
  store.pressAction("cancel"); // without confirm
  await flush();
  check(fake.calls.filter((c) => c.method === "cancelExecution").length === 0, "stop requires confirm first");
  store.beginStopConfirm();
  check(store.getSnapshot().confirmStop === true, "confirm state shown inline");
  check(timers.pending().includes(R7_STOP_CONFIRM_TIMEOUT_MS), "confirm auto-revert timer armed");
  await store.pressAction("cancel");
  await flush();
  check(fake.calls.filter((c) => c.method === "cancelExecution").length === 1, "confirmed stop posts cancel");
  check(store.getSnapshot().confirmStop === false, "confirm cleared after action");
  store.destroy();
}

// 15. Confirm auto-reverts after 8s without posting.
{
  const { fake, timers, store } = createHarness();
  fake.queueProgress(() => Promise.resolve(progressPayload()));
  store.show(ROUTE);
  await flush();
  store.beginStopConfirm();
  await timers.fire(R7_STOP_CONFIRM_TIMEOUT_MS);
  check(store.getSnapshot().confirmStop === false, "confirm auto-reverts after timeout");
  check(fake.calls.filter((c) => c.method === "cancelExecution").length === 0, "timeout posts nothing");
  store.destroy();
}

// 16. Esc cancels the confirm without posting.
{
  const { fake, timers, store } = createHarness();
  fake.queueProgress(() => Promise.resolve(progressPayload()));
  store.show(ROUTE);
  await flush();
  store.beginStopConfirm();
  store.cancelStopConfirm();
  check(store.getSnapshot().confirmStop === false, "Esc path reverts confirm");
  check(!timers.pending().includes(R7_STOP_CONFIRM_TIMEOUT_MS), "confirm timer cleared on revert");
  check(fake.calls.filter((c) => c.method === "cancelExecution").length === 0, "revert posts nothing");
  store.destroy();
}

// 17. While confirming, other actions stay locked out.
{
  const { fake, store } = createHarness();
  fake.queueProgress(() => Promise.resolve(progressPayload({ available_actions: ["停止", "继续"] })));
  store.show(ROUTE);
  await flush();
  store.beginStopConfirm();
  store.pressAction("resume");
  await flush();
  check(fake.calls.filter((c) => c.method === "resumeExecution").length === 0, "other actions blocked during confirm");
  store.destroy();
}

// 18. Action 403: facts kept, actions hidden, forbidden notice.
{
  const { fake, store } = createHarness();
  fake.queueProgress(() => Promise.resolve(progressPayload()));
  fake.queueAction("cancel", () => Promise.reject(httpError(403, "", "denied")));
  store.show(ROUTE);
  await flush();
  store.beginStopConfirm();
  await store.pressAction("cancel");
  await flush();
  const snap = store.getSnapshot();
  check(snap.notice?.kind === "forbidden", "action 403 shows forbidden notice");
  check(snap.actionsHidden === true, "action 403 hides actions");
  check(snap.view?.progressText === "已处理 3/8 项（37.5%）", "action 403 keeps facts");
  store.destroy();
}

// 19. Action failure with server copy: shown near actions, facts kept.
{
  const { fake, store } = createHarness();
  fake.queueProgress(() => Promise.resolve(progressPayload({ run_state: "interrupted_resumable", available_actions: ["继续"] })));
  fake.queueAction("resume", () => Promise.reject(httpError(409, "execution_conflict", "当前状态不能继续")));
  store.show(ROUTE);
  await flush();
  await store.pressAction("resume");
  await flush();
  const snap = store.getSnapshot();
  check(snap.notice?.kind === "action_failed", "action failure notice kind");
  check(snap.notice?.text === "当前状态不能继续", "action failure shows server Chinese copy");
  check(snap.view?.runState === "interrupted_resumable", "action failure keeps facts");
  check(snap.actionsHidden === false, "non-403 action failure keeps actions visible");
  store.destroy();
}

// 20. Page hidden stops polling; visible again refreshes immediately.
{
  const { fake, timers, vis, store } = createHarness();
  fake.queueProgress(() => Promise.resolve(progressPayload()));
  store.show(ROUTE);
  await flush();
  check(timers.pending().join(",") === "2000", "polling active while visible");
  vis.setVisible(false);
  check(timers.pending().length === 0, "hidden page stops polling");
  const before = fake.calls.filter((c) => c.method === "getProgress").length;
  vis.setVisible(true);
  await flush();
  check(fake.calls.filter((c) => c.method === "getProgress").length === before + 1, "visible again refreshes immediately");
  store.destroy();
}

// 21. Unmount aborts in-flight reads and never sends a stop request.
{
  const { fake, timers, store } = createHarness();
  const hanging = deferred();
  fake.queueProgress(() => hanging.promise);
  store.show(ROUTE);
  await flush();
  const readCall = fake.calls.find((c) => c.method === "getProgress");
  store.destroy();
  check(readCall.signal.aborted === true, "unmount aborts in-flight read");
  check(timers.pending().length === 0, "unmount clears timers");
  hanging.resolve(progressPayload());
  await flush();
  check(store.getSnapshot().view === null, "post-unmount response is dropped");
  check(fake.calls.every((c) => c.method === "getProgress"), "unmount sends no stop request");
  store.destroy(); // idempotent
  check(true, "destroy is idempotent");
}

// 22. Identity switch rejects the previous run's late response.
{
  const { fake, store } = createHarness();
  const stale = deferred();
  fake.queueProgress(
    () => stale.promise,
    () => Promise.resolve(progressPayload({ progress_text: "已处理 1/4 项（25%）" })),
  );
  store.show(ROUTE);
  await flush();
  store.show({ project_ref: ROUTE.project_ref, run_ref: "synthetic-run-r7-next" });
  await flush();
  stale.resolve(progressPayload({ progress_text: "已处理 9/9 项（100%）" }));
  await flush();
  check(store.getSnapshot().view?.progressText === "已处理 1/4 项（25%）", "previous run's late response is rejected");
  store.destroy();
}

// 23. Showing the same identity twice does not reload.
{
  const { fake, store } = createHarness();
  fake.queueProgress(() => Promise.resolve(progressPayload()));
  store.show(ROUTE);
  await flush();
  store.show({ ...ROUTE });
  await flush();
  check(fake.calls.filter((c) => c.method === "getProgress").length === 1, "same identity is a no-op");
  store.destroy();
}

// 24. Snapshot identity is stable between changes (useSyncExternalStore safe).
{
  const { fake, store } = createHarness();
  fake.queueProgress(() => Promise.resolve(progressPayload()));
  const before = store.getSnapshot();
  check(store.getSnapshot() === before, "snapshot stable without change");
  store.show(ROUTE);
  await flush();
  check(store.getSnapshot() !== before, "snapshot changes on update");
  store.destroy();
}

// 25. Forbidden-term scan over panel copy and failure/confirm texts.
{
  const texts = [
    R7_PANEL_TEXT.title,
    R7_PANEL_TEXT.loading,
    R7_PANEL_TEXT.latestUpdatesEmpty,
    R7_PANEL_TEXT.confirmStopAction,
    R7_PANEL_TEXT.confirmStopHint,
    R7_PANEL_TEXT.refreshAction,
    R7_PANEL_TEXT.actionFailed,
    R7_PANEL_TEXT.stageGroup,
    R7_PANEL_TEXT.currentWorkGroup,
    R7_PANEL_TEXT.latestUpdatesGroup,
    R7_PANEL_TEXT.actionsGroup,
    R7_PANEL_TEXT.refreshFailedAt("14:05"),
    R7_PANEL_TEXT.moreCurrentWork(2),
  ];
  const hits = findR7ForbiddenTerms(texts);
  check(hits.length === 0, `panel copy excludes forbidden terms${hits.length ? `: ${JSON.stringify(hits)}` : ""}`);
}

// 26. StrictMode remount: show() after destroy() revives the store and
// re-reads progress instead of deadlocking on the loading text.
{
  const { fake, timers, vis, store } = createHarness();
  fake.queueProgress(() => Promise.resolve(progressPayload()));
  fake.queueProgress(() => Promise.resolve(progressPayload()));
  store.show(ROUTE);
  await flush();
  check(store.getSnapshot().view?.runState === "running", "initial show loads facts");
  store.destroy();
  check(timers.pending().length === 0, "destroy clears the poll timer");
  store.show(ROUTE);
  await flush();
  const snap = store.getSnapshot();
  check(snap.view?.runState === "running", "show after destroy revives and reloads facts");
  check(fake.calls.filter((c) => c.method === "getProgress").length === 2, "revival re-reads progress");
  check(timers.pending().join(",") === "2000", "revival resumes polling");
  vis.setVisible(false);
  await flush();
  vis.setVisible(true);
  fake.queueProgress(() => Promise.resolve(progressPayload()));
  await flush();
  check(fake.calls.filter((c) => c.method === "getProgress").length === 3, "visibility refresh works after revival");
  store.destroy();
}

// 27. StrictMode effect re-run: a subscriber attached before destroy() still
// receives the revived show() snapshot. Clearing listeners on destroy is
// what left the Vite-dev panel stuck on the loading text.
{
  const { fake, store } = createHarness();
  let lastState = null;
  const unsubscribe = store.subscribe(() => {
    lastState = store.getSnapshot().view?.runState || null;
  });
  fake.queueProgress(() => Promise.resolve(progressPayload()));
  store.show(ROUTE);
  await flush();
  check(lastState === "running", "subscriber sees initial facts");
  store.destroy();
  lastState = "cleared";
  fake.queueProgress(() => Promise.resolve(progressPayload()));
  store.show(ROUTE);
  await flush();
  check(lastState === "running", "existing subscriber is notified after destroy+show revival");
  unsubscribe();
  store.destroy();
}

console.log(`medicalMonitoringR7ProgressPanelController: ${passed} passed`);
