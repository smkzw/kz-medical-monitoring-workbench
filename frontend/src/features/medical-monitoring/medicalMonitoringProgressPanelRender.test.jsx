import { renderToStaticMarkup } from "react-dom/server";
import { projectMonitoringProgress } from "./medicalMonitoringProgressProjection.mjs";
import { MonitoringProgressPanelView } from "./MedicalMonitoringProgressPanel.jsx";

function payload(overrides = {}) {
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

function render(panel) {
  return renderToStaticMarkup(
    <MonitoringProgressPanelView
      panel={panel}
      onAction={() => {}}
      onRefresh={() => {}}
      onBeginStopConfirm={() => {}}
      onCancelStopConfirm={() => {}}
      confirmButtonRef={{ current: null }}
    />,
  );
}

const waitingView = projectMonitoringProgress(payload({
  completed: 0,
  percent: 0,
  progress_text: "已处理 0/8 项（0%）",
  current_work: [],
  latest_updates: [],
  run_status_text: "等待开始医学监查",
  available_actions: ["开始"],
  run_state: "waiting_start",
}));

const runningView = projectMonitoringProgress(payload());

const failedView = projectMonitoringProgress(payload({
  current_work: [],
  run_status_text: "分析服务连接异常，本项分析未完成",
  available_actions: [],
  run_state: "failed",
}));

const idlePanel = { view: null, empty: null, notice: null, actionsHidden: false, pendingAction: null, confirmStop: false };

export const renders = {
  waiting: render({ ...idlePanel, view: waitingView }),
  running: render({ ...idlePanel, view: runningView }),
  confirming: render({ ...idlePanel, view: runningView, confirmStop: true }),
  pendingAction: render({ ...idlePanel, view: waitingView, pendingAction: "start" }),
  forbidden: render({
    ...idlePanel,
    view: runningView,
    actionsHidden: true,
    notice: { kind: "forbidden", text: "当前账号不能操作本次监查运行" },
  }),
  refreshFailed: render({
    ...idlePanel,
    view: runningView,
    notice: { kind: "refresh_failed", text: "进度刷新失败，最后读取于 14:05" },
  }),
  emptyNoRun: render({ ...idlePanel, empty: { reason: "no_run", text: "尚无本次监查" } }),
  loading: render(idlePanel),
  failed: render({ ...idlePanel, view: failedView }),
};
