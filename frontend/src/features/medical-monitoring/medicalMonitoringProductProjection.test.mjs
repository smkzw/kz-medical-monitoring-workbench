import assert from "node:assert/strict";

import {
  R7_PRODUCT_HISTORY_FIELDS,
  R7_PUBLIC_RESULT_UNAVAILABLE_TEXT,
  computeR7PublicResponseDigest,
  normalizeR7History,
  normalizeR7PublicProgress,
  normalizeR7ResultEntry,
  projectR7History,
  projectR7PublicProgress,
  projectR7ResultContext,
  projectR7ResultEntry,
  projectR7SetupOptions,
  safeValidateR7PublicResultEnvelope,
  validateR7PublicResultEnvelope,
  verifyR7PublicResultEnvelope,
} from "./medicalMonitoringProductProjection.mjs";

let passed = 0;
function check(condition, message) {
  assert.equal(Boolean(condition), true, message);
  passed += 1;
}

function mode(mode, overrides = {}) {
  return {
    mode,
    label: `${mode} 服务文案`,
    description: `${mode} 服务说明`,
    execution_basis_options: [
      { value: "full", label: "全量", available: true, disabled_reason: "" },
      ...(mode === "daily"
        ? [{ value: "incremental", label: "增量", available: true, disabled_reason: "" }]
        : []),
    ],
    default_execution_basis: mode === "daily" ? "incremental" : "full",
    requires_published_same_mode_baseline: mode === "daily",
    baseline_options: mode === "daily"
      ? [{
        baseline_token: "baseline:daily:1",
        mode: "daily",
        mode_text: "日常监查",
        data_cutoff: "2026-03-01",
        published_at: "2026-03-02T00:00:00Z",
        scope_description: "同项目已发布结果",
        recommended: true,
        selectable: true,
      }]
      : [],
    available: true,
    disabled_reason: "",
    recommended: mode === "daily",
    recommendation_reason: mode === "daily" ? "服务端推荐" : "",
    ...overrides,
  };
}

const setupPayload = {
  schema_version: "mm-r7-slice07c1-run-setup-v1",
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
  modes: [mode("daily"), mode("pre_lock"), mode("post_lock_pre_cfdi")],
  rule_revisions: [{
    project_id: "project-a",
    revision: 1,
    revision_token: "rule-revision:project-a:1",
    summary: "关注肝功能相关数据",
    applicable_scope: "所有受试者",
    starting_run: "下一次日常监查",
    selectable: true,
    created_at: "2026-03-01T00:00:00Z",
  }],
  recommended_mode: "daily",
  recommendation_reason: "服务端推荐日常监查",
};

const setup = projectR7SetupOptions(setupPayload, { projectId: "project-a" });
check(setup.kind === "setup", "setup options project to a pure setup view");
check(setup.modes.length === 3, "setup exposes exactly the three server modes");
check(setup.modes[0].label === "daily 服务文案", "mode label stays server-owned");
check(setup.modes[0].baselineOptions[0].baselineToken === "baseline:daily:1", "baseline remains opaque");
check(setup.currentData.rowCount === 12, "setup copies server row count without recalculation");
check(setup.ruleRevisions[0].revisionToken === "rule-revision:project-a:1", "rule revisions expose only public tokens");
check(
  projectR7SetupOptions({ ...setupPayload, modes: [...setupPayload.modes, mode("daily-unknown")] }, { projectId: "project-a" }).kind === "invalid",
  "a forged fourth mode fails closed instead of becoming a card",
);
check(
  projectR7SetupOptions({ ...setupPayload, project_id: "other" }, { projectId: "project-a" }).kind === "invalid",
  "cross-project setup responses fail closed",
);
check(
  projectR7SetupOptions({ ...setupPayload, current_data: { ...setupPayload.current_data, snapshot_ref: "internal" } }, { projectId: "project-a" }).kind === "invalid",
  "setup responses containing internal snapshot identity fail closed",
);

const historyRow = {
  public_run_token: "run:001",
  mode_text: "日常监查",
  data_cutoff_text: "2026-03-31",
  comparison_range_text: "当前完整数据（不使用比较基线）",
  run_state: "completed",
  result_available: true,
  main_action: "查看本次结果",
  status_text: "结果已整理完成",
};
const history = projectR7History({ runs: [historyRow] }, { projectId: "project-a" });
check(history.kind === "history", "history projects to a bounded view");
check(history.rows.length === 1 && history.rows[0].publicRunToken === "run:001", "history keeps the public run token");
check(history.rows[0].statusText === "结果已整理完成", "history keeps server Chinese status text");
check(!Object.hasOwn(history.rows[0], "percent"), "history has no percentage field");
check(
  normalizeR7History({ runs: [{ ...historyRow, percent: 100 }] }, { projectId: "project-a" }).ok === false,
  "history rejects percentage or other extra fields",
);
check(
  projectR7History({ runs: [{ ...historyRow, run_id: "internal" }] }, { projectId: "project-a" }).kind === "invalid",
  "history rejects internal run identity",
);
check(R7_PRODUCT_HISTORY_FIELDS.length === 8, "history field registry is exactly eight fields");
const resultEntry = projectR7ResultEntry({
  project_ref: "project-a",
  public_run_token: "run:001",
  snapshot_token: "snapshot:current",
  data_cutoff_text: "2026-03-31",
  site_options: [{ site_ref: "site-01", site_label: "中心 site-01" }],
  result_context_token: "result-context:abc",
}, { projectId: "project-a", publicRunToken: "run:001" });
check(resultEntry.kind === "result_entry", "result entry projects the public context handoff");
check(resultEntry.siteOptions[0].site_ref === "site-01", "result entry retains server site locator shape without internal identity");
check(resultEntry.resultContextToken === "result-context:abc", "result entry preserves the public result context token");
check(
  normalizeR7ResultEntry({
    project_ref: "project-a",
    public_run_token: "run:001",
    snapshot_token: "snapshot:current",
    data_cutoff_text: "2026-03-31",
    site_options: [{ site_ref: "site-01", site_label: "中心 site-01", run_ref: "internal" }],
    result_context_token: "result-context:abc",
  }, { projectId: "project-a" }).ok === false,
  "result entry rejects internal identities nested in site options",
);

const progressPayload = {
  run_state: "completed",
  headline: "本次监查已完成",
  completed: 8,
  total: 8,
  percent: 100,
  progress_text: "已处理 8/8 项（100%）",
  status_overview: [{ state_label: "已完成", count: 8 }],
  stage_progress: [],
  current_work: [],
  latest_updates: [],
  run_status_text: "已完成",
  available_actions: [],
  publication_state: "publishing",
  result_available: false,
  publication_status_text: "结果整理中",
};
const progress = projectR7PublicProgress(progressPayload, { publicRunToken: "run:001" });
check(progress.kind === "public_progress", "public progress keeps a distinct public projection kind");
check(progress.publicRunToken === "run:001", "public progress binds the path token locally");
check(progress.poll.active === true && progress.poll.reason === "publication", "completed unpublished progress keeps polling publication");
const availableProgress = projectR7PublicProgress({ ...progressPayload, publication_state: "available", result_available: true }, { publicRunToken: "run:001" });
check(availableProgress.poll.active === false, "available publication stops polling");
check(
  projectR7PublicProgress({ ...progressPayload, run_id: "internal" }, { publicRunToken: "run:001" }).kind === "invalid",
  "public progress rejects internal run identity",
);
check(
  normalizeR7PublicProgress(progressPayload, {}).ok === false,
  "public progress requires the caller's public run token",
);

const baseEnvelope = {
  identity: {
    project_ref: "project-a",
    public_run_token: "run:001",
    snapshot_token: "snapshot:current",
    data_cutoff_text: "2026-03-31",
    view: "overview",
    mode_text: "日常监查",
    site_scope_text: "中心 01、中心 02",
    site_ref: "site-01",
  },
  projection: {
    kind: "project_cockpit",
    subject_flow: { availability: "available", subjects: [] },
  },
  result_context_token: "result-context:abc",
  response_digest: "0".repeat(64),
};
const digest = await computeR7PublicResponseDigest(baseEnvelope);
const envelope = { ...baseEnvelope, response_digest: digest };
const valid = validateR7PublicResultEnvelope(envelope, {
  projectId: "project-a",
  resultContextToken: "result-context:abc",
  publicRunToken: "run:001",
  view: "overview",
});
check(valid.identity.project_ref === "project-a", "public envelope validates project identity");
check(valid.identity.site_ref === "site-01", "public envelope preserves public locators");
check(projectR7ResultContext(envelope, { projectId: "project-a" }).kind === "result", "result envelope projects to a result context");
check(
  safeValidateR7PublicResultEnvelope({ ...envelope, identity: { ...envelope.identity, run_ref: "internal" } }, { projectId: "project-a" }).ok === false,
  "public envelope rejects internal R5/run fields",
);
check(
  safeValidateR7PublicResultEnvelope({ ...envelope, response_digest: "bad" }, { projectId: "project-a" }).ok === false,
  "public envelope rejects malformed response digests",
);
check(
  safeValidateR7PublicResultEnvelope({ ...envelope, extra: true }, { projectId: "project-a" }).ok === false,
  "public envelope rejects unknown top-level keys",
);
check(
  safeValidateR7PublicResultEnvelope({ ...envelope, identity: { ...envelope.identity, project_ref: "other" } }, { projectId: "project-a" }).ok === false,
  "public envelope rejects cross-project identity",
);
await verifyR7PublicResultEnvelope(envelope, { projectId: "project-a", resultContextToken: "result-context:abc" });
passed += 1;
await assert.rejects(
  verifyR7PublicResultEnvelope({ ...envelope, projection: { changed: true } }, { projectId: "project-a" }),
  (error) => error.code === "public_response_digest_mismatch",
);
passed += 1;
check(
  projectR7ResultContext({ ...envelope, response_digest: "bad" }, { projectId: "project-a" }).text === R7_PUBLIC_RESULT_UNAVAILABLE_TEXT,
  "invalid result context maps to the unified Chinese unavailable state",
);

console.log(`medicalMonitoringProductProjection: ${passed} passed`);
