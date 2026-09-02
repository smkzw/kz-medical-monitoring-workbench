import assert from "node:assert/strict";
import {
  ADMISSION_WIZARD_STEPS,
  admissionPrimaryAction,
  admissionRecovery,
  admissionSecondaryActions,
  admissionStepView,
  admissionTechnicalRows,
  admissionWizardReducer,
  createAdmissionWizardState,
  formatAdmissionByteSize,
  projectAdmissionProfile,
  readAdmissionProfile,
  validateAdmissionSourceDir,
} from "./medicalMonitoringAdmissionWizardState.mjs";
import { findMonitoringForbiddenTerms } from "./medicalMonitoringProgressProjection.mjs";

let passed = 0;
function check(condition, message) {
  assert.ok(condition, message);
  passed += 1;
}

// ---------------------------------------------------------------------------
// Generated C1 payloads (fixtures, never real project data).

function hex(seed, length = 64) {
  let out = "";
  for (let index = 0; index < length; index += 1) {
    out += String.fromCharCode(97 + ((seed + index * 7) % 26));
  }
  return out;
}

function generatedTableFixture({ name, sourceFile, rowCount, withRoles }) {
  const column = (extra = {}) => ({
    name: extra.name,
    inferred_type: extra.inferred_type,
    missing_count: extra.missing ?? 0,
    distinct_count: extra.distinct ?? 12,
    samples: ["示例值"],
    date_range: extra.date_range ?? null,
    suggested_roles: extra.roles ?? [],
  });
  return {
    name,
    source_file: sourceFile,
    row_count: rowCount,
    column_count: 4,
    needs_confirmation: withRoles ? 2 : 0,
    columns: [
      column({ name: "受试者编号", inferred_type: "text", roles: withRoles ? ["受试者标识"] : [] }),
      column({ name: "访视", inferred_type: "text", roles: withRoles ? ["访视"] : [] }),
      column({
        name: "访视日期",
        inferred_type: "date",
        missing: 2,
        roles: withRoles ? ["日期"] : [],
        date_range: { min: "2026-01-12", max: "2026-08-30", parsed_count: rowCount - 2 },
      }),
      column({ name: "实验室结果", inferred_type: "number" }),
    ],
  };
}

function generatedAdmissionFixture({
  attemptId = "adm-20260902-0001",
  withRoles = true,
  withTechnical = true,
} = {}) {
  const tables = [
    generatedTableFixture({ name: "访视列表", sourceFile: "visit_listings.csv", rowCount: 128, withRoles }),
    generatedTableFixture({ name: "不良事件", sourceFile: "adverse_events.csv", rowCount: 36, withRoles }),
  ];
  return {
    schema_version: "mm-c1-data-admission-v1",
    project_id: "proj-e2e-check",
    attempt_id: attemptId,
    state: "profile_ready",
    summary: { files: 2, tables: 2, rows: 164 },
    tables,
    ...(withTechnical ? {
      technical_details: {
        manifest_hash: hex(3),
        files: [
          { path: "visit_listings.csv", size: 1536, sha256: hex(5) },
          { path: "adverse_events.csv", size: 20480, sha256: hex(9) },
        ],
        revision_ids: ["srcc1_" + hex(11, 24)],
        snapshot_ids: ["lsnap_" + hex(13, 24)],
        locator_index_ids: ["lsnap_" + hex(15, 24)],
        profile_ids: ["prof_" + hex(17, 24)],
      },
    } : {}),
  };
}

// ---------------------------------------------------------------------------
// Source-dir validation mirrors the server-side rules for instant feedback.

check(validateAdmissionSourceDir("").ok === false, "empty source dir rejected");
check(validateAdmissionSourceDir("   ").ok === false, "blank source dir rejected");
check(validateAdmissionSourceDir(" /data/listings ").ok === false, "edge spaces rejected");
check(validateAdmissionSourceDir("x".repeat(4097)).ok === false, "overlong source dir rejected");
check(validateAdmissionSourceDir("/data/listings/2026-08").ok === true, "plain path accepted");

// ---------------------------------------------------------------------------
// Happy-path transitions across the three steps.

let state = createAdmissionWizardState({ projectId: "proj-e2e-check" });
check(state.phase === "input" && state.stepIndex === 0, "initial state");

state = admissionWizardReducer(state, { type: "source-dir-change", value: "/data/listings/2026-08" });
check(admissionPrimaryAction(state).key === "import"
  && admissionPrimaryAction(state).disabled === false
  && admissionPrimaryAction(state).label === "开始导入", "input primary ready when source valid");
check(admissionPrimaryAction(createAdmissionWizardState({})).disabled === true, "input primary disabled when empty");

const pickedFile = { name: "listing.csv", webkitRelativePath: "本期数据/listing.csv" };
const picked = admissionWizardReducer(
  createAdmissionWizardState({ projectId: "proj-e2e-check" }),
  { type: "source-files-change", files: [pickedFile] },
);
check(picked.selectedFiles.length === 1 && picked.selectedFolderName === "本期数据",
  "browser-selected folder is summarized without exposing a local path");
check(admissionPrimaryAction(picked).disabled === false, "selected files enable import without a manual path");

state = admissionWizardReducer(state, { type: "import-start" });
check(state.phase === "creating" && admissionPrimaryAction(state).label === "正在导入…", "creating phase primary");

const createdPayload = generatedAdmissionFixture();
state = admissionWizardReducer(state, { type: "import-created", payload: createdPayload });
check(state.phase === "reading" && state.attemptId === "adm-20260902-0001" && state.stepIndex === 1, "created advances to reading");
check(admissionPrimaryAction(state).label === "正在识别数据结构…", "reading primary busy");

const profilePayload = generatedAdmissionFixture();
state = admissionWizardReducer(state, { type: "profile-loaded", payload: profilePayload });
check(state.phase === "ready" && state.profile, "profile loaded to ready");
check(state.profile.summaryText === "2 个文件 · 2 张数据表 · 164 行数据", "summary text from generated payload");
check(state.profile.pendingColumns.length === 6, "pending columns collected from generated roles");
check(admissionPrimaryAction(state).key === "advance", "review primary advances");

state = admissionWizardReducer(state, { type: "advance" });
check(state.stepIndex === 2 && admissionPrimaryAction(state).key === "finish", "confirm step primary finishes");
check(admissionSecondaryActions(state).length === 1
  && admissionSecondaryActions(state)[0].key === "back", "confirm step offers back");

state = admissionWizardReducer(state, { type: "finish" });
check(state.phase === "done" && admissionPrimaryAction(state).key === "restart", "done primary restarts");
check(admissionStepView(state).every((step) => step.kind === "done"), "done marks all steps complete");

const before = state;
state = admissionWizardReducer(state, { type: "restart" });
check(state.phase === "input" && state.stepIndex === 0 && state.attemptId === "" && state.sourceDir === ""
  && state.projectId === before.projectId, "restart resets but keeps project");

// Reducer ignores unknown actions.
check(admissionWizardReducer(before, { type: "nonsense" }) === before, "unknown action ignored");

// ---------------------------------------------------------------------------
// Failure paths with recovery guidance.

let bad = admissionWizardReducer(createAdmissionWizardState({}), { type: "import-start" });
check(bad.phase === "failed" && bad.error.code === "admission_project_missing", "missing project fails closed");

bad = admissionWizardReducer(
  createAdmissionWizardState({ projectId: "proj-e2e-check" }),
  { type: "import-created", payload: { attempt_id: "bad id!" } },
);
check(bad.phase === "failed" && bad.error.code === "admission_response_invalid" && bad.retryTarget === "create",
  "invalid attempt id treated as invalid response");

bad = admissionWizardReducer(
  createAdmissionWizardState({ projectId: "proj-e2e-check" }),
  { type: "profile-loaded", payload: { tables: [] } },
);
check(bad.phase === "failed" && bad.error.code === "admission_response_invalid", "empty tables treated as invalid response");

const sourceError = admissionWizardReducer(
  createAdmissionWizardState({ projectId: "proj-e2e-check" }),
  {
    type: "error",
    error: {
      status: 422,
      message: "未找到可导入的数据目录。请确认所选数据位置存在且包含数据文件后重试。",
      detail: { code: "admission_source_invalid" },
    },
  },
);
check(sourceError.phase === "failed", "source error fails");
check(sourceError.error.code === "admission_source_invalid", "recovery keeps server code");
check(sourceError.error.serverText.includes("未找到可导入的数据目录"), "server message stays headline");
check(sourceError.error.guidance.length === 2, "recovery guidance lines present");
check(sourceError.retryTarget === "create", "source error retries create");
check(admissionPrimaryAction(sourceError).key === "retry", "retryable failure primary is retry");
check(admissionSecondaryActions(sourceError)[0].key === "restart", "retryable failure secondary is restart");

// Editing the source after a failure returns to a clean input step.
const cleared = admissionWizardReducer(sourceError, { type: "source-dir-change", value: "/data/listings/2026-09" });
check(cleared.phase === "input" && cleared.error === null, "editing source clears failure");

const notFound = admissionRecovery({
  status: 404,
  message: "未找到对应的数据导入记录。请返回上一步重新选择，或重新发起导入。",
  detail: { code: "admission_attempt_not_found" },
});
check(notFound.canRetry === false, "missing attempt is not retryable");
check(admissionWizardReducer(sourceError, { type: "error", recovery: notFound }).retryTarget === null,
  "non-retryable failure clears retry target");
check(admissionPrimaryAction(
  admissionWizardReducer(sourceError, { type: "error", recovery: notFound }),
).key === "restart", "non-retryable failure primary is restart");

const network = admissionRecovery({ status: 0, message: "Failed to fetch" });
check(network.serverText.startsWith("网络连接异常"), "network failure replaces browser message");
check(network.canRetry === true, "network failure is retryable");

const identity = admissionRecovery({
  status: 409,
  message: "当前为演示项目，不能接入本机数据。请在实际研究项目中使用数据接入。",
  detail: { code: "admission_project_identity_conflict" },
});
check(identity.canRetry === false && identity.retryTarget === null, "identity conflict offers no retry");

// ---------------------------------------------------------------------------
// Reading-phase transport sequencing (status first, then profile).

const calls = [];
const stubApi = {
  getDataAdmissionStatus: async (projectId, attemptId) => {
    calls.push(["status", projectId, attemptId]);
    return { state: "profile_ready" };
  },
  getDataAdmissionProfile: async (projectId, attemptId) => {
    calls.push(["profile", projectId, attemptId]);
    return generatedAdmissionFixture();
  },
};

const readOk = await readAdmissionProfile({ api: stubApi, projectId: "proj-e2e-check", attemptId: "adm-20260902-0001" });
check(readOk.ok === true && calls.length === 2 && calls[0][0] === "status" && calls[1][0] === "profile",
  "status read precedes profile read");

const pendingApi = {
  getDataAdmissionStatus: async () => ({ state: "staging" }),
  getDataAdmissionProfile: async () => { throw new Error("must not be called"); },
};
const readPending = await readAdmissionProfile({ api: pendingApi, projectId: "p", attemptId: "a" });
check(readPending.ok === false && readPending.recovery.code === "admission_not_ready"
  && readPending.recovery.retryTarget === "read", "not-ready status skips profile read");

const failedApi = {
  getDataAdmissionStatus: async () => {
    throw {
      status: 404,
      message: "未找到对应的数据导入记录。",
      detail: { code: "admission_attempt_not_found" },
    };
  },
  getDataAdmissionProfile: async () => ({}),
};
const readFailed = await readAdmissionProfile({ api: failedApi, projectId: "p", attemptId: "a" });
check(readFailed.ok === false && readFailed.recovery.code === "admission_attempt_not_found"
  && readFailed.recovery.canRetry === false, "status failure maps recovery");

// ---------------------------------------------------------------------------
// Profile projection details.

const projected = projectAdmissionProfile(generatedAdmissionFixture());
check(projected.tables.length === 2, "tables projected");
check(projected.tables[0].columns[2].typeText === "日期", "date type label");
check(projected.tables[0].columns[2].missingText === "缺失 2", "missing count text");
check(projected.tables[0].columns[2].dateRangeText === "2026-01-12 ~ 2026-08-30", "date range text");
check(projected.tables[0].columns[3].typeText === "数值", "number type label");
check(projected.pendingColumns.every((item) => item.roles.length > 0), "pending columns carry roles");
check(projected.technical && typeof projected.technical.manifest_hash === "string", "technical carried separately");

const untyped = projectAdmissionProfile({
  summary: {},
  tables: [{
    name: "补充表",
    source_file: "extra.csv",
    row_count: 10,
    columns: [{ name: "备注", inferred_type: "unknown_kind", missing_count: 1, suggested_roles: [] }],
  }],
});
check(untyped.summaryText === "1 个文件 · 1 张数据表 · 10 行数据", "summary derived when absent");
check(untyped.tables[0].columns[0].typeText === "文本", "unknown type falls back to 文本");

const emptyProfile = projectAdmissionProfile({ summary: { files: 0, tables: 0, rows: 0 }, tables: [] });
check(emptyProfile.summaryText === "0 个文件 · 0 张数据表 · 0 行数据", "empty profile renders zeroed summary");
check(emptyProfile.technical === null, "missing technical stays null");

const localSelection = admissionWizardReducer(
  createAdmissionWizardState({ projectId: "p" }),
  { type: "source-dir-change", value: "/new/local/selection" },
);
check(
  admissionWizardReducer(localSelection, {
    type: "resume-created",
    payload: { attempt_id: "older-attempt" },
  }) === localSelection,
  "late resume never replaces a new local selection",
);
const resumed = admissionWizardReducer(
  createAdmissionWizardState({ projectId: "p" }),
  { type: "resume-created", payload: { attempt_id: "older-attempt" } },
);
check(
  resumed.phase === "reading" && resumed.attemptId === "older-attempt",
  "resume continues the latest untouched admission",
);

// ---------------------------------------------------------------------------
// Technical rows stay inside the collapsed region contract.

const techRows = admissionTechnicalRows(generatedAdmissionFixture().technical_details);
check(techRows[0].label === "数据清单校验值", "manifest row first");
check(techRows[1].label === "数据文件" && techRows[1].files.length === 2, "file rows listed");
check(techRows[1].files[0].sizeText === "1.5 KB", "byte size formatted as KB");
check(techRows[1].files[1].sizeText === "20 KB", "byte size rounded KB");
check(techRows.some((row) => row.label === "来源版本标识"), "revision ids row present");
check(techRows.some((row) => row.label === "单元格定位索引标识"), "locator ids row present");
check(admissionTechnicalRows(null) === null, "no technical renders nothing");
check(admissionTechnicalRows({}) === null, "empty technical renders nothing");

check(formatAdmissionByteSize(0) === "0 B", "0 B formatting");
check(formatAdmissionByteSize(1023) === "1023 B", "bytes formatting");
check(formatAdmissionByteSize(1024) === "1 KB", "1 KB formatting");
check(formatAdmissionByteSize(1048576) === "1 MB", "1 MB formatting");
check(formatAdmissionByteSize(3145728) === "3 MB", "3 MB formatting");

// ---------------------------------------------------------------------------
// Step indicator states.

const stepTodo = admissionStepView(createAdmissionWizardState({}));
check(stepTodo[0].kind === "current" && stepTodo[1].kind === "todo" && stepTodo[0].indexText === "第 一 步",
  "initial step view");
const stepMid = admissionStepView({ phase: "ready", stepIndex: 1 });
check(stepMid[0].kind === "done" && stepMid[1].kind === "current", "review step view");

check(ADMISSION_WIZARD_STEPS.map((step) => step.title).join("/") === "选择数据/查看系统识别结果/核对系统识别",
  "three canonical steps");

// ---------------------------------------------------------------------------
// User-visible copy must stay free of engineering terms.

const visibleCopy = [];
for (const guide of [
  admissionRecovery({ status: 422, message: "未找到可导入的数据目录。", detail: { code: "admission_source_invalid" } }),
  admissionRecovery({ status: 409, message: "数据复制校验未通过。", detail: { code: "admission_copy_rejected" } }),
  admissionRecovery({ status: 409, message: "无法识别结构。", detail: { code: "admission_profile_unavailable" } }),
  admissionRecovery({ status: 409, message: "当前为演示项目。", detail: { code: "admission_project_identity_conflict" } }),
  admissionRecovery({ status: 404, message: "未找到记录。", detail: { code: "admission_attempt_not_found" } }),
  admissionRecovery({ status: 503, message: "服务未配置。", detail: { code: "admission_pipeline_unconfigured" } }),
  admissionRecovery({ status: 500, message: "导入出现问题。", detail: { code: "admission_pipeline_failed" } }),
  admissionRecovery({ status: 0, message: "Failed to fetch" }),
  admissionRecovery({ code: "admission_not_ready" }),
  admissionRecovery({ code: "admission_response_invalid" }),
  admissionRecovery({ code: "admission_project_missing" }),
]) {
  visibleCopy.push(guide.serverText, ...guide.guidance);
}
for (const phase of ["input", "creating", "reading", "ready", "done", "failed"]) {
  const base = { ...createAdmissionWizardState({ projectId: "p" }), phase };
  visibleCopy.push(admissionPrimaryAction(base).label, ...admissionSecondaryActions(base).map((item) => item.label));
}
visibleCopy.push(
  admissionPrimaryAction({ ...createAdmissionWizardState({}), phase: "ready", stepIndex: 1 }).label,
  admissionPrimaryAction({ ...createAdmissionWizardState({}), phase: "ready", stepIndex: 2 }).label,
  admissionPrimaryAction({ ...createAdmissionWizardState({}), phase: "failed", retryTarget: null }).label,
);
for (const step of ADMISSION_WIZARD_STEPS) visibleCopy.push(step.title);

const copyHits = findMonitoringForbiddenTerms(visibleCopy);
check(copyHits.length === 0, `module copy excludes forbidden terms${copyHits.length ? `: ${JSON.stringify(copyHits)}` : ""}`);

console.log(`medicalMonitoringAdmissionWizardState: ${passed} passed`);
