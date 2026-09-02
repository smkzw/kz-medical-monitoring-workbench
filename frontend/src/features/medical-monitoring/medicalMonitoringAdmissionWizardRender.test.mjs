import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import { createRequire } from "node:module";
import { fileURLToPath } from "node:url";
import { buildSync } from "esbuild";
import { findMonitoringForbiddenTerms } from "./medicalMonitoringProgressProjection.mjs";

let passed = 0;
function check(condition, message) {
  assert.ok(condition, message);
  passed += 1;
}

const here = path.dirname(fileURLToPath(import.meta.url));

// Bundle the JSX render fixture with the already-installed esbuild so the
// wizard markup can be asserted without adding a DOM renderer dependency.
const bundlePath = path.join(here, ".monitoring-admission-wizard-render-bundle.cjs");
buildSync({
  entryPoints: [path.join(here, "medicalMonitoringAdmissionWizardRender.test.jsx")],
  bundle: true,
  outfile: bundlePath,
  format: "cjs",
  platform: "node",
  jsx: "automatic",
  loader: { ".css": "empty" },
  define: { "process.env.NODE_ENV": '"test"' },
  logLevel: "silent",
});
let renders;
let generatedAdmissionFixture;
try {
  const require = createRequire(import.meta.url);
  ({ renders, generatedAdmissionFixture } = require(bundlePath));
} finally {
  fs.rmSync(bundlePath, { force: true });
}

function stripTags(html) {
  return html.replace(/<[^>]*>/g, " ").replace(/\s+/g, " ").trim();
}

function withoutTechnical(html) {
  return html.replace(/<details[\s\S]*?<\/details>/g, " ");
}

// One primary action in every rendered state.
for (const [name, html] of Object.entries(renders)) {
  check(
    html.split('class="monitoring-admission-primary"').length - 1 === 1,
    `${name} renders exactly one primary action`,
  );
}

// Shared frame: heading, three-step indicator, aria labelling.
check(renders.input.includes("数据接入"), "wizard heading rendered");
check(renders.input.includes('aria-label="数据接入向导"'), "wizard aria label");
check(renders.input.includes("第 一 步") && renders.input.includes("选择数据"), "step one rendered");
check(renders.input.includes("第 二 步") && renders.input.includes("查看系统识别结果"), "step two rendered");
check(renders.input.includes("第 三 步") && renders.input.includes("核对系统识别"), "step three rendered");
check(renders.input.includes('aria-current="step"'), "current step exposed to assistive tech");
check(
  renders.input.split('aria-current="step"').length - 1 === 1,
  "only the current step is aria-current",
);
check(renders.input.includes("系统先保留副本再识别结构，原始文件保持不变"), "impact statement on entry");

// Step one: labelled input, format hint, disabled primary until valid.
check(renders.input.includes('id="monitoring-admission-files"'), "browser-native folder picker rendered");
check(renders.input.includes("选择本机数据文件夹"), "folder picker is the primary data choice");
check(renders.input.includes("无法选择文件夹时，手动填写数据位置"), "manual path is a collapsed fallback");
check(renders.input.includes('<label for="monitoring-admission-source">数据位置</label>'), "fallback source field remains labelled");
check(renders.input.includes("选择文件夹后即可开始导入"), "disabled import explains the next action");
check(renders.input.includes('aria-disabled="true"'), "disabled import exposes its state");
check(renders.input.includes('disabled=""'), "import disabled without source");
check(renders.input.includes(".csv / .xls / .xlsx / .xlsm"), "supported formats named");
check(!renders.input.includes("monitoring-admission-warning"), "no warning on clean input");
check(renders.typed.includes('value="/data/listings/2026-08"'), "typed source kept in field");
check(!renders.typed.includes('disabled=""'), "import enabled with valid source");
check(
  renders.inputWarning.includes("数据位置开头或结尾不能包含空格"),
  "edge-space warning rendered",
);
check(renders.creating.includes(">正在导入…</button>") && renders.creating.includes('disabled=""'),
  "creating keeps a single disabled primary");
check(renders.creating.includes("monitoring-admission-warning") === false, "no validation noise while importing");

// Reading phase: polite status line, no fabricated numbers.
check(renders.reading.includes('role="status"'), "reading uses a status role");
check(renders.reading.includes("正在识别数据结构"), "reading copy");
check(!renders.reading.includes("张数据表"), "reading shows no premature counts");

// Review step: structure summary first, tables next, technical details last
// and collapsed.
check(renders.review.includes("2 个文件 · 2 张数据表 · 164 行数据"), "summary text rendered");
check(
  renders.review.indexOf("2 个文件") < renders.review.indexOf("访视列表"),
  "summary precedes table blocks",
);
check(renders.review.includes('aria-label="数据表 访视列表"'), "table region labelled");
check(renders.review.includes("128 行 · 4 列 · 来源 visit_listings.csv"), "table meta rendered");
check(renders.review.includes("缺失 2"), "missing count rendered");
check(renders.review.includes("2026-01-12 ~ 2026-08-30"), "date range rendered");
check(renders.review.includes("受试者标识") && renders.review.includes("访视"), "role chips rendered");
check(renders.review.includes("<details"), "technical details collapsed by default");
check(renders.review.includes(">技术详情</summary>"), "technical details summary label");
const technicalOpen = renders.review.indexOf("<details");
const manifestValue = generatedAdmissionFixture().technical_details.manifest_hash;
const manifestIndex = renders.review.indexOf(manifestValue);
check(
  technicalOpen > -1 && manifestIndex > technicalOpen && renders.review.indexOf("</details>") > manifestIndex,
  "hash values stay inside the collapsed technical region",
);
check(renders.review.includes("数据清单校验值"), "manifest labelled in product language");
check(renders.review.includes("来源版本标识") && renders.review.includes("单元格定位索引标识"),
  "internal identities labelled in product language");
check(renders.review.includes(">下一步：核对系统识别</button>"), "review primary advances");
check(!renders.review.includes('role="alert"'), "clean review raises no alert");

// Confirm step: pending human-judgement fields, back navigation.
check(renders.confirm.includes("识别出可能的数据含义"), "pending note rendered");
check(renders.confirm.includes("访视列表 · 受试者编号"), "pending field naming");
check(renders.confirm.includes(">返回上一步</button>"), "back action rendered");
check(renders.confirm.includes("不会用于监查分析"), "candidate boundary stated");
check(
  renders.confirmNoPending.includes("本批数据没有需要人工判断的字段"),
  "no-pending copy rendered",
);

// Done: outcome, no exposed record identity, replacement guidance, restart primary.
check(renders.done.includes("数据已完成接入"), "done outcome rendered");
check(!renders.done.includes("adm-20260902-0001"), "attempt record identity remains hidden");
check(renders.done.includes("已接入的数据版本不会被覆盖"), "replacement guidance");
check(renders.done.includes(">再接入一批数据</button>"), "done primary restarts");

// Failures: alert role, server text, concrete guidance, retry hierarchy.
check(renders.failedRetry.includes('role="alert"'), "failure uses alert role");
check(renders.failedRetry.includes("未找到可导入的数据目录"), "server message kept");
check(renders.failedRetry.includes("修正后重新开始导入"), "guidance line rendered");
check(renders.failedRetry.includes(">重试</button>"), "retry primary");
check(renders.failedRetry.includes(">重新开始</button>"), "restart secondary");
check(!renders.failedRetry.includes('data-admission-phase="ready"'), "failure phase exposed for styling");
check(renders.failedBlocked.includes(">重新开始</button>") && !renders.failedBlocked.includes(">重试</button>"),
  "non-retryable failure swaps primary to restart");
check(renders.failedBlocked.includes("请返回实际研究项目"), "blocked failure gives a user-owned next action");

// User-visible text excludes engineering terms; technical region is exempt
// because paths, hashes and internal identities are contracted to live there.
for (const [name, html] of Object.entries(renders)) {
  const hits = findMonitoringForbiddenTerms([stripTags(withoutTechnical(html))]);
  check(hits.length === 0, `render ${name} excludes forbidden terms${hits.length ? `: ${JSON.stringify(hits)}` : ""}`);
}

// Style contract: Kangzhe single orange accent, risk red only on failure,
// visible focus, tabular numerals, internal wrapping, no gradients.
const css = fs.readFileSync(path.join(here, "medicalMonitoringAdmissionWizard.css"), "utf8");
check(css.includes(":focus-visible"), "visible focus styles");
check(css.includes("font-variant-numeric: tabular-nums"), "tabular numerals");
check(css.includes("flex-wrap: wrap"), "internal wrapping for narrow widths");
check(css.includes("var(--monitoring-orange, #e96828)"), "single orange accent token");
check(css.includes("var(--monitoring-line, #dce3e9)"), "shared line token");
check(
  css.includes(".monitoring-admission-alert") && css.includes("var(--monitoring-red, #b83b3b)"),
  "risk red reserved for the failure alert",
);
check(!/linear-gradient|backdrop-filter|blur\(/.test(css), "no gradients or glass effects");
check(css.includes("overflow-wrap: anywhere"), "long technical values wrap internally");
check(css.includes(".monitoring-admission-technical summary"), "collapsed region styled");
check(/\.monitoring-admission-primary:disabled\s*\{[^}]*background: #eef1f4/.test(css), "disabled import is visually quiet");
check(css.includes("@media (max-width: 900px)"), "narrow-width adjustment present");

console.log(`medicalMonitoringAdmissionWizardRender: ${passed} passed`);
