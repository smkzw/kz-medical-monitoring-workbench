import assert from "node:assert/strict";
import { parseMedicalMonitoringWorkspaceRouteState } from "./medicalMonitoringWorkspaceRouteState.mjs";
import {
  MONITORING_FORBIDDEN_ACCOUNT_TEXT,
  MONITORING_FORBIDDEN_USER_VISIBLE_TERMS,
  MONITORING_NOT_PREPARED_TEXT,
  MONITORING_NO_RUN_TEXT,
  MONITORING_PREPARING_NEXT_WORK_TEXT,
  MONITORING_REFRESH_FAILED_TEXT,
  MONITORING_RUN_STATES,
  collectMonitoringUserVisibleTexts,
  createMonitoringProgressGate,
  findMonitoringForbiddenTerms,
  projectMonitoringProgress,
  projectMonitoringProgressActions,
  projectMonitoringProgressError,
  monitoringPollDecision,
  monitoringProgressRequestContext,
  monitoringRefreshBackoffMs,
} from "./medicalMonitoringProgressProjection.mjs";

let passed = 0;
function check(condition, message) {
  assert.ok(condition, message);
  passed += 1;
}

function progressPayload(overrides = {}) {
  return {
    scope_version_text: "第 2 版监查范围",
    mode_text: "日常监查",
    basis_text: "增量",
    data_cutoff_text: "2026-08-28",
    headline: "医学监查进行中",
    completed: 3,
    total: 8,
    percent: 37.5,
    progress_text: "已处理 3/8 项（37.5%）",
    status_overview: [{ state_label: "已完成", count: 3 }],
    stage_progress: [
      { stage: "数据核查", processed: 2, total: 3, progress_text: "已处理 2/3 项" },
      { stage: "医学审阅", processed: 1, total: 5, progress_text: "已处理 1/5 项" },
    ],
    current_work: [
      { stage: "医学审阅", label: "审阅实验室异常", state_label: "进行中", elapsed_text: "约 2 分钟", message: "正在进行：审阅实验室异常" },
      { stage: "医学审阅", label: "核对合并用药", state_label: "进行中", elapsed_text: "约 1 分钟", message: "正在进行：核对合并用药" },
      { stage: "医学审阅", label: "核对病史记录", state_label: "进行中", elapsed_text: "约 1 分钟", message: "正在进行：核对病史记录" },
      { stage: "医学审阅", label: "核对访视日期", state_label: "进行中", elapsed_text: "约 1 分钟", message: "正在进行：核对访视日期" },
    ],
    latest_updates: [
      { time_text: "10:31", stage: "数据核查", label: "核查入排标准", state_label: "已完成", message: "已完成：核查入排标准" },
      { time_text: "10:30", stage: "数据核查", label: "核查实验室检查", state_label: "已完成", message: "已完成：核查实验室检查" },
      { time_text: "10:29", stage: "数据核查", label: "核查生命体征", state_label: "已完成", message: "已完成：核查生命体征" },
      { time_text: "10:28", stage: "医学审阅", label: "审阅不良事件", state_label: "已完成", message: "已完成：审阅不良事件" },
      { time_text: "10:27", stage: "医学审阅", label: "审阅合并用药", state_label: "已完成", message: "已完成：审阅合并用药" },
      { time_text: "10:26", stage: "医学审阅", label: "审阅病史", state_label: "进行中", message: "正在进行：审阅病史" },
    ],
    run_status_text: "医学监查进行中",
    available_actions: ["停止"],
    run_state: "running",
    ...overrides,
  };
}

function apiError({ status = 500, code = "", message = "" } = {}) {
  const error = new Error(message);
  error.status = status;
  error.detail = code ? { code, message } : null;
  return error;
}

// --- run_state authority and polling decisions -------------------------------

const running = projectMonitoringProgress(progressPayload());
check(running.kind === "progress", "valid payload projects to a progress view");
check(running.runState === "running", "keeps the machine-readable run state");
check(running.poll.active === true && running.poll.intervalMs === 2000, "running polls every 2s");

const stopping = projectMonitoringProgress(progressPayload({
  run_state: "stopping",
  run_status_text: "正在停止，当前分析可能完成；系统不会开始下一项工作。",
  available_actions: [],
}));
check(stopping.poll.active === true && stopping.poll.intervalMs === 2000, "stopping keeps polling until the server transitions");
check(stopping.actions.length === 0, "stopping renders no actions");

for (const state of ["waiting_start", "interrupted_resumable", "completed", "ended_incomplete", "failed"]) {
  check(monitoringPollDecision(state).active === false, `${state} does not poll continuously`);
}
check(MONITORING_RUN_STATES.length === 7, "run_state vocabulary stays at the contracted seven values");

check(
  projectMonitoringProgress(progressPayload({ run_state: "almost_done" })).kind === "invalid",
  "unknown run_state never reaches the view",
);
check(projectMonitoringProgress(null).kind === "invalid", "non-object payload projects invalid");
check(projectMonitoringProgress([1, 2]).kind === "invalid", "array payload projects invalid");
check(
  projectMonitoringProgress(progressPayload({ run_state: undefined })).kind === "invalid",
  "missing run_state projects invalid instead of guessing",
);

// --- field-level projection ---------------------------------------------------

check(running.progressText === "已处理 3/8 项（37.5%）", "headline numbers come from server progress_text");
check(running.outcomeLabel === "", "running does not invent a terminal outcome badge");
check(running.percent === 37.5 && running.completed === 3 && running.total === 8, "keeps server counts and percent");
check(running.stageProgress.length === 2, "keeps stage order from the server");
check(running.stageProgress[0].progressText === "已处理 2/3 项", "stage text is server text");
check(running.scope.modeText === "日常监查" && running.scope.basisText === "增量", "keeps scope metadata");
check(running.scope.dataCutoffText === "2026-08-28", "keeps the data cutoff text");

check(running.currentWork.length === 3, "current work is capped at three items");
check(running.currentWorkRemaining === 1, "overflow is exposed for the 另有 N 项 hint");
check(running.latestUpdates.length === 5, "latest updates are capped at five items");
check(
  running.latestUpdates.map((u) => u.timeText).join(",") === "10:31,10:30,10:29,10:28,10:27",
  "latest updates keep the server order without re-sorting",
);

const emptyWork = projectMonitoringProgress(progressPayload({ current_work: [] }));
check(
  emptyWork.currentWorkEmptyText === MONITORING_PREPARING_NEXT_WORK_TEXT,
  "running without current work shows the neutral preparing hint",
);
const waitingWork = projectMonitoringProgress(progressPayload({
  run_state: "waiting_start",
  run_status_text: "等待开始医学监查",
  available_actions: ["开始"],
  current_work: [],
}));
check(waitingWork.currentWorkEmptyText === "", "waiting start shows no fabricated current-work hint");

const failedOutcome = projectMonitoringProgress(progressPayload({
  run_state: "failed",
  run_status_text: "分析服务连接异常，本项分析未完成。",
  available_actions: [],
}));
check(failedOutcome.outcomeLabel === "本项未完成", "failed exposes a prominent non-completion label");

// --- missing fields degrade without invented numbers --------------------------

const sparse = projectMonitoringProgress({ run_state: "completed" });
check(sparse.kind === "progress", "missing optional fields still project");
check(sparse.completed === 0 && sparse.total === 0 && sparse.percent === 0, "missing counts are zero, never extrapolated");
check(sparse.progressText === "" && sparse.runStatusText === "", "missing texts stay empty for the caller to neutralize");
check(sparse.stageProgress.length === 0 && sparse.latestUpdates.length === 0, "missing lists are empty");
check(sparse.actions.length === 0, "missing actions render nothing");

const overflow = projectMonitoringProgress(progressPayload({ percent: 140 }));
check(overflow.percent === 100, "percent is clamped for the accessible progressbar range");

// --- action mapping -------------------------------------------------------------

const actions = projectMonitoringProgressActions(["开始", "停止", "继续"]);
check(
  actions.map((a) => a.action).join(",") === "start,cancel,resume",
  "开始/停止/继续 map to start/cancel/resume",
);
check(actions[0].label === "开始", "action labels stay in Chinese");
const filtered = projectMonitoringProgressActions(["停止", "暂停", "", 42, null]);
check(filtered.length === 1 && filtered[0].action === "cancel", "unrecognized actions never become buttons");
check(projectMonitoringProgressActions(undefined).length === 0, "missing action list maps to none");

// --- route run_ref context ------------------------------------------------------

const route = parseMedicalMonitoringWorkspaceRouteState(
  "?view=overview&project_id=proj/01&run_id=run 07&snapshot_id=snap/1&cutoff=2026-08-28&scope=trial",
);
check(route.valid, "route fixture parses as a valid R5 route");
const context = monitoringProgressRequestContext(route.canonical);
check(context?.projectRef === "proj/01" && context?.runRef === "run 07", "run identity comes from the route run_ref");

const noRun = parseMedicalMonitoringWorkspaceRouteState("?view=overview&project_id=proj/01");
check(monitoringProgressRequestContext(noRun.canonical) === null, "missing run_ref yields no request context");
check(monitoringProgressRequestContext(null) === null, "absent route state yields no request context");
check(
  monitoringProgressRequestContext({ project_ref: "p", run_ref: "  " }) === null,
  "blank run_ref yields no request context",
);

// --- late responses -------------------------------------------------------------

const gate = createMonitoringProgressGate();
const first = gate.begin({ projectRef: "p1", runRef: "r1" });
check(gate.accept(first), "the current ticket is accepted");
const second = gate.begin({ projectRef: "p1", runRef: "r1" });
check(gate.accept(second), "the newer same-identity ticket is accepted");
check(!gate.accept(first), "a superseded ticket is rejected as a late response");
const otherRun = gate.begin({ projectRef: "p1", runRef: "r2" });
check(gate.accept(otherRun), "the ticket for the new run is accepted");
check(!gate.accept(second), "tickets from the previous run are rejected after run switch");
const otherProject = gate.begin({ projectRef: "p2", runRef: "r2" });
check(!gate.accept(otherRun), "tickets from the previous project are rejected after project switch");
check(gate.accept(otherProject), "the new project ticket is accepted");
gate.reset();
check(!gate.accept(otherProject), "reset invalidates every outstanding ticket");
check(!gate.accept(null), "missing tickets are rejected");

// --- error-code empty states ------------------------------------------------------

const noBinding = projectMonitoringProgressError(apiError({
  status: 404,
  code: "run_binding_not_found",
  message: "未找到指定的监查运行绑定。",
}));
check(noBinding.kind === "empty" && noBinding.text === MONITORING_NO_RUN_TEXT, "run_binding_not_found maps to the neutral no-run empty state");

const notPrepared = projectMonitoringProgressError(apiError({
  status: 409,
  code: "execution_not_prepared",
  message: "请先准备本次监查工作范围。",
}));
check(notPrepared.kind === "empty" && notPrepared.text === MONITORING_NOT_PREPARED_TEXT, "execution_not_prepared maps to the not-prepared empty state");
check(noBinding.kind === "empty" && noBinding.text !== notPrepared.text, "the two empty states stay distinct");

const forbidden = projectMonitoringProgressError(apiError({
  status: 403,
  code: "not_permitted",
  message: "当前身份无权执行该医学监查 R7 操作。",
}));
check(forbidden.kind === "forbidden" && forbidden.text === MONITORING_FORBIDDEN_ACCOUNT_TEXT, "403 maps to the fixed account message");

const integrity = projectMonitoringProgressError(apiError({
  status: 422,
  code: "runtime_integrity_failed",
  message: "本次监查进度无法核对，已阻断。",
}));
check(integrity.kind === "error" && integrity.text === "本次监查进度无法核对，已阻断。", "other failures surface the server Chinese text");

const silent = projectMonitoringProgressError(apiError({ status: 0, code: "", message: "" }));
check(silent.kind === "error" && silent.text === MONITORING_REFRESH_FAILED_TEXT, "failures without server text fall back to the neutral refresh failure");
check(
  projectMonitoringProgressError(new Error("network down")).text === MONITORING_REFRESH_FAILED_TEXT,
  "network failures fall back to the neutral refresh failure",
);
check(
  projectMonitoringProgressError(apiError({ status: 404, code: "", message: "Not Found" })).kind === "error",
  "HTTP status alone never decides the empty branch",
);

// --- retry backoff -----------------------------------------------------------------

check(monitoringRefreshBackoffMs(1) === 2000, "first failure waits 2s");
check(monitoringRefreshBackoffMs(2) === 5000, "second failure waits 5s");
check(monitoringRefreshBackoffMs(3) === 10000, "third failure waits 10s");
check(monitoringRefreshBackoffMs(4) === 30000, "fourth failure waits 30s");
check(monitoringRefreshBackoffMs(12) === 30000, "backoff clamps at 30s");
check(monitoringRefreshBackoffMs(0) === 2000, "non-positive counts start the sequence");

// --- forbidden-term scan across every state branch ----------------------------------

const branchPayloads = [
  progressPayload({ run_state: "waiting_start", run_status_text: "等待开始医学监查", available_actions: ["开始"], completed: 0, percent: 0, progress_text: "已处理 0/8 项（0%）", current_work: [], latest_updates: [] }),
  progressPayload(),
  progressPayload({ run_state: "stopping", run_status_text: "正在停止，当前分析可能完成；系统不会开始下一项工作。", available_actions: [] }),
  progressPayload({ run_state: "interrupted_resumable", run_status_text: "分析已中断，可继续本次监查。", available_actions: ["继续"], current_work: [] }),
  progressPayload({ run_state: "interrupted_resumable", run_status_text: "已停止，可继续", available_actions: ["继续"], current_work: [] }),
  progressPayload({ run_state: "interrupted_resumable", run_status_text: "本项分析未完成，已达到本次重试上限。", available_actions: ["继续"], current_work: [] }),
  progressPayload({ run_state: "completed", run_status_text: "本次监查已完成", available_actions: [], completed: 8, percent: 100, progress_text: "已处理 8/8 项（100%）", current_work: [] }),
  progressPayload({ run_state: "ended_incomplete", run_status_text: "本次监查已结束，部分工作未完成", available_actions: [], current_work: [] }),
  progressPayload({ run_state: "failed", run_status_text: "分析服务连接异常，本项分析未完成。", available_actions: [], current_work: [] }),
  progressPayload({ run_state: "failed", run_status_text: "本项分析未完成，已达到本次重试上限。", available_actions: [], current_work: [] }),
];
check(branchPayloads.length === 10, "scan fixtures cover every state incl. retry-exhausted branches");

const scannedViews = [
  ...branchPayloads.map((payload) => projectMonitoringProgress(payload)),
  noBinding,
  notPrepared,
  forbidden,
  integrity,
  silent,
];
const scannedTexts = scannedViews.flatMap((view) => collectMonitoringUserVisibleTexts(view));
check(scannedTexts.length > 0, "the scan actually collected user-visible texts");
const hits = findMonitoringForbiddenTerms(scannedTexts);
check(hits.length === 0, `no forbidden user-visible terms across branches: ${JSON.stringify(hits)}`);

const dirty = findMonitoringForbiddenTerms(["后端 token 已轮换", "使用 provider 配置"]);
check(
  dirty.map((hit) => hit.term).join(",") === "后端,token,provider",
  "the scanner reports every forbidden term per text",
);
check(
  findMonitoringForbiddenTerms(["MODEL"].map((t) => t)).length === 1,
  "the scanner matches latin terms case-insensitively",
);
check(MONITORING_FORBIDDEN_USER_VISIBLE_TERMS.length === 20, "the forbidden vocabulary matches contract §5");

const staticCopyHits = findMonitoringForbiddenTerms([
  MONITORING_NO_RUN_TEXT,
  MONITORING_NOT_PREPARED_TEXT,
  MONITORING_FORBIDDEN_ACCOUNT_TEXT,
  MONITORING_REFRESH_FAILED_TEXT,
  MONITORING_PREPARING_NEXT_WORK_TEXT,
]);
check(staticCopyHits.length === 0, "the projection's own static copy is free of forbidden terms");

console.log(`medicalMonitoringProgressProjection: ${passed} passed`);
