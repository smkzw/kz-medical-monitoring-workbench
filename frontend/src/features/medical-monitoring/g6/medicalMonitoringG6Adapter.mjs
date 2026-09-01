import {
  projectG6Domains,
  projectG6Flow,
  projectG6Journey,
  projectG6Overview,
} from "./medicalMonitoringG6Projection.mjs";

export const G6_SYNTHETIC_BUNDLE_ENDPOINT = "/api/g6/synthetic-bundle";
export const G6_CANONICAL_FIXTURE_DIGEST = "sha256:5cc67a088c3b43b430e2ab3433184ac2b68fa8323f24bf7d7c6d9c962b5be053";
export const G6_CANONICAL_PROFILE_BINDING_DIGEST = "sha256:1a8d65615d43535891b32948585a5d347caf8dfcb2b22fed68ab95a88896d956";
export const G6_CANONICAL_RUN_BINDING_DIGEST = "sha256:1fbb3df577759f9924ed930de923d66e849a1b37d72b823c0d291f87c5e142f1";
export const G6_CANONICAL_BUNDLE_DIGEST = "sha256:5bed1d17f6133dfa13f9ad63c53ea0b10140befde44704c72d321da7a353fe34";
export const G6_CANONICAL_PROFILE_ID = "synthetic-profile-cross-domain-g6-v1";
export const G6_CANONICAL_APP_VERSION = "medical-monitoring-local-g6-synthetic-1";
export const G6_CANONICAL_CONTRACT_VERSION = "0.2";
export const G6_CANONICAL_CONTRACT_REF = "medical_monitoring_r8_gate6_synthetic_ego_audience_acceptance_contract_v0_1_20260831";
export const G6_CANONICAL_PROVIDER = "synthetic-recorded-provider";
export const G6_CANONICAL_MODEL = "synthetic-recorded-model";
export const G6_CANONICAL_ADAPTER_ID = "g6-mock-recorded-adapter";
export const G6_CANONICAL_ADAPTER_KIND = "mock_recorded";

export const G6_CANONICAL_DOMAINS = Object.freeze(["AE", "MH", "CM", "IP", "LAB", "PD", "EFFICACY", "VISIT"]);
export const G6_CANONICAL_MODES = Object.freeze(["full", "periodic_increment", "lock_revision_increment"]);
export const G6_CANONICAL_PROJECT_REFS = Object.freeze(["synthetic-project-alpha", "synthetic-project-beta"]);
export const G6_CANONICAL_CENTER_REFS = Object.freeze(["synthetic-center-01", "synthetic-center-02", "synthetic-center-03"]);
const G6_CANONICAL_REQUIRED_TASK_COUNT = 13;

const MODE_LABELS = Object.freeze({
  full: { label: "完整分析", description: "覆盖当前合成资料" },
  periodic_increment: { label: "定期增量", description: "比较最近一次变化" },
  lock_revision_increment: { label: "锁库修订增量", description: "核对锁库后的修订" },
});
const TERMINAL_LABELS = Object.freeze({
  complete: "已完成",
  failed: "执行失败",
  partial: "部分完成",
  final_partial: "部分完成（最终）",
  truncated: "结果已截断",
  timed_out: "等待超时",
  cancelled: "已取消",
  interrupted: "执行中断",
  blocked: "已阻止",
});
const PROGRESS_STEPS = Object.freeze([
  { key: "scope", label: "确认资料范围" },
  { key: "events", label: "整理事件与访视" },
  { key: "risks", label: "核对风险线索" },
  { key: "result", label: "整理结果" },
]);

function clone(value) {
  return value === undefined ? undefined : JSON.parse(JSON.stringify(value));
}

function asObject(value) {
  return value && typeof value === "object" && !Array.isArray(value) ? value : null;
}

function asArray(value) {
  return Array.isArray(value) ? value : [];
}

function text(value) {
  return value === null || value === undefined ? "" : String(value).trim();
}

function fail(code, message) {
  throw new G6SyntheticAdapterError(code, message);
}

function expectEqual(actual, expected, code, message) {
  if (actual !== expected) fail(code, message);
}

function expectArray(value, minimum, code, message) {
  if (!Array.isArray(value) || value.length < minimum) fail(code, message);
}

function expectSha256(value, code, message) {
  if (!/^sha256:[0-9a-f]{64}$/u.test(text(value))) fail(code, message);
}

export class G6SyntheticAdapterError extends Error {
  constructor(code, message) {
    super(message);
    this.name = "G6SyntheticAdapterError";
    this.code = code;
  }
}

export function validateG6CanonicalBundle(value) {
  const bundle = asObject(value);
  if (!bundle) fail("CANONICAL_BUNDLE_INVALID", "合成演练资料无法确认，已停止显示。");
  const fixture = asObject(bundle.fixture);
  const binding = asObject(bundle.binding);
  if (!fixture || !binding) fail("CANONICAL_BUNDLE_SHAPE", "合成演练资料结构无法确认，已停止显示。");

  expectEqual(bundle.schema, "mm-monitoring-r8-g6-synthetic-audience-bundle-v1", "BUNDLE_SCHEMA_MISMATCH", "合成演练资料版本无法确认，已停止显示。");
  expectEqual(bundle.version, "1", "BUNDLE_VERSION_MISMATCH", "合成演练资料版本无法确认，已停止显示。");
  expectEqual(bundle.contract_ref, G6_CANONICAL_CONTRACT_REF, "BUNDLE_CONTRACT_MISMATCH", "合成演练资料合同无法确认，已停止显示。");
  expectEqual(bundle.contract_version, G6_CANONICAL_CONTRACT_VERSION, "BUNDLE_CONTRACT_MISMATCH", "合成演练资料合同无法确认，已停止显示。");
  expectEqual(bundle.app_version, G6_CANONICAL_APP_VERSION, "BUNDLE_APP_MISMATCH", "合成演练应用版本无法确认，已停止显示。");
  expectEqual(bundle.synthetic_only, true, "BUNDLE_BOUNDARY_MISMATCH", "当前资料不是合成离线资料，已停止显示。");
  expectEqual(bundle.offline, true, "BUNDLE_BOUNDARY_MISMATCH", "当前资料不是合成离线资料，已停止显示。");
  expectEqual(bundle.bundle_digest, G6_CANONICAL_BUNDLE_DIGEST, "BUNDLE_DIGEST_MISMATCH", "合成演练资料版本已变化，已停止显示。");

  expectEqual(fixture.schema, "mm-monitoring-r8-g6-cross-domain-synthetic-fixture-v1", "FIXTURE_SCHEMA_MISMATCH", "合成资料结构无法确认，已停止显示。");
  expectEqual(fixture.version, "1", "FIXTURE_VERSION_MISMATCH", "合成资料版本无法确认，已停止显示。");
  expectEqual(fixture.contract_ref, G6_CANONICAL_CONTRACT_REF, "FIXTURE_CONTRACT_MISMATCH", "合成资料合同无法确认，已停止显示。");
  expectEqual(fixture.contract_version, G6_CANONICAL_CONTRACT_VERSION, "FIXTURE_CONTRACT_MISMATCH", "合成资料合同无法确认，已停止显示。");
  expectEqual(fixture.app_version, G6_CANONICAL_APP_VERSION, "FIXTURE_APP_MISMATCH", "合成资料应用版本无法确认，已停止显示。");
  expectEqual(fixture.synthetic_profile_id, G6_CANONICAL_PROFILE_ID, "FIXTURE_PROFILE_MISMATCH", "合成资料身份无法确认，已停止显示。");
  expectEqual(fixture.synthetic_only, true, "FIXTURE_BOUNDARY_MISMATCH", "当前资料不是合成离线资料，已停止显示。");
  expectEqual(fixture.offline, true, "FIXTURE_BOUNDARY_MISMATCH", "当前资料不是合成离线资料，已停止显示。");
  expectEqual(fixture.fixture_digest, G6_CANONICAL_FIXTURE_DIGEST, "FIXTURE_DIGEST_MISMATCH", "合成资料版本已变化，已停止显示。");
  expectEqual(fixture.binding_digest, G6_CANONICAL_PROFILE_BINDING_DIGEST, "PROFILE_BINDING_MISMATCH", "合成资料绑定无法确认，已停止显示。");
  expectEqual(fixture.profile_binding_digest, G6_CANONICAL_PROFILE_BINDING_DIGEST, "PROFILE_BINDING_MISMATCH", "合成资料绑定无法确认，已停止显示。");

  const counts = asObject(fixture.counts);
  if (!counts) fail("FIXTURE_COUNTS_MISSING", "合成资料数量无法确认，已停止显示。");
  for (const [key, expected] of Object.entries({ projects: 2, centers: 3, subjects: 12, visits: 48, events: 96, analysis_inputs: 6, risk_scenarios: 8 })) {
    expectEqual(counts[key], expected, "FIXTURE_COUNT_MISMATCH", "合成资料数量无法确认，已停止显示。");
  }
  expectArray(fixture.projects, 2, "FIXTURE_PROJECTS_MISSING", "合成项目无法确认，已停止显示。");
  expectArray(fixture.centers, 3, "FIXTURE_CENTERS_MISSING", "合成中心无法确认，已停止显示。");
  expectArray(fixture.subjects, 12, "FIXTURE_SUBJECTS_MISSING", "合成受试者无法确认，已停止显示。");
  expectArray(fixture.visits, 48, "FIXTURE_VISITS_MISSING", "合成访视无法确认，已停止显示。");
  expectArray(fixture.events, 96, "FIXTURE_EVENTS_MISSING", "合成事件无法确认，已停止显示。");
  expectArray(fixture.analysis_modes, 3, "FIXTURE_MODES_MISSING", "分析范围无法确认，已停止显示。");
  expectArray(fixture.analysis_inputs, 6, "FIXTURE_ANALYSIS_INPUTS_MISSING", "分析范围无法确认，已停止显示。");
  expectArray(fixture.risk_scenarios, 8, "FIXTURE_RISKS_MISSING", "风险范围无法确认，已停止显示。");
  expectArray(fixture.analysis_cases, 2, "FIXTURE_ANALYSIS_CASES_MISSING", "分析场景无法确认，已停止显示。");
  expectArray(fixture.flow_nodes, 5, "FIXTURE_FLOW_NODES_MISSING", "研究状态流向无法确认，已停止显示。");
  expectArray(fixture.flow_rows, 30, "FIXTURE_FLOW_ROWS_MISSING", "研究状态流向无法确认，已停止显示。");
  expectEqual(fixture.analysis_modes.join(","), G6_CANONICAL_MODES.join(","), "FIXTURE_MODES_MISMATCH", "分析范围无法确认，已停止显示。");
  expectEqual(fixture.journey?.orientation, "horizontal", "FIXTURE_JOURNEY_MISMATCH", "受试者旅程无法确认，已停止显示。");
  expectEqual(fixture.journey?.event_count, 96, "FIXTURE_JOURNEY_MISMATCH", "受试者旅程无法确认，已停止显示。");
  expectEqual(asArray(fixture.journey?.marker_domains).join(","), G6_CANONICAL_DOMAINS.join(","), "FIXTURE_DOMAINS_MISMATCH", "事件类别无法确认，已停止显示。");
  expectEqual(fixture.section_15_4?.task_count, G6_CANONICAL_REQUIRED_TASK_COUNT, "FIXTURE_TASKS_MISMATCH", "应用内任务范围无法确认，已停止显示。");
  if (!asArray(fixture.flow_rows).some((row) => Number(row.count) === 0)) fail("FIXTURE_ZERO_FLOW_MISSING", "零值流向无法确认，已停止显示。");
  const projectRefs = new Set(asArray(fixture.projects).map((project) => project.project_ref));
  if (G6_CANONICAL_PROJECT_REFS.some((ref) => !projectRefs.has(ref))) fail("FIXTURE_PROJECT_ID_MISMATCH", "合成项目身份无法确认，已停止显示。");
  if (asArray(fixture.projects).some((project) => project.synthetic_only !== true || G6_CANONICAL_CENTER_REFS.some((ref) => !asArray(project.center_refs).includes(ref)))) {
    fail("FIXTURE_PROJECT_BOUNDARY_MISMATCH", "合成项目范围无法确认，已停止显示。");
  }
  const eventDomains = new Set(asArray(fixture.events).map((event) => event.domain));
  if (G6_CANONICAL_DOMAINS.some((domain) => !eventDomains.has(domain))) fail("FIXTURE_EVENT_DOMAIN_MISMATCH", "事件类别无法确认，已停止显示。");

  expectEqual(binding.schema, "mm-monitoring-r8-g6-synthetic-profile-binding-v1", "BINDING_SCHEMA_MISMATCH", "合成执行绑定无法确认，已停止显示。");
  expectEqual(binding.version, "1", "BINDING_VERSION_MISMATCH", "合成执行绑定无法确认，已停止显示。");
  expectEqual(binding.contract_ref, G6_CANONICAL_CONTRACT_REF, "BINDING_CONTRACT_MISMATCH", "合成执行绑定无法确认，已停止显示。");
  expectEqual(binding.contract_version, G6_CANONICAL_CONTRACT_VERSION, "BINDING_CONTRACT_MISMATCH", "合成执行绑定无法确认，已停止显示。");
  expectEqual(binding.app_version, G6_CANONICAL_APP_VERSION, "BINDING_APP_MISMATCH", "合成执行绑定无法确认，已停止显示。");
  expectEqual(binding.synthetic_profile_id, G6_CANONICAL_PROFILE_ID, "BINDING_PROFILE_MISMATCH", "合成执行绑定无法确认，已停止显示。");
  expectEqual(binding.fixture_id, "synthetic-cross-domain-g6-v1", "BINDING_FIXTURE_MISMATCH", "合成执行绑定无法确认，已停止显示。");
  expectEqual(binding.fixture_digest, G6_CANONICAL_FIXTURE_DIGEST, "BINDING_FIXTURE_DIGEST_MISMATCH", "合成执行绑定无法确认，已停止显示。");
  expectEqual(binding.fixture_binding_digest, G6_CANONICAL_PROFILE_BINDING_DIGEST, "BINDING_PROFILE_BINDING_MISMATCH", "合成执行绑定无法确认，已停止显示。");
  expectEqual(binding.project_ref, "synthetic-project-alpha", "BINDING_PROJECT_MISMATCH", "合成执行绑定无法确认，已停止显示。");
  expectEqual(binding.admission_id, "synthetic-admission-alpha", "BINDING_ADMISSION_MISMATCH", "合成执行绑定无法确认，已停止显示。");
  expectEqual(binding.run_ref, "synthetic-run-alpha-full", "BINDING_RUN_MISMATCH", "合成执行绑定无法确认，已停止显示。");
  expectEqual(binding.analysis_mode, "full", "BINDING_MODE_MISMATCH", "合成执行绑定无法确认，已停止显示。");
  expectEqual(binding.provider, G6_CANONICAL_PROVIDER, "BINDING_PROVIDER_MISMATCH", "合成执行绑定无法确认，已停止显示。");
  expectEqual(binding.model, G6_CANONICAL_MODEL, "BINDING_MODEL_MISMATCH", "合成执行绑定无法确认，已停止显示。");
  expectEqual(binding.adapter_id, G6_CANONICAL_ADAPTER_ID, "BINDING_ADAPTER_MISMATCH", "合成执行绑定无法确认，已停止显示。");
  expectEqual(binding.adapter_kind, G6_CANONICAL_ADAPTER_KIND, "BINDING_ADAPTER_MISMATCH", "合成执行绑定无法确认，已停止显示。");
  expectEqual(binding.adapter_version, "1", "BINDING_ADAPTER_VERSION_MISMATCH", "合成执行绑定无法确认，已停止显示。");
  expectEqual(binding.synthetic_only, true, "BINDING_BOUNDARY_MISMATCH", "当前执行条件不是合成离线条件，已停止显示。");
  expectEqual(binding.offline, true, "BINDING_BOUNDARY_MISMATCH", "当前执行条件不是合成离线条件，已停止显示。");
  expectSha256(binding.source_manifest_digest, "BINDING_MANIFEST_MISMATCH", "合成执行来源无法确认，已停止显示。");
  expectSha256(binding.output_manifest_digest, "BINDING_MANIFEST_MISMATCH", "合成执行结果无法确认，已停止显示。");
  expectEqual(binding.binding_digest, G6_CANONICAL_RUN_BINDING_DIGEST, "BINDING_DIGEST_MISMATCH", "合成执行绑定版本已变化，已停止显示。");
  expectSha256(bundle.notification_matrix?.matrix_digest, "MATRIX_DIGEST_MISSING", "通知记录无法确认，已停止显示。");
  expectEqual(bundle.user_task_evidence?.task_count, G6_CANONICAL_REQUIRED_TASK_COUNT, "TASK_EVIDENCE_MISMATCH", "应用内任务记录无法确认，已停止显示。");
  return clone(bundle);
}

export async function fetchG6SyntheticBundle({ fetchImpl = globalThis.fetch } = {}) {
  if (typeof fetchImpl !== "function") {
    fail("FETCH_UNAVAILABLE", "合成演练资料暂不可用，已停止显示。");
  }
  let response;
  try {
    response = await fetchImpl(G6_SYNTHETIC_BUNDLE_ENDPOINT, {
      method: "GET",
      headers: { Accept: "application/json" },
    });
  } catch (error) {
    throw new G6SyntheticAdapterError("FETCH_FAILED", "合成演练资料暂不可用，已停止显示。");
  }
  if (!response || response.ok !== true) {
    throw new G6SyntheticAdapterError("CANONICAL_BUNDLE_UNAVAILABLE", "合成演练资料暂不可用，已停止显示。");
  }
  let payload;
  try {
    payload = await response.json();
  } catch (error) {
    throw new G6SyntheticAdapterError("CANONICAL_BUNDLE_PARSE_FAILED", "合成演练资料无法读取，已停止显示。");
  }
  return validateG6CanonicalBundle(payload);
}

function publicProgress(run) {
  const progress = Math.max(0, Math.min(100, Number(run.progress) || 0));
  const stepIndex = progress >= 100 ? PROGRESS_STEPS.length - 1 : Math.min(PROGRESS_STEPS.length - 1, Math.floor(progress / 25));
  const step = PROGRESS_STEPS[stepIndex];
  const terminalStatus = run.terminal_status || "complete";
  const terminalLabel = TERMINAL_LABELS[terminalStatus] || "结果状态待确认";
  return {
    run_ref: run.run_ref,
    project_ref: run.project_ref,
    mode: run.mode,
    state: run.state,
    percent: progress,
    terminal_status: terminalStatus,
    terminal_label: terminalLabel,
    current_step: step.key,
    current_step_label: step.label,
    detail: progress >= 100 ? `本轮结果已整理完成：${terminalLabel}。` : `${step.label}中，请稍候。`,
    steps: PROGRESS_STEPS.map((item, index) => ({
      key: item.key,
      label: item.label,
      state: index < stepIndex || progress >= 100 ? "done" : index === stepIndex ? "current" : "pending",
    })),
  };
}

export class G6SyntheticAdapter {
  constructor({ bundle } = {}) {
    if (!bundle) fail("CANONICAL_BUNDLE_REQUIRED", "合成演练资料暂不可用，已停止显示。");
    this.bundle = validateG6CanonicalBundle(bundle);
    this.fixture = this.bundle.fixture;
    this.binding = this.bundle.binding;
    this.runs = new Map();
    this.activeRunByProject = new Map();
    this.ledger = [{ action: "canonical_bundle_validated", bundle_digest: this.bundle.bundle_digest }];
  }

  _project(projectRef) {
    const project = asArray(this.fixture.projects).find((item) => item.project_ref === text(projectRef));
    if (!project) fail("PROJECT_NOT_FOUND", "当前项目无法确认，请返回项目列表。");
    return project;
  }

  _analysisInput(projectRef, mode) {
    const input = asArray(this.fixture.analysis_inputs).find((item) => item.project_ref === text(projectRef) && item.analysis_mode === text(mode));
    if (!input) fail("ANALYSIS_INPUT_NOT_FOUND", "当前分析范围无法确认，请返回项目总览。");
    return input;
  }

  listProjects() {
    return clone(asArray(this.fixture.projects).map((project) => ({
      ref: project.project_ref,
      label: project.display_name,
      centerRefs: [...project.center_refs],
      admissionId: project.admission_id,
      focusText: "查看本轮风险、研究状态流向和中心分布。",
    })));
  }

  getModes() {
    return clone(asArray(this.fixture.analysis_modes).map((key) => ({
      key,
      ...(MODE_LABELS[key] || { label: key, description: "当前合成资料范围" }),
    })));
  }

  getDomains() {
    return clone(projectG6Domains(this.fixture));
  }

  getOverview(projectRef) {
    const project = this._project(projectRef);
    const overview = projectG6Overview(this.fixture, project.project_ref);
    if (overview.state === "blocked") fail("OVERVIEW_BLOCKED", overview.notice);
    this.ledger.push({ action: "read_overview", project_ref: project.project_ref });
    return clone(overview);
  }

  getFlow(projectRef, centerRef = "") {
    const project = this._project(projectRef);
    if (centerRef && !asArray(project.center_refs).includes(centerRef)) fail("CENTER_OUT_OF_SCOPE", "该中心不在当前项目范围内。");
    const flow = projectG6Flow(this.fixture, project.project_ref, centerRef);
    if (flow.state === "blocked") fail("FLOW_BLOCKED", flow.notice);
    this.ledger.push({ action: "read_flow", project_ref: project.project_ref, center_ref: centerRef || null });
    return clone(flow);
  }

  getJourney(projectRef, subjectRef) {
    const project = this._project(projectRef);
    const journey = projectG6Journey(this.fixture, project.project_ref, text(subjectRef));
    if (journey.state === "blocked") fail("SUBJECT_NOT_FOUND", journey.notice);
    this.ledger.push({ action: "read_journey", project_ref: project.project_ref, subject_ref: text(subjectRef) });
    return clone(journey);
  }

  prepareRun({ projectRef, mode = "full", idempotencyKey = "" } = {}) {
    const project = this._project(projectRef);
    const selectedMode = text(mode) || "full";
    if (!G6_CANONICAL_MODES.includes(selectedMode)) fail("MODE_INVALID", "请选择一种分析范围。");
    const input = this._analysisInput(project.project_ref, selectedMode);
    const existingRef = this.activeRunByProject.get(project.project_ref);
    if (existingRef) {
      const existing = this.runs.get(existingRef);
      if (existing && existing.mode === selectedMode && (!idempotencyKey || existing.idempotency_key === idempotencyKey)) return clone(publicProgress(existing));
      fail("RUN_ALREADY_BOUND", "当前项目已有本轮分析，请先查看结果。");
    }
    const run = {
      run_ref: input.run_ref,
      project_ref: project.project_ref,
      mode: selectedMode,
      terminal_status: input.terminal_status,
      idempotency_key: text(idempotencyKey) || `g6:${project.project_ref}:${selectedMode}`,
      state: "prepared",
      progress: 0,
    };
    this.runs.set(run.run_ref, run);
    this.activeRunByProject.set(project.project_ref, run.run_ref);
    this.ledger.push({ action: "prepare_run", project_ref: project.project_ref, mode: selectedMode, run_ref: run.run_ref, binding_digest: this.binding.binding_digest });
    return clone(publicProgress(run));
  }

  startRun(runRef) {
    const ref = text(runRef);
    const run = this.runs.get(ref);
    if (!run) fail("RUN_NOT_FOUND", "本轮分析无法确认，请返回项目总览。");
    if (run.state === "complete" || run.state === "running") return clone(publicProgress(run));
    run.state = "running";
    this.ledger.push({ action: "start_run", project_ref: run.project_ref, run_ref: run.run_ref, binding_digest: this.binding.binding_digest });
    return clone(publicProgress(run));
  }

  readProgress(runRef) {
    const ref = text(runRef);
    const run = this.runs.get(ref);
    if (!run) fail("RUN_NOT_FOUND", "本轮分析无法确认，请返回项目总览。");
    if (run.state === "running") {
      run.progress = Math.min(100, run.progress + 25);
      if (run.progress >= 100) run.state = "complete";
      this.ledger.push({ action: "read_progress", project_ref: run.project_ref, run_ref: run.run_ref, percent: run.progress });
    }
    return clone(publicProgress(run));
  }

  getResult(runRef) {
    const ref = text(runRef);
    const run = this.runs.get(ref);
    if (!run || run.state !== "complete") fail("RESULT_NOT_READY", "本轮结果尚未整理完成。");
    const overview = this.getOverview(run.project_ref);
    this.ledger.push({ action: "read_result", project_ref: run.project_ref, run_ref: run.run_ref });
    return clone({ ...overview, run: publicProgress(run) });
  }

  getLedger() {
    return clone(this.ledger);
  }

  getBinding() {
    return clone(this.binding);
  }

  getBundleIdentity() {
    return clone({
      bundle_digest: this.bundle.bundle_digest,
      fixture_digest: this.fixture.fixture_digest,
      profile_binding_digest: this.fixture.profile_binding_digest,
      binding_digest: this.binding.binding_digest,
      app_version: this.bundle.app_version,
      contract_version: this.bundle.contract_version,
    });
  }
}

export function createG6SyntheticAdapter(options = {}) {
  return new G6SyntheticAdapter(options);
}

export { PROGRESS_STEPS };
