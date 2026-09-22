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
check(renders.input.includes("第 二 步") && renders.input.includes("查看导入概况"), "step two rendered");
check(renders.input.includes("第 三 步") && renders.input.includes("处理少量疑点"), "step three rendered");
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

// Review step: structure summary first and tables next. Internal hashes and
// storage identities never reach the user surface.
check(renders.review.includes("2 个文件 · 2 张数据表 · 164 行数据"), "summary text rendered");
check(
  renders.review.indexOf("2 个文件") < renders.review.indexOf("访视列表"),
  "summary precedes table blocks",
);
check(renders.review.includes("查看 2 张表的结构"), "table structures stay in one optional disclosure");
check(renders.review.includes("128 行 · 4 列"), "table meta rendered");
check(renders.review.includes("缺失 2"), "missing count rendered");
check(renders.review.includes("2026-01-12 ~ 2026-08-30"), "date range rendered");
check(!renders.review.includes("受试者标识"), "deterministic role guesses stay out of the overview");
const manifestValue = generatedAdmissionFixture().technical_details.manifest_hash;
check(!renders.review.includes(manifestValue), "manifest hash stays out of the product UI");
check(!renders.review.includes("校验值"), "file hashes stay out of the product UI");
check(!renders.review.includes("来源版本标识"), "source revision ids stay out of the product UI");
check(!renders.review.includes("单元格定位索引标识"), "locator ids stay out of the product UI");
check(renders.review.includes(">下一步：让系统核对字段</button>"), "review primary advances");
check(!renders.review.includes('role="alert"'), "clean review raises no alert");

// Before mapping, the system explains missing study evidence in plain Chinese
// and asks only for the two files it cannot safely infer by itself. Optional
// context stays clearly optional and never blocks mapping.
check(renders.documentsMissing.includes("还需要 2 份研究文件"), "missing-document purpose is explicit");
check(
  renders.documentsMissing.includes("通常不需要您逐列核对"),
  "missing-document guidance promises system-led recognition",
);
check(renders.documentsMissing.includes("当前研究方案"), "protocol uses a medical-facing label");
check(renders.documentsMissing.includes("当前 eCRF"), "eCRF uses a recognizable label");
check(
  renders.documentsMissing.split(">一次选择研究文件</").length - 1 === 1,
  "one batch picker replaces per-role confirmation work",
);
check(
  renders.documentsMissing.includes('multiple=""'),
  "the research document picker accepts a batch",
);
check(
  renders.documentsMissing.includes('accept=".docx,.pdf,.xlsx"'),
  "the batch picker accepts all supported research document formats",
);
check(
  renders.documentsMissing.includes(">请先添加所需文件</button>")
    && renders.documentsMissing.includes('aria-disabled="true"'),
  "mapping action stays disabled until required evidence is present",
);
check(
  !renders.documentsMissing.includes('aria-label="数据表识别摘要"'),
  "mapping questions stay hidden while study evidence is incomplete",
);
check(renders.documentsReady.includes("研究文件已准备好"), "ready evidence is acknowledged");
check(
  renders.documentsReady.includes('aria-label="数据表识别摘要"'),
  "mapping summary appears only after required evidence is ready",
);
check(renders.documentsFailed.includes("当前研究方案"), "readiness failure preserves known document status");
check(renders.documentsFailed.includes("已识别"), "readiness failure keeps completed work visible");
check(renders.documentsFailed.includes(">重新核对研究文件</button>"), "readiness failure offers one plain retry action");
check(renders.documentsFailed.includes('role="alert"'), "readiness failure is announced accessibly");
check(
  renders.documentsCrossChecking.includes("系统正在复核最后几个分歧"),
  "critique progress stays in plain Chinese",
);
check(
  renders.documentsCrossChecking.includes("eCRF 修订说明.pdf")
    && renders.documentsCrossChecking.includes('disabled=""'),
  "critique keeps the named file visible and upload disabled",
);
check(
  renders.documentsContentDifference.includes("研究方案：研究方案V2.0.docx")
    && renders.documentsContentDifference.includes("当前项目：MG-K10-SAR-001")
    && renders.documentsContentDifference.includes("文件内容：MG-K10-SAR-01"),
  "content differences show the medical-facing expected and observed values",
);
check(
  renders.documentsContentDifference.includes("差异不影响本次监查，继续使用"),
  "an overridable difference has one consequence-based action",
);
for (const internal of ["project_identity", "requires_confirmation", "mismatch", "角色 protocol"]) {
  check(!renders.documentsContentDifference.includes(internal), `content decision hides internal value: ${internal}`);
}

// Confirm step: plain summary leads, engineering field list stays collapsed.
check(
  renders.confirm.includes("系统已自动识别 2 个字段，其中 1 个需要您确认"),
  "plain recognition headline rendered",
);
check(
  renders.confirmDrafting.indexOf("系统已自动识别")
    < renders.confirmDrafting.indexOf("monitoring-admission-question"),
  "headline precedes the question cards",
);
check(renders.confirm.includes('aria-label="数据表识别摘要"'), "table summary region labelled");
check(renders.confirm.includes("2 个字段 · 1 个待确认"), "per-table summary counts rendered");
check(renders.confirm.includes("确认前不会生成可用于监查的数据"), "candidate/fact boundary stated");
check(renders.confirm.includes(">返回上一步</button>"), "back action rendered");
check(renders.confirm.includes(">采用系统识别结果</button>"), "system adopts the recognition draft itself");
check(renders.confirm.includes("查看全部字段的识别结果"), "collapsed full-recognition digest exists");
check(
  renders.confirm.indexOf("<details") < renders.confirm.indexOf("查看全部字段的识别结果"),
  "full digest stays inside a collapsed region",
);
for (const engineering of ["重点优先", "全部建议", 'aria-label="搜索字段"', "建议核对", "字段对应技术值"]) {
  check(!renders.confirm.includes(engineering), `engineering control hidden from default view: ${engineering}`);
}

// Question guide: only the current substantive ambiguity is prominent.
check(!renders.confirm.includes("低置信度"), "internal attention label stays hidden");
check(!renders.confirmDrafting.includes("<span>访视列表 · 访视日期</span>"), "question hides table and column codes");
check(renders.confirmDrafting.includes("请做一个医学选择"), "question uses a plain medical heading");
check(renders.confirmDrafting.includes("请确认这一列是否为实际访视日期。"), "harness question copy rendered");
check(renders.confirmDrafting.includes("126/128 条非空"), "value-profile evidence rendered");
check(renders.confirmDrafting.includes("2 个样例默认隐藏"), "sample values stay hidden by default");
check(renders.confirmDrafting.includes("查看系统判断依据"), "technical evidence is collapsed by default");
check(!renders.confirm.includes("确认无误"), "answer controls wait for the adopted draft");
check(!renders.confirm.includes("subject_id"), "technical role stays out of the question surface");

// Drafting: answer controls appear and confirmation waits for every answer.
check(renders.confirmDrafting.includes("已完成 0/1"), "answer progress rendered");
check(renders.confirmDrafting.includes(">系统判断正确</button>"), "one-tap confirmation offered");
check(renders.confirmDrafting.includes(">说明实际含义</button>"), "free-text alternative offered");
check(
  renders.confirmDrafting.includes('aria-label="补充实际医学含义"') === false,
  "note field appears only after choosing 另有情况",
);
check(
  renders.confirmDrafting.includes('aria-disabled="true"'),
  "confirmation stays disabled while a question is unanswered",
);
check(renders.confirmDraftingAnswered.includes("已完成 1/1"), "answered progress rendered");
check(!renders.confirmDraftingAnswered.includes("请做一个医学选择"), "answered card leaves the active view");
check(
  renders.confirmDraftingAnswered.includes("系统正在完成字段识别"),
  "system completes automatically after every question is answered",
);

// No-questions draft: system adopted everything, direct confirmation.
check(
  renders.confirmNoQuestions.includes("全部对应关系清晰，无需您补充判断"),
  "zero-question headline rendered",
);
check(
  renders.confirmNoQuestions.includes("正在自动保存字段对应关系，无需您逐项核对"),
  "zero-question draft completes without user confirmation",
);

// Done: automatic fact generation and a plain ready state, without identities.
check(renders.done.includes("系统已完成字段识别"), "done outcome uses plain Chinese recognition copy");
check(!renders.done.includes("adm-20260902-0001"), "attempt record identity remains hidden");
check(renders.done.includes("无需逐项确认"), "post-confirm facts generate automatically");
check(renders.done.includes("正在生成监查数据"), "done primary reports automatic progress");
check(renders.doneReady.includes("监查数据已准备完成"), "ready outcome names the user result");
check(renders.doneReady.includes("已核对 640 个原始数据位置"), "ready outcome explains automatic source alignment");
check(renders.doneReady.includes("已整理 3 张数据表、128 条记录、640 个数据项"), "ready outcome summarizes generated data");
check(renders.doneReady.includes("无需逐项检查"), "ready outcome removes manual verification burden");
check(renders.doneReady.includes("进入医学监查"), "ready outcome offers one clear next action");

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

// User-visible text excludes engineering terms; collapsed technical regions
// are exempt because digests and internal identities are contracted to live
// there.
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
check(css.includes(".monitoring-admission-question"), "medical question cards styled");
check(css.includes(".monitoring-admission-table-summary"), "recognition summary styled");
check(css.includes("position: sticky"), "ready-step actions remain visible while reviewing long lists");

console.log(`medicalMonitoringAdmissionWizardRender: ${passed} passed`);
