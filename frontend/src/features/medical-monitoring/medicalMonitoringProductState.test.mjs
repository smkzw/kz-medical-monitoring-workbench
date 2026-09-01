import assert from "node:assert/strict";

import {
  projectMonitoringHistory,
  projectMonitoringSetupOptions,
} from "./medicalMonitoringProductProjection.mjs";
import {
  MONITORING_NEW_RUN_ACTION_TEXT,
  MONITORING_RETURN_IN_FLIGHT_ACTION_TEXT,
  advanceMonitoringWizardStep,
  buildMonitoringPrepareAndStartPayload,
  canAdvanceMonitoringWizard,
  createMonitoringIdempotencyController,
  createMonitoringIdempotencyState,
  createMonitoringWizardState,
  handleMonitoringPrepareTimeout,
  markMonitoringPrepareAttempt,
  projectMonitoringAwayRestore,
  projectMonitoringProductState,
  projectMonitoringWizardState,
  projectMonitoringWorkbar,
  rotateMonitoringIdempotencyKey,
  selectMonitoringRun,
  setMonitoringWizardSelection,
  syncMonitoringIdempotencySelection,
} from "./medicalMonitoringProductState.mjs";

let passed = 0;
function check(condition, message) {
  assert.equal(Boolean(condition), true, message);
  passed += 1;
}

function setupPayload() {
  const mode = (name, basis, baselineOptions = []) => ({
    mode: name,
    label: name === "daily" ? "日常监查" : name === "pre_lock" ? "锁库前监查" : "核查前监查",
    description: `${name} 服务说明`,
    execution_basis_options: basis.map((value) => ({
      value,
      label: value === "full" ? "全量" : "基于上次结果分析变化",
      available: true,
      disabled_reason: "",
    })),
    default_execution_basis: basis[0],
    requires_published_same_mode_baseline: name === "daily",
    baseline_options: baselineOptions,
    available: true,
    disabled_reason: "",
    recommended: name === "daily",
    recommendation_reason: name === "daily" ? "服务端推荐" : "",
  });
  return {
    schema_version: "mm-monitoring-slice07c1-run-setup-v1",
    project_id: "project-a",
    data_batches: [{
      snapshot_token: "snapshot:current",
      data_cutoff: "2026-03-31",
      imported_at: "2026-03-31T00:00:00Z",
      scope_description: "当前完整数据",
      row_count: 12,
      can_compare: true,
    }],
    current_data: {
      snapshot_token: "snapshot:current",
      data_cutoff: "2026-03-31",
      imported_at: "2026-03-31T00:00:00Z",
      scope_description: "当前完整数据",
      row_count: 12,
      can_compare: true,
    },
    modes: [
      mode("daily", ["incremental", "full"], [{
        baseline_token: "baseline:daily:1",
        mode: "daily",
        mode_text: "日常监查",
        data_cutoff: "2026-03-01",
        published_at: "2026-03-02T00:00:00Z",
        scope_description: "同项目已发布结果",
        recommended: true,
        selectable: true,
      }]),
      mode("pre_lock", ["full"], [{
        baseline_token: "baseline:pre-lock:1",
        mode: "pre_lock",
        mode_text: "锁库前监查",
        data_cutoff: "2026-03-01",
        published_at: "2026-03-02T00:00:00Z",
        scope_description: "上一轮锁库前结果",
        recommended: true,
        selectable: true,
      }]),
      mode("post_lock_pre_cfdi", ["full"]),
    ],
    rule_revisions: [{
      project_id: "project-a",
      revision: 1,
      revision_token: "rule-revision:project-a:1",
      summary: "关注肝功能相关数据",
      applicable_scope: "所有受试者",
      starting_run: "下一次日常监查",
      selectable: true,
      recommended: true,
      created_at: "2026-03-01T00:00:00Z",
    }],
    recommended_mode: "daily",
    recommendation_reason: "服务端推荐日常监查",
  };
}

const setup = projectMonitoringSetupOptions(setupPayload(), { projectId: "project-a" });
const inFlight = {
  public_run_token: "run:active",
  mode_text: "日常监查",
  data_cutoff_text: "2026-03-31",
  comparison_range_text: "当前完整数据",
  run_state: "running",
  result_available: false,
  main_action: "查看本次进度",
  status_text: "医学监查进行中",
};
const published = {
  public_run_token: "run:published",
  mode_text: "日常监查",
  data_cutoff_text: "2026-03-01",
  comparison_range_text: "同项目已发布结果",
  run_state: "completed",
  result_available: true,
  main_action: "查看本次结果",
  status_text: "结果已整理完成",
};
const history = projectMonitoringHistory({ runs: [inFlight, published] }, { projectId: "project-a" });

const defaultSelection = selectMonitoringRun({ history });
check(defaultSelection.selectedPublicRunToken === "run:active", "default entry prefers the in-flight public run");
check(defaultSelection.selectedRun.runState === "running", "default selection retains the machine state for routing");
const explicitPublished = selectMonitoringRun({ history, selectedPublicRunToken: "run:published" });
check(explicitPublished.selectedPublicRunToken === "run:published", "explicit public run selection is preserved");
check(explicitPublished.hasOtherInFlight === true, "historical result selection notices a separate in-flight run");
check(projectMonitoringWorkbar(explicitPublished).secondaryAction === MONITORING_RETURN_IN_FLIGHT_ACTION_TEXT, "selected historical result offers return to in-flight");
check(projectMonitoringWorkbar(explicitPublished).showNewRun === false, "a separate in-flight run suppresses silent new-run switching");
const explicitResult = selectMonitoringRun({
  history,
  selectedResultContextToken: "result-context:published",
  resultContext: {
    kind: "result",
    resultContextToken: "result-context:published",
    publicRunToken: "run:published",
  },
});
check(explicitResult.selectedResultContextToken === "result-context:published", "explicit result context wins over history refresh");
check(explicitResult.selectedPublicRunToken === "run:published", "result context binds its public run");
check(selectMonitoringRun({ history, selectedResultContextToken: "result-context:missing" }).selectedPublicRunToken === "", "missing explicit context never falls back to latest history");
const unresolvedProgress = selectMonitoringRun({ history, selectedPublicRunToken: "run:outside-history-window" });
check(unresolvedProgress.unresolvedExplicitPublicRun === true, "explicit progress token is not replaced when history omits it");
check(projectMonitoringWorkbar(unresolvedProgress).mainTarget === "progress", "omitted historical rows still route to the explicit progress token");

const activeState = projectMonitoringProductState({ projectId: "project-a", options: setup, history });
check(activeState.kind === "active_run", "product state exposes active run as the product state");
const readyHistory = projectMonitoringHistory({ runs: [published] }, { projectId: "project-a" });
const resultState = projectMonitoringProductState({ projectId: "project-a", options: setup, history: readyHistory });
check(resultState.kind === "result_available", "product state exposes available result state");
check(resultState.workbar.secondaryAction === MONITORING_NEW_RUN_ACTION_TEXT, "available result exposes new-run secondary action");
const contextOnlyState = projectMonitoringProductState({
  projectId: "project-a",
  options: setup,
  history: { runs: [] },
  resultContext: {
    kind: "result",
    resultContextToken: "result-context:outside-history-window",
    publicRunToken: "run:outside-history-window",
  },
  selectedResultContextToken: "result-context:outside-history-window",
});
check(contextOnlyState.kind === "result_available", "explicit result context stays selected even outside the history window");
check(contextOnlyState.workbar.mainAction === "查看本次结果", "context-only selection never falls back to start");
const emptyState = projectMonitoringProductState({ projectId: "project-a", options: setup, history: { runs: [] } });
check(emptyState.kind === "ready" && emptyState.workbar.mainAction === "开始一次监查", "empty history exposes the start action");
check(projectMonitoringProductState({ options: null, history: null }).kind === "loading", "missing reads stay in loading state");

let wizard = createMonitoringWizardState(setup, { idempotencyKey: "nonce-1" });
check(wizard.mode === "daily", "wizard uses the server recommended mode");
check(wizard.executionBasis === "incremental", "wizard uses the server default basis");
check(wizard.baselineToken === "baseline:daily:1", "wizard uses the server recommended baseline");
check(wizard.riskRuleTokens.includes("rule-revision:project-a:1"), "wizard uses only server-recommended rules");
check(canAdvanceMonitoringWizard(wizard, setup).ok === true, "wizard server recommendation satisfies the initial selection");
wizard = setMonitoringWizardSelection(wizard, "mode", "daily", setup);
check(canAdvanceMonitoringWizard(wizard, setup).ok === true, "selected mode and server basis satisfy the first two steps");
wizard = advanceMonitoringWizardStep(wizard, setup, 1);
check(wizard.step === 2, "wizard advances one step without rewriting selections");
wizard = setMonitoringWizardSelection(wizard, "executionBasis", "full", setup);
check(wizard.baselineToken === "", "daily full analysis does not retain a prior baseline");
wizard = setMonitoringWizardSelection(wizard, "mode", "pre_lock", setup);
check(wizard.executionBasis === "full", "pre-lock mode uses its server basis");
wizard = setMonitoringWizardSelection(wizard, "baselineToken", "baseline:pre-lock:1", setup);
wizard = { ...wizard, step: 4 };
check(canAdvanceMonitoringWizard(wizard, setup).ok === true, "wizard confirmation step accepts a complete selection");
const prepare = buildMonitoringPrepareAndStartPayload(wizard, setup);
check(prepare.current_snapshot_token === "snapshot:current", "prepare payload uses the selected public snapshot token");
check(prepare.mode === "pre_lock" && prepare.execution_basis === "full", "prepare payload preserves selected mode and basis");
check(prepare.baseline_token === "baseline:pre-lock:1", "prepare payload preserves selected baseline token");
check(!Object.hasOwn(prepare, "run_id") && !Object.hasOwn(prepare, "snapshot_ref"), "prepare payload has no internal identity");
const staleWizard = setMonitoringWizardSelection(wizard, "currentSnapshotToken", "", setup);
check(staleWizard.errorText === "监查范围已更新，请重新确认", "stale snapshot keeps the frozen Chinese refresh message");
const invalidIncremental = { ...wizard, mode: "daily", executionBasis: "incremental", baselineToken: "", step: 2 };
check(canAdvanceMonitoringWizard(invalidIncremental, setup).code === "baseline_required", "incremental mode requires a selectable baseline");
const projectedWizard = projectMonitoringWizardState(wizard, setup);
check(projectedWizard.modeOptions.length === 3 && projectedWizard.summary.dataCutoffText === "2026-03-31", "wizard projection exposes server options and summary only");

const nonceValues = ["r7_first", "r7_second", "r7_third"];
const nonceFactory = () => nonceValues.shift();
let idem = createMonitoringIdempotencyState();
idem = rotateMonitoringIdempotencyKey(idem, { nonceFactory, selection: wizard });
check(idem.key === "r7_first", "idempotency key is a random client nonce");
const same = syncMonitoringIdempotencySelection(idem, wizard, { nonceFactory });
check(same.key === idem.key, "same substantive selection keeps the idempotency key");
const changedSelection = { ...wizard, baselineToken: "baseline:other" };
const rotated = syncMonitoringIdempotencySelection(same, changedSelection, { nonceFactory });
check(rotated.key === "r7_second", "mode/data/baseline/rule changes rotate the nonce");
const attempted = markMonitoringPrepareAttempt(rotated);
check(attempted.attemptCount === 1, "attempt count is local bookkeeping only");
let timeout = handleMonitoringPrepareTimeout(attempted);
check(timeout.action === "retry_same_key" && timeout.state.key === attempted.key, "tokenless timeout retries once with the same key");
timeout = handleMonitoringPrepareTimeout(timeout.state);
check(timeout.action === "surface_timeout", "second tokenless timeout does not guess from history");
timeout = handleMonitoringPrepareTimeout(timeout.state, { publicRunToken: "run:returned" });
check(timeout.action === "lookup_public_run" && timeout.publicRunToken === "run:returned", "returned public token is looked up before any retry");
check(handleMonitoringPrepareTimeout(timeout.state).action === "surface_timeout", "a returned public token disables guessing retries");
const controller = createMonitoringIdempotencyController({ nonceFactory: () => "r7_controller" });
check(controller.getState().key === "r7_controller", "idempotency controller initializes one nonce");

const returned = projectMonitoringAwayRestore({
  history,
  navigation: "return_overview",
  route: { result_context_token: "result-context:published", public_run_token: "run:published" },
});
check(returned.preservedResultContext === true, "return to overview preserves selected result context");
check(returned.selectedResultContextToken === "result-context:published", "result context survives internal overview navigation");
const reentered = projectMonitoringAwayRestore({
  history,
  navigation: "module_entry",
  route: { result_context_token: "result-context:published", public_run_token: "run:published" },
});
check(reentered.selectedPublicRunToken === "run:active", "module re-entry re-applies in-flight precedence");
check(reentered.selectedResultContextToken === "", "module re-entry clears a stale result route");

console.log(`medicalMonitoringProductState: ${passed} passed`);
