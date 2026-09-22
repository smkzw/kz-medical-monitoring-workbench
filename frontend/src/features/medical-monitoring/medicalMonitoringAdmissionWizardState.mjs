// Pure state machine for the C2 data-admission wizard. The component owns
// transport only; every transition, projection and recovery decision lives
// here so the C1 admission contract can be tested without a DOM.

export const ADMISSION_WIZARD_STEPS = Object.freeze([
  { key: "select-source", title: "选择数据" },
  { key: "review-profile", title: "查看导入概况" },
  { key: "confirm-fields", title: "处理少量疑点" },
]);

export const ADMISSION_SUPPORTED_SUFFIX_TEXT = ".csv / .xls / .xlsx / .xlsm";

export const ADMISSION_SOURCE_MAX_LENGTH = 4096;
const ATTEMPT_ID_PATTERN = /^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$/;

const COLUMN_TYPE_TEXTS = Object.freeze({
  date: "日期",
  number: "数值",
  text: "文本",
  mixed: "混合",
});

const STEP_INDEX_TEXTS = Object.freeze(["一", "二", "三"]);

function cleanText(value) {
  return typeof value === "string" ? value.trim() : "";
}

function toCount(value) {
  const parsed = Number(value);
  return Number.isFinite(parsed) && parsed >= 0 ? Math.round(parsed) : 0;
}

function isRecord(value) {
  return Boolean(value) && typeof value === "object" && !Array.isArray(value);
}

// Recovery guidance per stable admission error code. Server messages stay the
// headline; guidance lines always name the next concrete action for the user.
const RECOVERY_GUIDES = Object.freeze({
  admission_source_invalid: Object.freeze({
    guidance: Object.freeze([
      "确认数据位置填写正确，且该位置包含受支持的数据文件（.csv / .xls / .xlsx / .xlsm）。",
      "修正后重新开始导入。",
    ]),
    canRetry: true,
    retryTarget: "create",
  }),
  admission_copy_rejected: Object.freeze({
    guidance: Object.freeze([
      "本次导入已自动取消，原始数据未受任何影响。",
      "请重新发起导入；如再次失败，请先确认数据来源完整后再试。",
    ]),
    canRetry: true,
    retryTarget: "create",
  }),
  admission_profile_unavailable: Object.freeze({
    guidance: Object.freeze([
      "系统未能识别这批数据的结构，本次导入未完成。",
      "请确认文件格式受支持后重新导入。",
    ]),
    canRetry: true,
    retryTarget: "create",
  }),
  admission_project_identity_conflict: Object.freeze({
    guidance: Object.freeze([
      "演示数据会继续保持原样，不会被本机数据替换。",
      "请返回实际研究项目后重新选择数据。",
    ]),
    canRetry: false,
  }),
  admission_attempt_not_found: Object.freeze({
    guidance: Object.freeze([
      "未找到对应的导入记录，该记录可能已失效。",
      "请返回第 1 步重新选择数据位置，并重新发起导入。",
    ]),
    canRetry: false,
  }),
  admission_attempt_id_invalid: Object.freeze({
    guidance: Object.freeze([
      "导入记录标识无效，无法继续读取。",
      "请返回第 1 步重新选择数据位置，并重新发起导入。",
    ]),
    canRetry: false,
  }),
  admission_pipeline_unconfigured: Object.freeze({
    guidance: Object.freeze([
      "数据接入服务尚未配置，暂时无法导入新数据。",
      "请联系管理员完成配置后再试。",
    ]),
    canRetry: false,
  }),
  admission_pipeline_failed: Object.freeze({
    guidance: Object.freeze([
      "导入过程中出现问题，本次操作未生效，原始数据未受影响。",
      "请重试；如再次失败，请联系管理员。",
    ]),
    canRetry: true,
  }),
  admission_projection_violation: Object.freeze({
    guidance: Object.freeze([
      "系统生成的识别结果格式异常，本次结果未展示，原始数据未受影响。",
      "请重试；如再次失败，请联系管理员。",
    ]),
    canRetry: true,
  }),
  // Internal-only code: the status read succeeded but the attempt is not
  // finished yet; the profile is intentionally not fetched.
  admission_not_ready: Object.freeze({
    serverText: "这批数据还在处理中，尚未完成识别。",
    guidance: Object.freeze([
      "请稍后重试；若多次提示，请返回重新发起导入。",
    ]),
    canRetry: true,
    retryTarget: "read",
  }),
  // Internal-only code: create returned an unusable response body.
  admission_response_invalid: Object.freeze({
    serverText: "系统返回的导入结果不完整，本次导入未生效。",
    guidance: Object.freeze([
      "本次导入未生效，原始数据未受影响。",
      "请重试；如再次失败，请联系管理员。",
    ]),
    canRetry: true,
    retryTarget: "create",
  }),
  // Internal-only code: the wizard was mounted without a usable project.
  admission_project_missing: Object.freeze({
    serverText: "当前项目无法确认，请返回项目概览后重试。",
    guidance: Object.freeze([
      "返回项目概览重新进入医学监查后，再发起数据接入。",
    ]),
    canRetry: false,
  }),
});

const NETWORK_RECOVERY = Object.freeze({
  serverText: "网络连接异常，本次导入未完成，原始数据未受影响。",
  guidance: Object.freeze([
    "请稍后重试；如再次失败，请联系管理员检查服务状态。",
  ]),
  canRetry: true,
});

export function admissionRecovery(errorLike) {
  const status = Number(errorLike?.status) || 0;
  const code = cleanText(errorLike?.detail?.code) || cleanText(errorLike?.code);
  const guide = RECOVERY_GUIDES[code] || null;
  let serverText = cleanText(errorLike?.message);
  if (guide?.serverText) serverText = guide.serverText;
  if (!code && status === 0) {
    // Transport-level failure (browser message is not user-facing Chinese).
    serverText = NETWORK_RECOVERY.serverText;
  }
  if (!serverText) {
    serverText = "数据导入未能完成，原始数据未受影响。";
  }
  const canRetry = guide ? guide.canRetry : true;
  const retryTarget = guide ? guide.retryTarget || null : null;
  const guidance = guide ? guide.guidance : NETWORK_RECOVERY.guidance;
  return Object.freeze({
    code: code || (status ? `http_${status}` : "network"),
    status,
    serverText,
    guidance: Object.freeze([...guidance]),
    canRetry,
    retryTarget,
  });
}

export function validateAdmissionSourceDir(value) {
  const raw = String(value ?? "");
  if (!raw.trim()) return { ok: false, text: "请填写数据所在位置。" };
  if (raw !== raw.trim()) return { ok: false, text: "数据位置开头或结尾不能包含空格。" };
  if (raw.length > ADMISSION_SOURCE_MAX_LENGTH) {
    return { ok: false, text: "数据位置过长，请检查填写内容。" };
  }
  return { ok: true, text: "" };
}

export function createAdmissionWizardState({ projectId = "" } = {}) {
  return {
    projectId: String(projectId || ""),
    sourceDir: "",
    selectedFiles: [],
    selectedFolderName: "",
    phase: "input", // input | creating | reading | ready | failed | done
    stepIndex: 0,
    attemptId: "",
    profile: null,
    error: null,
    retryTarget: null, // "create" | "read"
  };
}

function responseInvalidFailure(state) {
  const recovery = admissionRecovery({ code: "admission_response_invalid" });
  return { ...state, phase: "failed", error: { ...recovery, retryTarget: "create" }, retryTarget: "create" };
}

export function admissionWizardReducer(state, action) {
  switch (action?.type) {
    case "source-dir-change":
      return {
        ...state,
        sourceDir: String(action.value ?? ""),
        error: null,
        retryTarget: null,
        phase: state.phase === "failed" ? "input" : state.phase,
      };
    case "source-files-change": {
      const selectedFiles = Array.from(action.files || []);
      const firstPath = String(selectedFiles[0]?.webkitRelativePath || selectedFiles[0]?.name || "");
      const selectedFolderName = firstPath.includes("/") ? firstPath.split("/")[0] : "所选文件";
      return {
        ...state,
        selectedFiles,
        selectedFolderName: selectedFiles.length ? selectedFolderName : "",
        sourceDir: selectedFiles.length ? "" : state.sourceDir,
        error: null,
        retryTarget: null,
        phase: state.phase === "failed" ? "input" : state.phase,
      };
    }
    case "import-start":
      if (!state.projectId.trim()) {
        const recovery = admissionRecovery({ code: "admission_project_missing" });
        return { ...state, phase: "failed", error: { ...recovery, retryTarget: null }, retryTarget: null };
      }
      return { ...state, phase: "creating", error: null, retryTarget: null };
    case "import-created": {
      const attemptId = cleanText(action.payload?.attempt_id);
      if (!ATTEMPT_ID_PATTERN.test(attemptId)) return responseInvalidFailure(state);
      return { ...state, attemptId, stepIndex: 1, phase: "reading", retryTarget: "read", error: null };
    }
    case "resume-created": {
      if (state.selectedFiles.length || state.sourceDir.trim()) return state;
      const attemptId = cleanText(action.payload?.attempt_id);
      if (!ATTEMPT_ID_PATTERN.test(attemptId)) return responseInvalidFailure(state);
      return { ...state, attemptId, stepIndex: 1, phase: "reading", retryTarget: "read", error: null };
    }
    case "profile-loaded": {
      if (!Array.isArray(action.payload?.tables) || action.payload.tables.length === 0) {
        return responseInvalidFailure(state);
      }
      return {
        ...state,
        profile: projectAdmissionProfile(action.payload),
        phase: "ready",
        error: null,
        retryTarget: null,
      };
    }
    case "advance":
      return state.stepIndex === 1 ? { ...state, stepIndex: 2 } : state;
    case "back":
      return state.stepIndex === 2 ? { ...state, stepIndex: 1 } : state;
    case "finish":
      return { ...state, phase: "done" };
    case "retry": {
      const target = state.retryTarget || (state.attemptId ? "read" : "create");
      return { ...state, phase: target === "create" ? "creating" : "reading", error: null, retryTarget: target };
    }
    case "restart":
      return createAdmissionWizardState({ projectId: state.projectId });
    case "error": {
      const recovery = action.recovery || admissionRecovery(action.error);
      const fallbackTarget = state.attemptId ? "read" : "create";
      const retryTarget = recovery.canRetry ? recovery.retryTarget || fallbackTarget : null;
      return { ...state, phase: "failed", error: { ...recovery, retryTarget }, retryTarget };
    }
    default:
      return state;
  }
}

// Single primary action per render; the label names the concrete next step.
export function admissionPrimaryAction(state) {
  switch (state?.phase) {
    case "creating":
      return { key: "creating", label: "正在导入…", disabled: true };
    case "reading":
      return { key: "reading", label: "正在识别数据结构…", disabled: true };
    case "ready":
      return state.stepIndex === 1
        ? { key: "advance", label: "下一步：让系统核对字段" }
        : { key: "finish", label: "完成接入" };
    case "done":
      return { key: "restart", label: "再接入一批数据" };
    case "failed":
      return state.retryTarget
        ? { key: "retry", label: "重试" }
        : { key: "restart", label: "重新开始" };
    default:
      return {
        key: "import",
        label: "开始导入",
        disabled: !(state?.selectedFiles?.length > 0) && !validateAdmissionSourceDir(state?.sourceDir).ok,
      };
  }
}

export function admissionSecondaryActions(state) {
  if (!state) return [];
  if (state.phase === "failed" && state.retryTarget) {
    return [{ key: "restart", label: "重新开始" }];
  }
  if (state.phase === "ready" && state.stepIndex === 2) {
    return [{ key: "back", label: "返回上一步" }];
  }
  return [];
}

export function admissionStepView(state) {
  const current = state?.phase === "done" ? ADMISSION_WIZARD_STEPS.length : state?.stepIndex || 0;
  return ADMISSION_WIZARD_STEPS.map((step, index) => ({
    ...step,
    indexText: `第 ${STEP_INDEX_TEXTS[index]} 步`,
    kind: index < current ? "done" : index === current ? "current" : "todo",
  }));
}

export function formatAdmissionByteSize(size) {
  const bytes = toCount(size);
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) {
    const kb = Math.round((bytes / 1024) * 10) / 10;
    return `${kb} KB`;
  }
  const mb = Math.round((bytes / (1024 * 1024)) * 10) / 10;
  return `${mb} MB`;
}

// Structure summary first: counts, per-table plain-language rows, and the
// pending human-judgement columns. `technical_details` is carried separately
// and may only be rendered inside the collapsed region.
export function projectAdmissionProfile(payload) {
  const tables = Array.isArray(payload?.tables) ? payload.tables : [];
  const summary = isRecord(payload?.summary) ? payload.summary : {};
  const tableViews = tables.map((table) => {
    const columns = Array.isArray(table?.columns) ? table.columns : [];
    const columnViews = columns.map((column) => ({
      name: cleanText(column?.name),
      typeText: COLUMN_TYPE_TEXTS[column?.inferred_type] || "文本",
      missingCount: toCount(column?.missing_count),
      missingText: toCount(column?.missing_count) > 0 ? `缺失 ${toCount(column?.missing_count)}` : "",
      roles: Object.freeze(Array.isArray(column?.suggested_roles) ? column.suggested_roles.map(cleanText).filter(Boolean) : []),
      dateRangeText: isRecord(column?.date_range) && column.date_range.min && column.date_range.max
        ? `${column.date_range.min} ~ ${column.date_range.max}`
        : "",
    }));
    return {
      name: cleanText(table?.name),
      sourceFile: cleanText(table?.source_file),
      rowCount: toCount(table?.row_count),
      rowsText: `${toCount(table?.row_count)} 行`,
      columnCount: toCount(table?.column_count) || columnViews.length,
      needsConfirmation: columnViews.some((column) => column.roles.length > 0),
      columns: columnViews,
    };
  });
  const pendingColumns = tableViews.flatMap((table) =>
    table.columns
      .filter((column) => column.roles.length > 0)
      .map((column) => ({
        tableName: table.name,
        columnName: column.name,
        roles: column.roles,
      })),
  );
  const files = toCount(summary.files) || new Set(tableViews.map((table) => table.sourceFile).filter(Boolean)).size;
  const rows = toCount(summary.rows) || tableViews.reduce((total, table) => total + table.rowCount, 0);
  return {
    summaryText: `${files} 个文件 · ${tableViews.length} 张数据表 · ${rows} 行数据`,
    files,
    tables: tableViews,
    pendingColumns,
    technical: isRecord(payload?.technical_details) ? payload.technical_details : null,
  };
}

// Collapsed technical region content: paths, hashes and internal identities,
// labelled in product language. Returns null when there is nothing to show.
export function admissionTechnicalRows(technical) {
  if (!isRecord(technical)) return null;
  const rows = [];
  const manifestHash = cleanText(technical.manifest_hash);
  if (manifestHash) rows.push({ label: "数据清单校验值", value: manifestHash });
  if (Array.isArray(technical.files) && technical.files.length > 0) {
    rows.push({
      label: "数据文件",
      files: technical.files.map((file) => ({
        name: cleanText(file?.path) || cleanText(file?.name),
        sizeText: file?.size === undefined || file?.size === null ? "" : formatAdmissionByteSize(file.size),
        digest: cleanText(file?.sha256),
      })).filter((file) => file.name),
    });
  }
  const idRows = [
    ["revision_ids", "来源版本标识"],
    ["snapshot_ids", "数据快照标识"],
    ["locator_index_ids", "单元格定位索引标识"],
    ["profile_ids", "结构画像标识"],
  ];
  for (const [key, label] of idRows) {
    const ids = Array.isArray(technical[key]) ? technical[key].map(cleanText).filter(Boolean) : [];
    if (ids.length > 0) rows.push({ label, value: ids.join("、") });
  }
  return rows.length > 0 ? rows : null;
}

// Transport sequencing for the reading phase: confirm the attempt status
// first, then fetch the profile. Returns a plain result the component turns
// into dispatches, so the ordering is testable without React.
export async function readAdmissionProfile({ api, projectId, attemptId }) {
  try {
    const status = await api.getDataAdmissionStatus(projectId, attemptId);
    if (status?.state !== "profile_ready") {
      return { ok: false, recovery: admissionRecovery({ code: "admission_not_ready" }) };
    }
    const payload = await api.getDataAdmissionProfile(projectId, attemptId);
    return { ok: true, payload, status };
  } catch (error) {
    return { ok: false, recovery: admissionRecovery(error) };
  }
}
