import {
  R7_COMPARISON_UNAVAILABLE_TEXT,
  R7_OPTIONS_REFRESH_TEXT,
  R7_PRODUCT_IN_FLIGHT_STATES,
  R7_PRODUCT_MODES,
  R7_PRODUCT_STATE_KINDS,
  R7_PUBLIC_RESULT_UNAVAILABLE_TEXT,
  isR7InFlightRunState,
  projectR7History,
  projectR7ResultContext,
} from "./medicalMonitoringR7ProductProjection.mjs";

export const R7_WIZARD_STEP_COUNT = 4;
export const R7_WIZARD_STEPS = Object.freeze([
  Object.freeze({ number: 1, key: "mode", label: "选择监查方式" }),
  Object.freeze({ number: 2, key: "scope", label: "确认数据范围" }),
  Object.freeze({ number: 3, key: "rules", label: "选择特殊关注" }),
  Object.freeze({ number: 4, key: "confirm", label: "确认并开始" }),
]);

export const R7_START_ACTION_TEXT = "开始一次监查";
export const R7_HISTORY_ACTION_TEXT = "查看历史";
export const R7_PROGRESS_ACTION_TEXT = "查看本次进度";
export const R7_RESULT_ACTION_TEXT = "查看本次结果";
export const R7_NEW_RUN_ACTION_TEXT = "开始一次新的监查";
export const R7_RETURN_IN_FLIGHT_ACTION_TEXT = "返回正在进行的监查";

const IN_FLIGHT_SET = new Set(R7_PRODUCT_IN_FLIGHT_STATES);
const MODE_SET = new Set(R7_PRODUCT_MODES);

function isRecord(value) {

  return value !== null && typeof value === "object" && !Array.isArray(value);
}

function text(value) {
  return typeof value === "string" ? value.trim() : "";
}
function safeServerText(error) {
  const message = text(error?.message || error?.text || (typeof error === "string" ? error : ""));
  const status = Number(error?.status) || 0;
  return status > 0 && /[\u4e00-\u9fff]/u.test(message) ? message : "";
}

function clone(value) {
  if (Array.isArray(value)) return value.map(clone);
  if (isRecord(value)) return Object.fromEntries(Object.entries(value).map(([key, item]) => [key, clone(item)]));
  return value;
}

function freeze(value) {
  if (Array.isArray(value)) value.forEach((item) => freeze(item));
  else if (isRecord(value)) Object.values(value).forEach((item) => freeze(item));
  return Object.freeze(value);
}

function rowValue(row, camel, snake, fallback = "") {
  if (!isRecord(row)) return fallback;
  const value = row[camel] !== undefined ? row[camel] : row[snake];
  return value === null || value === undefined ? fallback : value;
}

function rowModel(row) {
  if (!isRecord(row)) return null;
  const publicRunToken = text(rowValue(row, "publicRunToken", "public_run_token"));
  if (!publicRunToken) return null;
  const runState = text(rowValue(row, "runState", "run_state"));
  return freeze({
    publicRunToken,
    modeText: text(rowValue(row, "modeText", "mode_text")),
    dataCutoffText: text(rowValue(row, "dataCutoffText", "data_cutoff_text")),
    comparisonRangeText: text(rowValue(row, "comparisonRangeText", "comparison_range_text")),
    runState,
    resultAvailable: rowValue(row, "resultAvailable", "result_available") === true,
    mainAction: text(rowValue(row, "mainAction", "main_action")),
    statusText: text(rowValue(row, "statusText", "status_text")),
  });
}

function runRows(history, runs) {
  const source = Array.isArray(runs)
    ? runs
    : Array.isArray(history?.rows)
      ? history.rows
      : Array.isArray(history?.runs)
        ? history.runs
        : [];
  return source.map(rowModel).filter(Boolean);
}

function inFlightRows(rows) {
  return rows.filter((row) => IN_FLIGHT_SET.has(row.runState));
}

function unpublishedClosureRows(rows) {
  return rows.filter((row) => row.runState === "completed" && !row.resultAvailable);
}

function latestAvailableRow(rows) {
  return rows.find((row) => row.resultAvailable) || null;
}

function selectedResultToken(input) {
  return text(
    input?.selectedResultContextToken
      || input?.resultContextToken
      || input?.route?.result_context_token
      || input?.route?.resultContextToken,
  );
}

function selectedRunToken(input) {
  return text(
    input?.selectedPublicRunToken
      || input?.publicRunToken
      || input?.route?.public_run_token
      || input?.route?.publicRunToken,
  );
}

function contextPublicRunToken(context) {
  return text(
    context?.publicRunToken
      || context?.identity?.public_run_token
      || context?.identity?.publicRunToken,
  );
}

/**
 * Select one public run without ever allowing a latest-history refresh to
 * replace an explicitly opened result context. Only public run/result tokens
 * enter this model; internal run/snapshot/cutoff identities are not accepted.
 */
export function selectR7Run(input = {}) {
  const rows = runRows(input.history, input.runs);
  const explicitResultToken = selectedResultToken(input);
  const context = input.resultContext && input.resultContext.kind !== "invalid"
    ? input.resultContext
    : null;
  const contextToken = context?.resultContextToken
    || context?.result_context_token
    || explicitResultToken;
  const contextRunToken = contextPublicRunToken(context);
  const explicitRunToken = selectedRunToken(input) || contextRunToken;
  let selectedRun = null;
  let selectionSource = "default";

  if (contextToken) {
    selectionSource = "route_result_context";
    selectedRun = rows.find((row) => row.publicRunToken === explicitRunToken) || null;
  } else if (explicitRunToken) {
    selectionSource = "explicit_public_run";
    selectedRun = rows.find((row) => row.publicRunToken === explicitRunToken) || null;
  } else {
    const active = inFlightRows(rows)[0] || unpublishedClosureRows(rows)[0];
    selectedRun = active || latestAvailableRow(rows);
    selectionSource = selectedRun
      ? (isR7InFlightRunState(selectedRun.runState) || !selectedRun.resultAvailable
        ? "default_in_flight"
        : "default_latest_result")
      : "default_empty";
  }

  const activeRows = inFlightRows(rows);
  const selectedToken = selectedRun?.publicRunToken || explicitRunToken || contextRunToken;
  const otherInFlight = activeRows.find((row) => row.publicRunToken !== selectedToken) || null;
  const selectedIsPublished = Boolean(
    (contextToken && context)
      || selectedRun?.resultAvailable,
  );
  return freeze({
    kind: "selection",
    rows: freeze(rows),
    selectedRun,
    selectedPublicRunToken: selectedToken,
    selectedResultContextToken: contextToken,
    selectedResultContext: context,
    selectionSource,
    explicitPublicRunToken: Boolean(explicitRunToken),
    unresolvedExplicitPublicRun: Boolean(explicitRunToken && !selectedRun && !contextToken),
    inFlightRun: activeRows[0] || null,
    hasInFlight: activeRows.length > 0,
    otherInFlightRun: selectedIsPublished ? otherInFlight : null,
    hasOtherInFlight: Boolean(selectedIsPublished && otherInFlight),
    returnInFlightAction: selectedIsPublished && otherInFlight ? R7_RETURN_IN_FLIGHT_ACTION_TEXT : "",
  });
}

export const projectR7SelectedRun = selectR7Run;
export const projectR7RunSelection = selectR7Run;

function selectedIsActive(selection) {
  const run = selection?.selectedRun;
  return Boolean(run && (isR7InFlightRunState(run.runState) || (run.runState === "completed" && !run.resultAvailable)));
}

/**
 * Work-bar action matrix. A selected run's main action is always copied from
 * the server history row; this function never translates run_state into a
 * replacement main label.
 */
export function projectR7Workbar(selectionOrInput = {}) {
  const selection = selectionOrInput?.kind === "selection"
    ? selectionOrInput
    : selectR7Run(selectionOrInput);
  const selectedRun = selection.selectedRun;
  if (!selectedRun && selection.unresolvedExplicitPublicRun) {
    return freeze({
      kind: "workbar",
      mainAction: R7_PROGRESS_ACTION_TEXT,
      mainTarget: "progress",
      secondaryAction: R7_HISTORY_ACTION_TEXT,
      secondaryTarget: "history",
      otherAction: "",
      otherTarget: "",
      showNewRun: false,
      selectedPublicRunToken: selection.selectedPublicRunToken || "",
      selectedResultContextToken: "",
    });
  }
  if (!selectedRun && selection.selectedResultContext) {
    return freeze({
      kind: "workbar",
      mainAction: R7_RESULT_ACTION_TEXT,
      mainTarget: "result",
      secondaryAction: selection.hasOtherInFlight ? R7_RETURN_IN_FLIGHT_ACTION_TEXT : "",
      secondaryTarget: selection.hasOtherInFlight ? "progress" : "",
      otherAction: R7_HISTORY_ACTION_TEXT,
      otherTarget: "history",
      showNewRun: false,
      selectedPublicRunToken: selection.selectedPublicRunToken || "",
      selectedResultContextToken: selection.selectedResultContextToken || "",
    });
  }
  if (!selectedRun) {
    return freeze({
      kind: "workbar",
      mainAction: R7_START_ACTION_TEXT,
      mainTarget: "wizard",
      secondaryAction: R7_HISTORY_ACTION_TEXT,
      secondaryTarget: "history",
      otherAction: "",
      otherTarget: "",
      showNewRun: true,
      selectedPublicRunToken: selection.selectedPublicRunToken || "",
      selectedResultContextToken: selection.selectedResultContextToken || "",
    });
  }
  const active = selectedIsActive(selection);
  const published = Boolean(
    selectedRun.resultAvailable
      || (selection.selectedResultContext && selection.selectedResultContext.kind === "result"),
  );
  const workbar = {
    kind: "workbar",
    // Server-owned. Empty means malformed history and is not repaired here.
    mainAction: selectedRun.mainAction,
    mainTarget: active ? "progress" : published ? "result" : "progress",
    secondaryAction: "",
    secondaryTarget: "",
    otherAction: R7_HISTORY_ACTION_TEXT,
    otherTarget: "history",
    showNewRun: false,
    selectedPublicRunToken: selectedRun.publicRunToken,
    selectedResultContextToken: selection.selectedResultContextToken || "",
  };
  if (published) {
    if (selection.hasOtherInFlight) {
      workbar.secondaryAction = R7_RETURN_IN_FLIGHT_ACTION_TEXT;
      workbar.secondaryTarget = "progress";
    } else {
      workbar.secondaryAction = R7_NEW_RUN_ACTION_TEXT;
      workbar.secondaryTarget = "wizard";
      workbar.showNewRun = true;
    }
  }
  return freeze(workbar);
}

export const projectR7MonitoringWorkbar = projectR7Workbar;

function normalizeOptions(options, projectId) {
  if (options?.kind === "setup") return options;
  const projected = projectR7SetupOptions(options, { projectId });
  return projected.kind === "setup" ? projected : null;
}

function normalizeHistory(history, projectId) {
  if (history?.kind === "history") return history;
  const projected = projectR7History(history, { projectId });
  return projected.kind === "history" ? projected : null;
}

export function projectR7ProductState({
  projectId = "",
  options = null,
  history = null,
  resultContext = null,
  selectedPublicRunToken = "",
  selectedResultContextToken = "",
  route = null,
  loading = false,
  optionsLoading = false,
  historyLoading = false,
  error = null,
} = {}) {
  const routeResultToken = text(
    selectedResultContextToken
      || route?.result_context_token
      || route?.resultContextToken,
  );
  if (loading || optionsLoading || historyLoading || options === null || history === null) {
    return freeze({
      kind: "loading",
      status: "loading",
      selectedRun: null,
      workbar: null,
      error: "",
    });
  }
  const setup = normalizeOptions(options, projectId);
  const runs = normalizeHistory(history, projectId);
  const resolvedResultContext = resultContext?.kind === "result"
    ? resultContext
    : resultContext
      ? projectR7ResultContext(resultContext, {
        projectId,
        resultContextToken: routeResultToken,
      })
      : null;
  if (
    !setup
    || !runs
    || error
    || resolvedResultContext?.kind === "invalid"
    || (routeResultToken && !resolvedResultContext)
  ) {
    if (routeResultToken && !resultContext && !error && setup && runs) {
      return freeze({
        kind: "loading",
        status: "loading",
        selectedRun: null,
        workbar: null,
        error: "",
      });
    }
    return freeze({
      kind: "unavailable",
      selectedRun: null,
      workbar: null,
      error: safeServerText(error) || R7_PUBLIC_RESULT_UNAVAILABLE_TEXT,
    });
  }
  const selection = selectR7Run({
    history: runs,
    resultContext: resolvedResultContext,
    selectedPublicRunToken,
    selectedResultContextToken,
    route,
  });
  const workbar = projectR7Workbar(selection);
  const resultSelected = Boolean(
    resolvedResultContext?.kind === "result"
      || selection.selectedRun?.resultAvailable,
  );
  const activeSelected = selectedIsActive(selection) || selection.unresolvedExplicitPublicRun;
  const kind = resultSelected
    ? "result_available"
    : activeSelected
      ? "active_run"
      : "ready";
  if (!R7_PRODUCT_STATE_KINDS.includes(kind)) {
    return freeze({ kind: "unavailable", status: "unavailable", selectedRun: null, workbar: null, error: R7_PUBLIC_RESULT_UNAVAILABLE_TEXT });
  }
  return freeze({
    kind,
    status: kind,
    projectId: text(projectId) || setup.projectId,
    options: setup,
    history: runs,
    selection,
    selectedRun: selection.selectedRun,
    selectedPublicRunToken: selection.selectedPublicRunToken,
    selectedResultContextToken: selection.selectedResultContextToken,
    resultContext: resolvedResultContext?.kind === "result" ? resolvedResultContext : null,
    workbar,
    error: "",
  });
}

export const projectR7MonitoringState = projectR7ProductState;

function modeOption(state, setup) {
  return setup?.modes?.find((item) => item.mode === state.mode) || null;
}

function validBasisOption(option, basis) {
  return Boolean(option?.executionBasisOptions?.some((item) => item.value === basis && item.available));
}

function selectableBaseline(option, token) {
  return option?.baselineOptions?.find((item) => item.baselineToken === token && item.selectable) || null;
}

function recommendedBaseline(option) {
  return option?.baselineOptions?.find((item) => item.recommended && item.selectable)
    || option?.baselineOptions?.find((item) => item.selectable)
    || null;
}

function initialRuleTokens(setup) {
  return (setup?.ruleRevisions || [])
    .filter((item) => item.selectable && item.recommended)
    .map((item) => item.revisionToken);
}

function stateSelection(state) {
  return {
    mode: text(state?.mode),
    executionBasis: text(state?.executionBasis),
    currentSnapshotToken: text(state?.currentSnapshotToken),
    baselineToken: text(state?.baselineToken),
    riskRuleTokens: [...new Set((Array.isArray(state?.riskRuleTokens) ? state.riskRuleTokens : []).map(text).filter(Boolean))].sort(),
  };
}

function idempotencySelectionEqual(left, right) {
  const a = stateSelection(left);
  const b = stateSelection(right);
  return a.mode === b.mode
    && a.executionBasis === b.executionBasis
    && a.currentSnapshotToken === b.currentSnapshotToken
    && a.baselineToken === b.baselineToken
    && JSON.stringify(a.riskRuleTokens) === JSON.stringify(b.riskRuleTokens);
}

export function createR7WizardState(options, initial = {}) {
  const setup = normalizeOptions(options, initial.projectId);
  const modeFromInput = text(initial.mode);
  const recommendedMode = text(setup?.recommendedMode);
  const mode = MODE_SET.has(modeFromInput)
    && setup?.modes?.some((item) => item.mode === modeFromInput && item.available)
    ? modeFromInput
    : MODE_SET.has(recommendedMode)
      && setup?.modes?.some((item) => item.mode === recommendedMode && item.available)
        ? recommendedMode
        : "";
  const option = setup?.modes?.find((item) => item.mode === mode) || null;
  const basisInput = text(initial.executionBasis);
  const executionBasis = validBasisOption(option, basisInput)
    ? basisInput
    : text(option?.defaultExecutionBasis);
  const baselineInput = text(initial.baselineToken);
  const baseline = selectableBaseline(option, baselineInput)
    || (mode === "daily" && executionBasis === "incremental" ? recommendedBaseline(option) : null);
  const currentToken = text(initial.currentSnapshotToken)
    || text(setup?.currentData?.snapshotToken);
  const selectedRules = Array.isArray(initial.riskRuleTokens)
    ? [...new Set(initial.riskRuleTokens.map(text).filter(Boolean))]
    : initial.riskRuleTokens === undefined
      ? initialRuleTokens(setup)
      : [];
  return freeze({
    kind: "wizard",
    projectId: text(initial.projectId) || text(setup?.projectId),
    step: Number.isInteger(initial.step) && initial.step >= 1 && initial.step <= R7_WIZARD_STEP_COUNT ? initial.step : 1,
    stepCount: R7_WIZARD_STEP_COUNT,
    mode,
    executionBasis,
    currentSnapshotToken: currentToken,
    baselineToken: baseline?.baselineToken || "",
    riskRuleTokens: selectedRules,
    preview: isRecord(initial.preview) ? clone(initial.preview) : null,
    previewCandidateId: text(initial.previewCandidateId),
    idempotencyKey: text(initial.idempotencyKey),
    timeoutRetryUsed: initial.timeoutRetryUsed === true,
    errorCode: "",
    errorText: "",
  });
}

export function projectR7WizardState(state, options) {
  const setup = normalizeOptions(options, state?.projectId);
  if (!setup || !isRecord(state)) {
    return freeze({ kind: "invalid", status: "invalid", text: R7_OPTIONS_REFRESH_TEXT });
  }
  const wizard = freeze({
    ...state,
    kind: "wizard",
    projectId: text(state.projectId) || text(setup.projectId),
    step: Number.isInteger(state.step) && state.step >= 1 && state.step <= R7_WIZARD_STEP_COUNT
      ? state.step
      : 1,
    stepCount: R7_WIZARD_STEP_COUNT,
    mode: text(state.mode),
    executionBasis: text(state.executionBasis),
    currentSnapshotToken: text(state.currentSnapshotToken),
    baselineToken: text(state.baselineToken),
    riskRuleTokens: Array.isArray(state.riskRuleTokens)
      ? [...new Set(state.riskRuleTokens.map(text).filter(Boolean))]
      : [],
    preview: isRecord(state.preview) ? clone(state.preview) : null,
    previewCandidateId: text(state.previewCandidateId),
    idempotencyKey: text(state.idempotencyKey),
    timeoutRetryUsed: state.timeoutRetryUsed === true,
    errorCode: text(state.errorCode),
    errorText: text(state.errorText),
  });
  const option = modeOption(wizard, setup);
  const current = setup.currentData;
  const rules = setup.ruleRevisions || [];
  const summary = {
    modeText: text(option?.label),
    modeDescription: text(option?.description),
    dataCutoffText: text(current?.dataCutoff),
    scopeDescription: text(current?.scopeDescription),
    comparisonRangeText: text(selectableBaseline(option, wizard.baselineToken)?.scopeDescription),
    selectedRuleCount: wizard.riskRuleTokens.length,
  };
  return freeze({
    ...wizard,
    modeOptions: setup.modes,
    basisOptions: option?.executionBasisOptions || [],
    baselineOptions: option?.baselineOptions || [],
    currentData: current,
    ruleRevisions: rules,
    summary: freeze(summary),
    canAdvance: canAdvanceR7Wizard(wizard, setup).ok,
  });
}

function wizardFailure(code, message, state) {
  return freeze({
    ...state,
    errorCode: code,
    errorText: message,
  });
}

export function setR7WizardSelection(state, field, value, options) {
  const setup = normalizeOptions(options, state?.projectId);
  if (!setup || !isRecord(state)) return freeze({ kind: "invalid", status: "invalid", text: R7_OPTIONS_REFRESH_TEXT });
  const next = { ...state, errorCode: "", errorText: "" };
  if (field === "mode") {
    const mode = text(value);
    const option = setup.modes.find((item) => item.mode === mode && item.available);
    if (!option) return wizardFailure("unsupported_mode", "请选择当前可用的监查方式。", state);
    const basis = text(option.defaultExecutionBasis);
    const baseline = mode === "daily" && basis === "incremental" ? recommendedBaseline(option) : null;
    return freeze({
      ...next,
      mode,
      executionBasis: basis,
      baselineToken: baseline?.baselineToken || "",
      step: Math.min(next.step, 1),
    });
  }
  if (field === "executionBasis") {
    const option = modeOption(state, setup);
    const basis = text(value);
    if (!validBasisOption(option, basis)) return wizardFailure("invalid_execution_basis", "请选择当前可用的执行基础。", state);
    const baseline = state.mode === "daily" && basis === "incremental"
      ? recommendedBaseline(option)
      : state.mode === "daily"
        ? null
        : selectableBaseline(option, next.baselineToken);
    return freeze({ ...next, executionBasis: basis, baselineToken: baseline?.baselineToken || "" });
  }
  if (field === "baselineToken") {
    const option = modeOption(state, setup);
    const token = text(value);
    if (token && !selectableBaseline(option, token)) {
      return wizardFailure("invalid_baseline", R7_COMPARISON_UNAVAILABLE_TEXT, state);
    }
    return freeze({ ...next, baselineToken: token });
  }
  if (field === "currentSnapshotToken") {
    const token = text(value);
    if (!token) return wizardFailure("invalid_snapshot", R7_OPTIONS_REFRESH_TEXT, state);
    return freeze({ ...next, currentSnapshotToken: token });
  }
  if (field === "riskRuleTokens") {
    const wanted = Array.isArray(value) ? value.map(text).filter(Boolean) : [];
    const allowed = new Set(setup.ruleRevisions.filter((item) => item.selectable).map((item) => item.revisionToken));
    return freeze({ ...next, riskRuleTokens: [...new Set(wanted.filter((token) => allowed.has(token)))] });
  }
  if (field === "preview") return freeze({ ...next, preview: isRecord(value) ? clone(value) : null });
  if (field === "previewCandidateId") return freeze({ ...next, previewCandidateId: text(value) });
  if (field === "idempotencyKey") return freeze({ ...next, idempotencyKey: text(value) });
  return freeze({ ...next, [field]: clone(value) });
}

export function canAdvanceR7Wizard(state, options) {
  const setup = normalizeOptions(options, state?.projectId);
  if (!setup || !isRecord(state)) return { ok: false, code: "options_invalid", text: R7_OPTIONS_REFRESH_TEXT };
  const option = modeOption(state, setup);
  const current = setup.currentData;
  if (state.step <= 1 && (!option || !option.available)) {
    return { ok: false, code: "mode_required", text: "请选择当前可用的监查方式。" };
  }
  if (state.step <= 2) {
    if (!text(state.currentSnapshotToken) || !current) return { ok: false, code: "snapshot_required", text: R7_OPTIONS_REFRESH_TEXT };
    if (state.executionBasis === "incremental" && current.canCompare !== true) {
      return { ok: false, code: "no_stable_business_key", text: R7_COMPARISON_UNAVAILABLE_TEXT };
    }
    if (!validBasisOption(option, state.executionBasis)) return { ok: false, code: "basis_required", text: "请选择当前可用的执行基础。" };
    if (state.mode === "daily" && state.executionBasis === "full" && text(state.baselineToken)) {
      return { ok: false, code: "baseline_forbidden", text: "全面分析不使用上次结果。" };
    }
    if (state.mode === "post_lock_pre_cfdi" && text(state.baselineToken)) {
      return { ok: false, code: "baseline_forbidden", text: "核查前监查使用新的固定数据范围。" };
    }
    if (state.executionBasis === "incremental" && !selectableBaseline(option, state.baselineToken)) {
      return { ok: false, code: "baseline_required", text: R7_COMPARISON_UNAVAILABLE_TEXT };
    }
  }
  if (state.step >= 4 && !text(state.idempotencyKey)) {
    return { ok: false, code: "idempotency_required", text: "本次设置尚未准备完成，请重新确认后开始。" };
  }
  return { ok: true, code: "", text: "" };
}

export function advanceR7WizardStep(state, options, direction = 1) {
  const step = Number.isInteger(state?.step) ? state.step : 1;
  const target = step + (direction >= 0 ? 1 : -1);
  if (target < 1 || target > R7_WIZARD_STEP_COUNT) return freeze(state);
  if (direction >= 0) {
    const check = canAdvanceR7Wizard(state, options);
    if (!check.ok) return wizardFailure(check.code, check.text, state);
  }
  return freeze({ ...state, step: target, errorCode: "", errorText: "" });
}

export const moveR7WizardStep = advanceR7WizardStep;

export function buildR7PrepareAndStartPayload(state, options) {
  const setup = normalizeOptions(options, state?.projectId);
  const check = !setup
    ? { ok: false, code: "options_invalid", text: R7_OPTIONS_REFRESH_TEXT }
    : canAdvanceR7Wizard({ ...state, step: 2 }, setup);
  if (!check.ok || !text(state?.idempotencyKey)) {
    const failure = !check.ok
      ? check
      : { ok: false, code: "idempotency_required", text: "本次设置尚未准备完成，请重新确认后开始。" };
    const error = new Error(failure.text);
    error.code = failure.code;
    throw error;
  }
  const option = modeOption(state, setup);
  const allowedRules = new Set(setup.ruleRevisions.filter((item) => item.selectable).map((item) => item.revisionToken));
  const payload = {
    current_snapshot_token: text(state.currentSnapshotToken),
    mode: text(state.mode),
    execution_basis: text(state.executionBasis),
    baseline_token: text(state.baselineToken) || null,
    risk_rule_tokens: [...new Set((Array.isArray(state.riskRuleTokens) ? state.riskRuleTokens : [])
      .map(text)
      .filter((token) => token && allowedRules.has(token)))],
    idempotency_key: text(state.idempotencyKey),
  };
  if (!option || !MODE_SET.has(payload.mode)) {
    const error = new Error("请选择当前可用的监查方式。");
    error.code = "mode_required";
    throw error;
  }
  return freeze(payload);
}

function defaultNonce() {
  if (typeof globalThis.crypto?.randomUUID === "function") return `r7_${globalThis.crypto.randomUUID()}`;
  return `r7_${Math.random().toString(36).slice(2)}_${Date.now().toString(36)}`;
}

function safeNonce(nonceFactory) {
  const value = text((nonceFactory || defaultNonce)());
  if (!/^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$/.test(value)) {
    throw new TypeError("idempotency nonce must be a bounded public client identifier");
  }
  return value;
}

export function createR7IdempotencyState({ key = "", selection = null, timeoutRetryUsed = false } = {}) {
  return freeze({
    key: text(key),
    selection: selection ? stateSelection(selection) : null,
    timeoutRetryUsed: timeoutRetryUsed === true,
    attemptCount: 0,
    lastPublicRunToken: "",
  });
}

export function ensureR7IdempotencyKey(state = {}, { nonceFactory } = {}) {
  if (text(state.key)) return freeze({ ...state });
  return freeze({
    ...createR7IdempotencyState(state),
    key: safeNonce(nonceFactory),
  });
}

export function rotateR7IdempotencyKey(state = {}, { nonceFactory, selection = null } = {}) {
  return freeze({
    ...createR7IdempotencyState(state),
    key: safeNonce(nonceFactory),
    selection: selection ? stateSelection(selection) : state.selection || null,
  });
}

export function syncR7IdempotencySelection(state = {}, selection, { nonceFactory } = {}) {
  const current = state.selection;
  if (!current || !idempotencySelectionEqual(current, selection)) {
    return rotateR7IdempotencyKey(state, { nonceFactory, selection });
  }
  return freeze({ ...state, selection: stateSelection(selection) });
}

export function markR7PrepareAttempt(state = {}) {
  return freeze({ ...state, attemptCount: (Number.isInteger(state.attemptCount) ? state.attemptCount : 0) + 1 });
}

/**
 * Timeout policy: a server-returned public token wins; otherwise one replay
 * with the same random nonce is permitted. A payload hash is never used as a
 * client idempotency key.
 */
export function handleR7PrepareTimeout(state = {}, { publicRunToken = "" } = {}) {
  const token = text(publicRunToken);
  if (token) {
    return freeze({
      state: { ...state, lastPublicRunToken: token, timeoutRetryUsed: true },
      action: "lookup_public_run",
      publicRunToken: token,
    });
  }
  if (state.timeoutRetryUsed === true) {
    return freeze({
      state: { ...state },
      action: "surface_timeout",
      publicRunToken: "",
    });
  }
  return freeze({
    state: { ...state, timeoutRetryUsed: true },
    action: "retry_same_key",
    publicRunToken: "",
  });
}

export function resetR7TimeoutRetry(state = {}) {
  return freeze({ ...state, timeoutRetryUsed: false, lastPublicRunToken: "" });
}

export function createR7IdempotencyController({ nonceFactory, initialState = {} } = {}) {
  let current = ensureR7IdempotencyKey(createR7IdempotencyState(initialState), { nonceFactory });
  return Object.freeze({
    getState() {
      return current;
    },
    syncSelection(selection) {
      current = syncR7IdempotencySelection(current, selection, { nonceFactory });
      return current;
    },
    rotate(selection = null) {
      current = rotateR7IdempotencyKey(current, { nonceFactory, selection });
      return current;
    },
    markAttempt() {
      current = markR7PrepareAttempt(current);
      return current;
    },
    handleTimeout(details = {}) {
      const result = handleR7PrepareTimeout(current, details);
      current = freeze(result.state);
      return result;
    },
    resetTimeoutRetry() {
      current = resetR7TimeoutRetry(current);
      return current;
    },
  });
}

export function projectR7AwayRestore({
  runs = null,
  history = null,
  route = {},
  navigation = "module_entry",
  resultContext = null,
  selectedPublicRunToken = "",
  selectedResultContextToken = "",
} = {}) {
  const explicitReturn = navigation === "return_overview" || navigation === "result_return";
  const routeResult = text(
    selectedResultContextToken
      || route?.result_context_token
      || route?.resultContextToken,
  );
  const routeRun = text(
    selectedPublicRunToken
      || route?.public_run_token
      || route?.publicRunToken,
  );
  const selection = selectR7Run({
    runs,
    history,
    // Module navigation intentionally re-applies default precedence; an old
    // result route must not pin stale history on a fresh module entry.
    selectedResultContextToken: explicitReturn ? routeResult : "",
    selectedPublicRunToken: explicitReturn ? routeRun : "",
    resultContext: explicitReturn ? resultContext : null,
  });
  return freeze({
    kind: "restore",
    navigation,
    view: explicitReturn ? "overview" : text(route?.view) || "overview",
    selectedPublicRunToken: explicitReturn
      ? selection.selectedPublicRunToken
      : selection.inFlightRun?.publicRunToken || selection.selectedPublicRunToken,
    selectedResultContextToken: explicitReturn
      ? routeResult || selection.selectedResultContextToken
      : "",
    selection,
    preservedResultContext: explicitReturn,
  });
}

export const restoreR7SelectedRun = projectR7AwayRestore;
export const projectR7ReturnState = projectR7AwayRestore;

export function markR7WizardOptionsStale(state) {
  return wizardFailure("options_stale", R7_OPTIONS_REFRESH_TEXT, state || {});
}

export function isR7ProductStateKind(value) {
  return R7_PRODUCT_STATE_KINDS.includes(text(value));
}

export function isR7InFlightProductRun(row) {
  return IN_FLIGHT_SET.has(text(rowValue(row, "runState", "run_state")));
}
