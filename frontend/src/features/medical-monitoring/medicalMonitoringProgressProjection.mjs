// Pure projection for the R7 live monitoring progress surface. The server
// progress payload is the only display authority; this module never invents
// numbers, never parses Chinese text to decide polling, and never derives
// state from time, tokens, or log lines.

export const R7_RUN_STATES = Object.freeze([
  "waiting_start",
  "running",
  "stopping",
  "interrupted_resumable",
  "completed",
  "ended_incomplete",
  "failed",
]);

const R7_RUN_STATE_SET = new Set(R7_RUN_STATES);

export const R7_POLLING_RUN_STATES = Object.freeze(["running", "stopping"]);
export const R7_POLL_INTERVAL_MS = 2000;
export const R7_REFRESH_BACKOFF_MS = Object.freeze([2000, 5000, 10000, 30000]);

export const R7_CURRENT_WORK_LIMIT = 3;
export const R7_LATEST_UPDATES_LIMIT = 5;

export const R7_NO_RUN_TEXT = "尚无本次监查";
export const R7_NOT_PREPARED_TEXT = "本次监查范围尚未准备";
export const R7_FORBIDDEN_ACCOUNT_TEXT = "当前账号不能操作本次监查运行";
export const R7_REFRESH_FAILED_TEXT = "进度刷新失败";
export const R7_PREPARING_NEXT_WORK_TEXT = "正在准备下一项分析";

export const R7_OUTCOME_LABELS = Object.freeze({
  stopping: "正在停止",
  interrupted_resumable: "可继续",
  completed: "已完成",
  ended_incomplete: "有未完成项",
  failed: "本项未完成",
});

// Fixed action mapping (contract §4): unknown server actions are dropped,
// never rendered as buttons.
export const R7_ACTION_ROUTES = Object.freeze({
  开始: "start",
  停止: "cancel",
  继续: "resume",
});

// User-visible copy must never contain these terms (contract §5).
export const R7_FORBIDDEN_USER_VISIBLE_TERMS = Object.freeze([
  "正式事实",
  "候选信号",
  "只读",
  "provider",
  "model",
  "selector",
  "attempt",
  "session",
  "owner",
  "lease",
  "generation",
  "invocation",
  "profile",
  "adapter",
  "hash",
  "path",
  "sqlite",
  "后端",
  "日志",
  "token",
]);

function cleanText(value) {
  return typeof value === "string" ? value.trim() : "";
}

function cleanCount(value) {
  return Number.isInteger(value) && value >= 0 ? value : 0;
}

function cleanList(value) {
  return Array.isArray(value) ? value : [];
}

export function isR7RunState(value) {
  return R7_RUN_STATE_SET.has(value);
}

export function r7PollDecision(runState) {
  const active = R7_POLLING_RUN_STATES.includes(runState);
  return Object.freeze({
    active,
    intervalMs: active ? R7_POLL_INTERVAL_MS : 0,
  });
}

export function r7RefreshBackoffMs(consecutiveFailures) {
  const failures = Number.isInteger(consecutiveFailures) && consecutiveFailures > 0
    ? consecutiveFailures
    : 1;
  return R7_REFRESH_BACKOFF_MS[Math.min(failures, R7_REFRESH_BACKOFF_MS.length) - 1];
}

// Extract the request context from the R5 canonical route state. Returns null
// when the route carries no run_ref: callers must not send a progress request
// in that case and must show the neutral empty state instead.
export function r7ProgressRequestContext(canonical) {
  const source = canonical && typeof canonical === "object" ? canonical : {};
  const projectRef = cleanText(source.project_ref);
  const runRef = cleanText(source.run_ref);
  if (!projectRef || !runRef) return null;
  return Object.freeze({ projectRef, runRef });
}

export function projectR7ProgressActions(availableActions) {
  const actions = [];
  for (const label of cleanList(availableActions)) {
    const text = cleanText(label);
    const route = R7_ACTION_ROUTES[text];
    if (route) actions.push(Object.freeze({ label: text, action: route }));
  }
  return Object.freeze(actions);
}

export function projectR7Progress(payload) {
  if (!payload || typeof payload !== "object" || Array.isArray(payload)) {
    return Object.freeze({ kind: "invalid", text: R7_REFRESH_FAILED_TEXT });
  }
  const runState = cleanText(payload.run_state);
  if (!isR7RunState(runState)) {
    return Object.freeze({ kind: "invalid", text: R7_REFRESH_FAILED_TEXT });
  }

  const completed = cleanCount(payload.completed);
  const total = cleanCount(payload.total);
  const percentRaw = typeof payload.percent === "number" && Number.isFinite(payload.percent)
    ? payload.percent
    : 0;
  const percent = Math.min(100, Math.max(0, percentRaw));

  const stageProgress = Object.freeze(cleanList(payload.stage_progress).map((stage) => {
    const row = stage && typeof stage === "object" ? stage : {};
    return Object.freeze({
      stage: cleanText(row.stage),
      processed: cleanCount(row.processed),
      total: cleanCount(row.total),
      progressText: cleanText(row.progress_text),
    });
  }));

  const currentWorkAll = cleanList(payload.current_work).map((item) => {
    const row = item && typeof item === "object" ? item : {};
    return Object.freeze({
      stage: cleanText(row.stage),
      label: cleanText(row.label),
      stateLabel: cleanText(row.state_label),
      elapsedText: cleanText(row.elapsed_text),
      message: cleanText(row.message),
    });
  });
  const currentWork = Object.freeze(currentWorkAll.slice(0, R7_CURRENT_WORK_LIMIT));
  const currentWorkRemaining = Math.max(0, currentWorkAll.length - R7_CURRENT_WORK_LIMIT);

  const selectedUpdates = cleanList(payload.latest_updates)
    .slice(0, R7_LATEST_UPDATES_LIMIT);
  const terminalLabels = new Set(
    selectedUpdates
      .filter((item) => {
        const stateLabel = cleanText(item?.state_label);
        return stateLabel === "已完成" || stateLabel === "未完成";
      })
      .map((item) => cleanText(item?.label))
      .filter(Boolean),
  );
  const latestUpdates = Object.freeze(
    selectedUpdates
      .map((item) => {
        const row = item && typeof item === "object" ? item : {};
        const label = cleanText(row.label);
        const stateLabel = cleanText(row.state_label);
        const terminal = stateLabel === "已完成" || stateLabel === "未完成";
        const historical = Boolean(label) && !terminal && terminalLabels.has(label);
        return Object.freeze({
          timeText: cleanText(row.time_text),
          stage: cleanText(row.stage),
          label,
          stateLabel,
          message: cleanText(row.message),
          historical,
        });
      }),
  );

  return Object.freeze({
    kind: "progress",
    runState,
    runStatusText: cleanText(payload.run_status_text),
    progressText: cleanText(payload.progress_text),
    outcomeLabel: R7_OUTCOME_LABELS[runState] || "",
    completed,
    total,
    percent,
    stageProgress,
    currentWork,
    currentWorkRemaining,
    currentWorkEmptyText: runState === "running" && currentWork.length === 0
      ? R7_PREPARING_NEXT_WORK_TEXT
      : "",
    latestUpdates,
    scope: Object.freeze({
      scopeVersionText: cleanText(payload.scope_version_text),
      modeText: cleanText(payload.mode_text),
      basisText: cleanText(payload.basis_text),
      dataCutoffText: cleanText(payload.data_cutoff_text),
    }),
    actions: projectR7ProgressActions(payload.available_actions),
    poll: r7PollDecision(runState),
  });
}

function errorCode(error) {
  const detail = error && typeof error === "object" ? error.detail : null;
  if (detail && typeof detail === "object" && typeof detail.code === "string") {
    return detail.code;
  }
  return "";
}

// Map failures by machine-readable code/status only; HTTP text is never
// parsed to decide the branch.
export function projectR7ProgressError(error) {
  const code = errorCode(error);
  if (code === "run_binding_not_found") {
    return Object.freeze({ kind: "empty", emptyReason: "no_run", text: R7_NO_RUN_TEXT });
  }
  if (code === "execution_not_prepared") {
    return Object.freeze({
      kind: "empty",
      emptyReason: "not_prepared",
      text: R7_NOT_PREPARED_TEXT,
    });
  }
  const status = Number(error?.status) || 0;
  // Only HTTP responses carry server-reviewed Chinese copy; raw fetch
  // rejections never reach the view.
  const serverText = status > 0 ? cleanText(error?.message) : "";
  if (status === 403) {
    return Object.freeze({
      kind: "forbidden",
      text: R7_FORBIDDEN_ACCOUNT_TEXT,
      serverText,
    });
  }
  return Object.freeze({
    kind: "error",
    text: serverText || R7_REFRESH_FAILED_TEXT,
  });
}

// Late-response guard: a ticket is accepted only while it is the most recent
// begin() for the same project/run identity. Project or run switches and
// reset() invalidate every earlier ticket, so stale responses never reach
// the current view.
export function createR7ProgressGate() {
  let epoch = 0;
  let identity = "";
  return Object.freeze({
    begin({ projectRef, runRef } = {}) {
      identity = `${cleanText(projectRef)}‱${cleanText(runRef)}`;
      epoch += 1;
      return Object.freeze({ epoch, identity });
    },
    accept(ticket) {
      return Boolean(ticket)
        && ticket.epoch === epoch
        && ticket.identity === identity
        && identity !== "‱";
    },
    reset() {
      epoch += 1;
      identity = "";
    },
  });
}

export function collectR7UserVisibleTexts(view) {
  if (!view || typeof view !== "object") return [];
  const texts = [];
  const push = (value) => {
    const text = cleanText(value);
    if (text) texts.push(text);
  };
  push(view.text);
  push(view.runStatusText);
  push(view.progressText);
  push(view.currentWorkEmptyText);
  for (const stage of view.stageProgress || []) {
    push(stage.stage);
    push(stage.progressText);
  }
  for (const item of view.currentWork || []) {
    push(item.stage);
    push(item.label);
    push(item.stateLabel);
    push(item.elapsedText);
    push(item.message);
  }
  for (const update of view.latestUpdates || []) {
    push(update.timeText);
    push(update.stage);
    push(update.label);
    push(update.stateLabel);
    push(update.message);
  }
  if (view.scope) {
    push(view.scope.scopeVersionText);
    push(view.scope.modeText);
    push(view.scope.basisText);
    push(view.scope.dataCutoffText);
  }
  for (const action of view.actions || []) push(action.label);
  return texts;
}

export function findR7ForbiddenTerms(texts) {
  const hits = [];
  for (const text of cleanList(texts)) {
    const haystack = String(text).toLowerCase();
    for (const term of R7_FORBIDDEN_USER_VISIBLE_TERMS) {
      if (haystack.includes(term.toLowerCase())) {
        hits.push(Object.freeze({ term, text: String(text) }));
      }
    }
  }
  return Object.freeze(hits);
}
