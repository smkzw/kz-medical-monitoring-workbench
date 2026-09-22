// Phase C C2 product-loop admission integration: the loop mounts exactly one
// data-admission card plus the inline MedicalMonitoringAdmissionWizard on the
// project start surface, and touches nothing else. Without a DOM renderer the
// deterministic contract checks combine three established signals: static
// markup of the exported subcomponents, a static mount of the wizard with
// exactly the props the loop passes, and whitespace-normalized source pins of
// the wiring (same method as medicalMonitoringContinuityIntegration.test.mjs).
//
// Contract sources:
// - context/medical_monitoring_ai_native_implementation_plan_v2_20260901.md §6 (阶段 C item 1)
// - plans/codex_execution_mm-c2-admission-wizard.md work item 3
// - packages/medical_monitoring/api/r7_product/admission_routes.py (C1 payload shapes)

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

function bundle(entryName, outfile) {
  const bundlePath = path.join(here, outfile);
  buildSync({
    entryPoints: [path.join(here, entryName)],
    bundle: true,
    format: "cjs",
    platform: "node",
    outfile: bundlePath,
    jsx: "automatic",
    loader: { ".css": "empty" },
    define: { "process.env.NODE_ENV": '"test"' },
    // Keep React external so the bundled components share the dispatcher of
    // the react-dom/server copy; the wizard's hooks need one single copy.
    packages: "external",
    logLevel: "silent",
  });
  try {
    return require(bundlePath);
  } finally {
    fs.rmSync(bundlePath, { force: true });
  }
}

// Bundling the loop proves the admission import graph resolves end to end:
// loop -> admission wizard -> wizard state -> product api (C1 transport).
const loop = bundle("MedicalMonitoringProductLoop.jsx", ".admission-loop-bundle.cjs");
const wizardBundle = bundle("MedicalMonitoringAdmissionWizard.jsx", ".admission-wizard-bundle.cjs");
const wizardState = await import("./medicalMonitoringAdmissionWizardState.mjs");

function element(bundled, name, props = {}) {
  return createElement(bundled[name], props);
}

function render(value) {
  // Load the server renderer only after the JSX bundle has been built.
  return require("react-dom/server").renderToStaticMarkup(value);
}

// --- generated C1 admission payloads (deterministic, no real project data) ---
function generatedAdmissionPayload({ attemptId = "att-c2-0001", tableCount = 2 } = {}) {
  const tables = Array.from({ length: tableCount }, (_, index) => ({
    name: `受试者列表${index + 1}`,
    source_file: `listing-part${index + 1}.xlsx`,
    row_count: 12 + index,
    column_count: 3,
    columns: [
      { name: "受试者编号", inferred_type: "text", missing_count: 0, distinct_count: 12 + index, samples: ["S001", "S002"], date_range: null, suggested_roles: ["受试者标识"] },
      { name: "访视名称", inferred_type: "text", missing_count: 1, distinct_count: 4, samples: ["V1"], date_range: null, suggested_roles: ["访视"] },
      { name: `备注${index + 1}`, inferred_type: "text", missing_count: 0, distinct_count: 2, samples: [], date_range: null, suggested_roles: [] },
    ],
  }));
  return {
    schema_version: "mm-c1-data-admission-v1",
    project_id: "proj-c2",
    attempt_id: attemptId,
    state: "profile_ready",
    summary: {
      files: tableCount,
      tables: tableCount,
      rows: tables.reduce((total, table) => total + table.row_count, 0),
    },
    tables,
    technical_details: {
      manifest_hash: `manifest-${attemptId}`,
      files: tables.map((table, index) => ({
        path: table.source_file,
        size: 1024 * (index + 1),
        sha256: `sha-${attemptId}-${index + 1}`,
      })),
      revision_ids: [`srcc1-${attemptId}-1`],
      snapshot_ids: [`snap-${attemptId}-1`],
      locator_index_ids: [`loc-${attemptId}-1`],
      profile_ids: [`prof-${attemptId}-1`],
    },
  };
}

// --- card render: closed state offers exactly one primary entry ---
const cardClosedHtml = render(element(loop, "MonitoringAdmissionCard", { open: false, onToggle: () => {} }));
check(cardClosedHtml.includes('data-monitoring-admission-card'), "admission card is a single identifiable card");
check(cardClosedHtml.includes('aria-label="数据接入"'), "admission card keeps a native Chinese region name");
check(cardClosedHtml.includes("数据接入") && cardClosedHtml.includes("原始文件保持不变"), "admission card copy states the source-preservation promise without internal terms");
check(cardClosedHtml.includes('aria-expanded="false"'), "closed card exposes the toggle state");
check(cardClosedHtml.includes(">开始数据接入</button>"), "closed card offers exactly one entry action");
check(/monitoring-product-button\s+is-primary/.test(cardClosedHtml), "closed card entry action is the single primary control");
check(!cardClosedHtml.includes("attempt") && !cardClosedHtml.includes("token"), "admission card never exposes machine identities");

// --- card render: open state demotes to a non-primary toggle ---
const cardOpenHtml = render(element(loop, "MonitoringAdmissionCard", { open: true, onToggle: () => {} }));
check(cardOpenHtml.includes('aria-expanded="true"'), "open card exposes the expanded toggle state");
check(cardOpenHtml.includes(">收起数据接入</button>"), "open card offers the collapse action");
check(!/monitoring-product-button\s+is-primary/.test(cardOpenHtml), "open card button is not primary so the wizard keeps the single primary action");

// --- wizard mount smoke: exactly the props the loop passes (projectId + api) ---
const stubApi = {
  createDataAdmission: () => Promise.resolve(generatedAdmissionPayload()),
  createDataAdmissionUpload: () => Promise.resolve(generatedAdmissionPayload()),
  getDataAdmissionStatus: () => Promise.resolve(generatedAdmissionPayload()),
  getDataAdmissionProfile: () => Promise.resolve(generatedAdmissionPayload()),
};
const wizardMountHtml = render(element(wizardBundle, "MedicalMonitoringAdmissionWizard", { projectId: "proj-c2", api: stubApi }));
check(wizardMountHtml.includes('aria-label="数据接入向导"'), "mounted wizard renders its accessible region");
check(wizardMountHtml.includes('id="monitoring-admission-files"'), "mounted wizard starts with the browser-native folder picker");
check(wizardMountHtml.includes("选择数据") && wizardMountHtml.includes("查看导入概况") && wizardMountHtml.includes("处理少量疑点"), "mounted wizard renders the three native Chinese steps");
check(wizardMountHtml.includes("disabled"), "wizard entry primary action waits for selected files or a fallback location");

const mappingFlowCalls = [];
const startedMapping = await wizardBundle.loadOrStartAdmissionMapping({
  listDataAdmissionMappingCandidates: async () => {
    mappingFlowCalls.push("list");
    const error = new Error("尚未生成");
    error.detail = { code: "mapping_candidates_not_found" };
    throw error;
  },
  startDataAdmissionMappingCandidates: async () => {
    mappingFlowCalls.push("start-dual");
    return { state: "generating", candidates: [] };
  },
}, "proj-c2", "att-c2-0001");
check(
  mappingFlowCalls.join(",") === "list,start-dual",
  "a genuinely new admission starts the dual analysis after the empty read",
);
check(startedMapping.state === "generating", "new dual analysis returns the generating state");

// --- wizard ready phase on the real state machine proves the C1 payload
// contract flows through the mounted component without exposing internal
// storage identities ---
const admittedState = [
  wizardState.createAdmissionWizardState({ projectId: "proj-c2" }),
  { type: "source-dir-change", value: "/tmp/mm-c2-generated-listings" },
  { type: "import-start" },
  { type: "import-created", payload: generatedAdmissionPayload() },
].reduce(wizardState.admissionWizardReducer);
const readyState = wizardState.admissionWizardReducer(admittedState, { type: "profile-loaded", payload: generatedAdmissionPayload() });
check(readyState.phase === "ready" && readyState.profile, "generated C1 payload drives the wizard to the ready phase");
const readyHtml = render(element(wizardBundle, "MedicalMonitoringAdmissionWizardView", { state: readyState }));
const summaryIndex = readyHtml.indexOf("2 个文件 · 2 张数据表 · 25 行数据");
check(summaryIndex !== -1, "ready wizard renders the generated structure summary");
check(!readyHtml.includes("技术详情"), "ready wizard hides engineering details");
check(!readyHtml.includes("manifest-att-c2-0001"), "ready wizard hides manifest identities");
check(readyHtml.includes("查看 2 张表的结构"), "table details remain available in one collapsed disclosure");
check(!readyHtml.includes("受试者标识"), "unverified role guesses stay out of the overview");

// --- wiring pins: whitespace-normalized source sequences of the loop ---
const source = fs.readFileSync(path.join(here, "MedicalMonitoringProductLoop.jsx"), "utf8");
const wizardSource = fs.readFileSync(path.join(here, "MedicalMonitoringAdmissionWizard.jsx"), "utf8");
const compact = (text) => text.replace(/\s+/g, "");
const src = compact(source);
const wizardSrc = compact(wizardSource);
const needle = (text) => compact(text);

{
  check(
    src.includes(needle(`import { MedicalMonitoringAdmissionWizard } from "./MedicalMonitoringAdmissionWizard.jsx";`)),
    "loop imports the admission wizard",
  );
  check(
    src.includes(needle(`const [admissionOpen, setAdmissionOpen] = useState(false);`)),
    "admission open state is declared beside the wizard state",
  );
  check(
    src.includes(needle(`{!loadingBody && !resultLoaded && !publicRunToken ? (\n        <>\n          <section className="monitoring-product-start-surface"><strong>{admissionOnly ? "先核对字段对应关系" : startSurfaceTitle}</strong><span>{admissionOnly ? setupHistoryError?.text : startSurfaceCopy}</span></section>\n          <MonitoringAdmissionCard open={admissionOpen} onToggle={() => setAdmissionOpen((value) => !value)} />\n          {admissionOpen ? <MedicalMonitoringAdmissionWizard key={normalizedProjectId} projectId={normalizedProjectId} api={api} onAdmitted={retryPage} /> : null}\n        </>\n      ) : null}`)),
    "card and wizard mount only on the project start-surface gate",
  );
  check(
    src.includes(needle(`<MedicalMonitoringAdmissionWizard key={normalizedProjectId} projectId={normalizedProjectId} api={api} onAdmitted={retryPage} />`)),
    "wizard receives the project identity and refreshes when monitor-ready data is complete",
  );
  passed += 4;
}

check(
  wizardSrc.includes(needle(`const payload = await api.analyzeStudyDocuments(
        state.projectId,
        state.attemptId,
        files,
      );`)),
  "one batch choice starts system-led dual document analysis",
);
check(
  wizardSrc.includes("api.startDataAdmissionMappingCandidates")
    && wizardSrc.includes("mapping_candidates_not_found"),
  "a first admission automatically starts dual mapping when no candidates exist",
);
check(
  wizardSrc.includes(needle('mappingState.payload?.state !== "generating"')),
  "only active generation is polled; terminal attention waits for a recovery action",
);

// --- result navigation and board gating unchanged ---
{
  check(
    src.includes(needle(`navigate("overview", { result_context_token: entry.resultContextToken, public_run_token: "" })`)),
    "result entry navigation patch is unchanged",
  );
  check(
    src.includes(needle(`<ProductRouteTabs route={route} resultLoaded={resultLoaded} onOverview={() => navigate("overview")} />`)),
    "result route tabs render unchanged",
  );
  check(
    src.includes(needle(`const onWorkbarAction = useCallback((target) => {\n    if (target === "wizard") openWizard();\n    else if (target === "history") setHistoryOpen(true);\n    else if (target === "progress") goToProgress();\n    else if (target === "result") openResult();\n    else if (target === "overview") navigate("overview", { public_run_token: "", result_context_token: "" });\n  }, [goToProgress, navigate, openResult, openWizard]);`)),
    "workbar action routing is unchanged",
  );
  check(
    src.includes(needle(`const loadingBody = setupHistoryLoading || resultLoading || entryLoading;`)),
    "board loading gate excludes admission state",
  );
  check(
    src.includes(needle(`const admissionOnly = setupHistoryError?.code === "run_data_not_ready";`))
      && src.includes(needle(`const productStatus = resultError || (setupHistoryError && !admissionOnly) ? "unavailable" : admissionOnly ? "admission_ready" : loadingBody ? "loading" : productState.kind;`)),
    "page status keeps pre-fact admission available without synthetic setup",
  );
  check(!src.includes("medical-writing") && !src.includes("MedicalWriting"), "loop keeps importing nothing from medical-writing surfaces");
  passed += 6;
}

// --- card CSS follows the product visual system ---
const css = fs.readFileSync(path.join(here, "medicalMonitoringProductLoop.css"), "utf8");
check(css.includes(".monitoring-admission-card"), "admission card ships product-loop CSS");
check(/\.monitoring-admission-card\s*\{[^}]*border-left: 3px solid var\(--monitoring-product-orange\)/.test(css), "admission card uses the product orange accent like the workbar");
check(!/linear-gradient|backdrop-filter|blur\(/.test(css), "admission card adds no gradient or glass effects");

console.log(`medicalMonitoringAdmissionIntegration: ${passed} passed`);
