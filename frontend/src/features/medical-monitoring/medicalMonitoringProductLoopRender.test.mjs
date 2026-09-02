import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import { createRequire } from "node:module";
import { fileURLToPath } from "node:url";
import { createElement } from "react";
import { buildSync } from "esbuild";

let passed = 0;
function check(condition, message) {
  assert.equal(Boolean(condition), true, message);
  passed += 1;
}
const require = createRequire(import.meta.url);

const here = path.dirname(fileURLToPath(import.meta.url));
const bundlePath = path.join(here, ".monitoring-product-loop-render-bundle.cjs");
buildSync({
  entryPoints: [path.join(here, "MedicalMonitoringProductLoop.jsx")],
  bundle: true,
  format: "cjs",
  platform: "node",
  outfile: bundlePath,
  jsx: "automatic",
  loader: { ".css": "empty" },
  define: { "process.env.NODE_ENV": '"test"' },
  logLevel: "silent",
});
let bundled;
try {
  bundled = require(bundlePath);
} finally {
  fs.rmSync(bundlePath, { force: true });
}

function element(name, props = {}) {
  return createElement(bundled[name], props);
}

function render(value) {
  // Load the server renderer only after the JSX bundle has been built.
  return require("react-dom/server").renderToStaticMarkup(value);
}

const noRun = {
  kind: "ready",
  selectedRun: null,
  workbar: {
    mainAction: "开始一次监查",
    mainTarget: "wizard",
    secondaryAction: "查看历史",
    secondaryTarget: "history",
    otherAction: "",
  },
};
const inFlight = {
  kind: "active_run",
  selectedRun: {
    publicRunToken: "run:active",
    modeText: "日常监查",
    dataCutoffText: "2026-08-28",
    comparisonRangeText: "同项目已发布基线",
  },
  workbar: {
    mainAction: "查看本次进度",
    mainTarget: "progress",
    secondaryAction: "查看历史",
    secondaryTarget: "history",
    otherAction: "",
  },
};
const published = {
  kind: "result_available",
  selectedRun: {
    publicRunToken: "run:published",
    modeText: "锁库前监查",
    dataCutoffText: "2026-08-20",
    comparisonRangeText: "上一轮同模式结果",
  },
  workbar: {
    mainAction: "查看本次结果",
    mainTarget: "result",
    secondaryAction: "开始一次新的监查",
    secondaryTarget: "wizard",
    otherAction: "查看历史",
    otherTarget: "history",
  },
};

const noRunHtml = render(element("MonitoringProductWorkbar", { state: noRun, onAction: () => {} }));
check(noRunHtml.includes('aria-label="本次监查"'), "workbar keeps 本次监查 as the accessible region name");
check(noRunHtml.includes("医学监查工作区"), "empty workbar falls back to workspace title without cadence pair");
check(noRunHtml.includes(">开始一次监查</button>"), "empty project offers server start action");
check(noRunHtml.includes(">查看历史</button>"), "empty project offers history action");

const activeHtml = render(element("MonitoringProductWorkbar", { state: inFlight, onAction: () => {} }));
check(activeHtml.includes("日常监查（本次）"), "in-flight workbar uses one cadence line without 本次监查/日常监查 adjacency");
check(!/本次监查<\/span>\s*<strong>日常监查/.test(activeHtml), "in-flight workbar does not stack 本次监查 beside 日常监查");
check(activeHtml.includes(">查看本次进度</button>"), "in-flight workbar routes to public progress");
check(!activeHtml.includes("开始一次新的监查"), "in-flight workbar suppresses new run");

const publishedHtml = render(element("MonitoringProductWorkbar", { state: published, onAction: () => {} }));
check(publishedHtml.includes("锁库前监查（本次）"), "published workbar keeps cadence in one native Chinese line");
check(publishedHtml.includes(">查看本次结果</button>"), "published workbar routes to result");
check(publishedHtml.includes(">开始一次新的监查</button>"), "published workbar exposes new run");
check(!publishedHtml.includes("run:published"), "public run token is not rendered to the user");

const wizard = {
  step: 1,
  mode: "daily",
  modeOptions: [
    { mode: "daily", label: "日常监查", description: "服务端日常监查说明", available: true, recommended: true, recommendationReason: "服务端推荐" },
    { mode: "pre_lock", label: "锁库前监查", description: "服务端锁库前说明", available: true, recommended: false },
    { mode: "post_lock_pre_cfdi", label: "核查前监查", description: "服务端核查前说明", available: true, recommended: false },
  ],
  basisOptions: [],
  baselineOptions: [],
  ruleRevisions: [],
  riskRuleTokens: [],
  currentData: { scopeDescription: "当前完整数据", dataCutoff: "2026-08-28", rowCount: 12 },
  summary: {},
};
const wizardHtml = render(element("MonitoringWizardView", { wizard, onClose: () => {}, onSelect: () => {}, onAdvance: () => {}, onPreview: () => {}, onClosePreview: () => {}, onConfirmPreview: () => {} }));
check((wizardHtml.match(/monitoring-mode-card(?:\s|")/g) || []).length === 3, "wizard step one renders exactly three server modes");
check(wizardHtml.includes("选择监查方式") && wizardHtml.includes("确认数据范围") && wizardHtml.includes("选择特殊关注") && wizardHtml.includes("确认并开始"), "wizard renders four Chinese steps");
check(!wizardHtml.includes("run_state") && !wizardHtml.includes("publication_state") && !wizardHtml.includes("token"), "wizard does not expose machine identities");

const scopeWizardHtml = render(element("MonitoringWizardView", {
  wizard: {
    ...wizard,
    step: 2,
    currentSnapshotToken: "snapshot:current",
    dataBatches: [{ snapshotToken: "snapshot:current", dataCutoff: "2026-08-28", scopeDescription: "当前完整数据", rowCount: 12 }],
    executionBasis: "incremental",
    basisOptions: [{ value: "incremental", label: "基于上次结果分析变化", available: true }],
    baselineToken: "baseline:1",
    baselineOptions: [{ baselineToken: "baseline:1", scopeDescription: "同项目已发布结果", dataCutoff: "2026-08-20", selectable: true, recommended: true }],
  },
  onClose: () => {},
  onSelect: () => {},
  onAdvance: () => {},
  onPreview: () => {},
  onClosePreview: () => {},
  onConfirmPreview: () => {},
}));
check(scopeWizardHtml.includes("确认数据范围") && scopeWizardHtml.includes("基于上次结果分析变化") && scopeWizardHtml.includes("同项目已发布结果"), "wizard scope step renders server basis and baseline");
const previewWizardHtml = render(element("MonitoringWizardView", {
  wizard: {
    ...wizard,
    step: 3,
    ruleRevisions: [{ revisionToken: "rule:1", summary: "关注肝功能", applicableScope: "项目内", startingRun: "下一次监查", selectable: true }],
    riskRuleTokens: ["rule:1"],
    preview: { state: "ambiguous", reason: "请选择一个关注方向。", candidates: [{ candidate_id: "candidate:1", subject: "感染事件", condition: "体温异常", explanation: "按输入保留条件" }, { candidate_id: "candidate:2", subject: "实验室检查", condition: "指标变化", explanation: "按输入保留条件" }] },
    previewCandidateId: "candidate:1",
  },
  previewOpen: true,
  onClose: () => {},
  onSelect: () => {},
  onAdvance: () => {},
  onPreview: () => {},
  onClosePreview: () => {},
  onConfirmPreview: () => {},
  canConfirmPreview: true,
}));
check(previewWizardHtml.includes("增加特殊关注") && previewWizardHtml.includes("确认并保存到项目"), "wizard renders the separate special-attention preview action");
const confirmWizardHtml = render(element("MonitoringWizardView", {
  wizard: { ...wizard, step: 4, summary: { modeText: "日常监查", scopeDescription: "当前完整数据", dataCutoffText: "2026-08-28", comparisonRangeText: "同项目已发布结果", selectedRuleCount: 1 } },
  onClose: () => {},
  onSelect: () => {},
  onAdvance: () => {},
  onPreview: () => {},
  onClosePreview: () => {},
  onConfirmPreview: () => {},
}));
check(confirmWizardHtml.includes("确认并开始监查") && confirmWizardHtml.includes("工作项总数"), "wizard confirmation step renders the start action and server-owned work-item placeholder");

const historyHtml = render(element("MonitoringHistoryDrawer", { history: { rows: [{ publicRunToken: "run:1", modeText: "日常监查", dataCutoffText: "2026-08-20", comparisonRangeText: "当前完整数据", statusText: "本次监查已完成", resultAvailable: true, mainAction: "查看本次结果" }] }, selectedPublicRunToken: "run:1", onSelect: () => {}, onClose: () => {} }));
check(historyHtml.includes("历史") && historyHtml.includes("本次监查已完成"), "history drawer renders server status text");
check(historyHtml.includes("查看本次结果"), "history action uses server-owned main action");
check(!historyHtml.includes("run_state") && !historyHtml.includes("100%"), "history hides machine state and progress percentage");

const identityHtml = render(element("MonitoringPublicResultIdentityStrip", { identity: { mode_text: "日常监查", data_cutoff_text: "2026-08-28", site_scope_text: "中心 006、中心 010" } }));
check(identityHtml.includes("本次结果范围") && identityHtml.includes("数据截止 2026-08-28") && identityHtml.includes("中心 006、中心 010"), "result identity strip renders cutoff and site scope without duplicating mode");
check(!/日常监查[\s·]*日常监查/.test(identityHtml), "identity strip alone does not invent a duplicated mode banner");
check((identityHtml.match(/data-monitoring-result-identity/g) || []).length === 1, "result identity strip is a single non-overlapping band");
check(!identityHtml.includes("result-context:") && !identityHtml.includes("snapshot_ref"), "result identity strip hides public routing internals");
const centerIdentityHtml = render(element("MonitoringPublicResultIdentityStrip", { identity: { mode_text: "日常监查", data_cutoff_text: "2026-08-28", site_scope_text: "中心 006、中心 010" }, siteScopeText: "中心 006" }));
check(centerIdentityHtml.includes("中心 006") && !centerIdentityHtml.includes("中心 006、中心 010"), "center result identity strip renders the active center label instead of the project scope");

const normalizedPublicResult = bundled.normalizePublicProductPayload({
  identity: { project_ref: "synthetic-project", site_ref: "site-006" },
  resultContextToken: "result-context:test",
  projection: {
    measures: [{ measure_ref: "measure-006", site_ref: "site-006", numerator: 2, denominator: 12, coverage_state: "complete" }],
    current_risks: [
      { risk_ref: "risk-1", risk_instance_ref: "risk-instance-1", site_ref: "site-006", subject_ref: "subject-1", severity: "high", domain: "ae" },
      { risk_ref: "risk-2", risk_instance_ref: "risk-instance-2", site_ref: "site-006", subject_ref: "subject-1", severity: "medium", domain: "ae" },
    ],
    center_map: { cells: [{ site_ref: "site-006", measure_refs: ["measure-006"], individual_risk_refs: ["risk-1", "risk-2"] }] },
  },
});
check(normalizedPublicResult.projection.centers[0].coverageState === "complete", "center inherits verified coverage from its referenced measure");
check(normalizedPublicResult.projection.centers[0].coverageLabel === "完整", "center renders the verified coverage as native Chinese");
check(normalizedPublicResult.projection.centers[0].risks.length === 2, "center keeps its referenced risk prompts for center summary counts");
check(normalizedPublicResult.projection.centers[0].siteLabel === "中心 006", "center hides the synthetic internal site token behind a user label");
check(normalizedPublicResult.projection.currentRisks.every((risk) => risk.siteLabel === "中心 006"), "risk rows keep the user-facing center label");
check(bundled.publicResultSiteScopeText(normalizedPublicResult, {}) === "中心 006", "project result scope derives its audience center labels from the projection");
check(bundled.publicResultSiteScopeText({ projection: { centers: [], raw: {} } }, { site_ref: "s7-site-006" }) === "中心 6", "subject result scope never falls back to the internal site token");

const publicProgressHtml = render(element("MonitoringPublicProgressSurface", {
  progress: {
    runState: "completed",
    runStatusText: "分析已结束",
    publicationStatusText: "分析已结束，结果整理未完成",
    progressText: "已处理 8/8 项（100%）",
    outcomeLabel: "已完成",
    percent: 100,
    stageProgress: [],
    currentWork: [],
    currentWorkRemaining: 0,
    currentWorkEmptyText: "",
    latestUpdates: [],
    scope: { modeText: "日常监查", basisText: "全面分析", dataCutoffText: "2026-08-28", scopeVersionText: "本次范围" },
    resultAvailable: false,
  },
  error: null,
  loading: false,
  onRefresh: () => {},
  onBack: () => {},
  onOpenResult: () => {},
}));
check(publicProgressHtml.includes("分析已结束，结果整理未完成"), "public progress keeps the unpublished-result Chinese status");
check(!publicProgressHtml.includes(">停止</button>") && !publicProgressHtml.includes(">继续</button>"), "medical monitor progress hides operator controls");

const css = fs.readFileSync(path.join(here, "medicalMonitoringProductLoop.css"), "utf8");
check(css.includes("max-height: 56px"), "workbar height target is compact");
check(css.includes(":focus-visible"), "product controls have visible focus treatment");
check(css.includes("prefers-reduced-motion"), "product loop respects reduced motion");
check(!/linear-gradient|backdrop-filter|blur\(/.test(css), "product loop does not add gradient or glass effects");

console.log(`medicalMonitoringProductLoopRender: ${passed} passed`);
