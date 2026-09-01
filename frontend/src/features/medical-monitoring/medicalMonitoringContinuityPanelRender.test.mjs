// R7 Slice-08C-2 panel render contract (contract §6.3): bundles the panel
// fixture with esbuild (single React copy; the panel uses useState/useMemo)
// and asserts static markup for loading / unavailable / ready / empty /
// filter-empty / truncated states, the default mid_high view, the five key
// counts, closed filter chips, the Journey/source button gates, and the
// no-internal-leak rule. No DOM, no browser, no server.

import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import { createRequire } from "node:module";
import { fileURLToPath } from "node:url";
import { buildSync } from "esbuild";

let passed = 0;
function check(condition, message) {
  assert.equal(Boolean(condition), true, message);
  passed += 1;
}

const here = path.dirname(fileURLToPath(import.meta.url));
const bundlePath = path.join(here, ".monitoring-continuity-panel-render-bundle.cjs");
buildSync({
  entryPoints: [path.join(here, "medicalMonitoringContinuityPanelRender.test.jsx")],
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
let expectedCounts;
let expectedTruncationText;
let unavailableText;
try {
  const require = createRequire(import.meta.url);
  ({ renders, expectedCounts, expectedTruncationText, unavailableText } = require(bundlePath));
} finally {
  fs.rmSync(bundlePath, { force: true });
}

function countOf(html, needle) {
  return (html.match(new RegExp(needle.replace(/[.*+?^${}()|[\]\\]/g, "\\$&"), "g")) || []).length;
}

// --- loading: short placeholder, no counts, no list, no stale numbers ---
check(renders.loading.includes('data-monitoring-continuity-state="loading"'), "loading state hook present");
check(renders.loading.includes("连续性比较"), "loading keeps the eyebrow");
check(renders.loading.includes("本轮变化加载中…"), "loading short placeholder copy");
check(!renders.loading.includes("monitoring-continuity-counts"), "loading renders no counts");
check(!renders.loading.includes("monitoring-continuity-list"), "loading renders no rows");
check(!renders.loading.includes("本轮变化暂不可查看"), "loading is not the unavailable state");
passed += 6;

// --- unavailable: single degrade text (contract §5) ---
check(renders.unavailableDefault.includes('data-monitoring-continuity-state="unavailable"'), "unavailable state hook present");
check(renders.unavailableDefault.includes(unavailableText), "default unavailable copy is the frozen text");
check(renders.unavailableDefault.includes("本轮变化暂不可查看"), "frozen text matches the contract wording");
check(renders.unavailableCustom.includes("自定义错误提示"), "custom unavailable text is shown");
check(renders.unavailableWins.includes("自定义错误提示") && !renders.unavailableWins.includes("monitoring-continuity-counts"), "unavailable takes precedence over a stale comparison");
check(!renders.unavailableDefault.includes("monitoring-continuity-list"), "unavailable renders no rows");
passed += 6;

// --- ready: title, subtitle, five key counts, closed filter chips ---
check(renders.ready.includes('data-monitoring-continuity-state="ready"'), "ready state hook present");
check(renders.ready.includes("<h2>本轮变化</h2>"), "headline is 本轮变化");
check(renders.ready.includes("已与上次监查结果比较"), "subtitle is the compared comparison text");
check(renders.readyFirstAnalysis.includes("本轮为首次全面分析，无比较基线"), "first-analysis subtitle is the other frozen text");
for (const label of ["新增", "升级", "重开", "需重新判断", "中高风险"]) {
  check(renders.ready.includes(`<dt>${label}</dt>`), `key count label ${label} rendered in the frozen order`);
}
for (const key of ["new", "upgraded", "reopened", "needs_rejudgment", "mid_high_total"]) {
  check(renders.ready.includes(`<dd data-count-key="${key}">${expectedCounts[key]}</dd>`), `key count ${key} shows the rebuilt value ${expectedCounts[key]}`);
}
check(renders.ready.includes("monitoring-continuity-count is-key"), "中高风险 is the single semantic emphasis");
check(countOf(renders.ready, 'data-severity-filter="') === 5, "severity chip set is the closed five states");
check(renders.ready.includes('data-severity-filter="mid_high"') && renders.ready.includes('aria-pressed="true"'), "default severity chip is active");
check(countOf(renders.ready, 'data-change-filter="') === 8, "change chip set is 全部变化 plus seven kinds");
check(countOf(renders.ready, 'data-object-filter="') === 4, "object chip set is 全部类别 plus three types");
check(renders.ready.includes("仅看需重新判断"), "needs-rejudgment toggle label rendered");
check(renders.ready.includes('type="checkbox"'), "toggle is a checkbox");
check(renders.ready.includes('placeholder="搜索受试者"'), "subject search input rendered");
passed += 16;

// --- ready rows: default mid_high view, tags, meta, note, reason ---
check(countOf(renders.ready, 'data-object-type="risk"') === 4, "default view shows only the four current 高/中 risk rows");
check(renders.ready.includes('data-change-kind="new"') && renders.ready.includes('data-change-kind="upgraded"') && renders.ready.includes('data-change-kind="needs_rejudgment"'), "visible rows keep wire-format change kinds");
check(renders.ready.includes("不良事件与记录一致性"), "row title rendered");
check(renders.ready.includes("中心一 · 受试者 S/01 · 2026-02-14"), "row meta line renders site · subject · date labels");
check(renders.ready.includes("本轮记录与上轮不一致，已重新分析。"), "row reason text rendered");
check(renders.ready.includes("无法直接比较 · 身份或数据不完整，需重新判断"), "row note joins data change and attention texts");
check(renders.ready.includes("<span class=\"monitoring-continuity-tag is-object\">风险</span>"), "object tag uses the public Chinese label");
check(renders.ready.includes("中 → 高"), "upgraded severity badge shows before → after");
check(!renders.ready.includes("（已关闭）"), "closed rows are hidden under the default mid_high view");
check(!renders.ready.includes("实验室复查 Query 草稿") && !renders.ready.includes("受试者 005"), "Query 草稿 rows are hidden under the default mid_high view");
check(!renders.ready.includes("监查发现跟踪项"), "monitoring output rows are hidden under the default view");
passed += 10;

// --- Journey / source gates (contract §2.4/§2.5) ---
check(countOf(renders.ready, ">进入旅程</button>") === 3, "Journey enabled for the three resolvable subjects");
check(countOf(renders.ready, "受试者时间范围待确认") === 1, "Journey gated closed with the hint for the unresolvable subject");
check(countOf(renders.ready, ">查看来源</button>") === 3, "source enabled for the rows with the usable locator pair");
check(countOf(renders.ready, "原始记录位置待确认") === 1, "source gated closed with the hint for the empty-locator row");
check(countOf(renders.ready, 'disabled=""') === 2, "exactly the two gated-closed buttons are disabled");
check(!renders.ready.includes("spine/01") && !renders.ready.includes("spine/03"), "routing identity refs are never rendered into buttons");
passed += 5;

// --- empty and filtered-empty states ---
check(renders.empty.includes("本轮没有变化记录。"), "empty comparison shows the no-records copy");
check(renders.empty.includes('<dd data-count-key="new">0</dd>'), "empty comparison shows zeroed counts");
check(renders.truncated.includes("当前筛选下没有变化记录。"), "default filter over low-only rows shows the filtered-empty copy");
check(renders.truncated.includes(expectedTruncationText), "truncated comparisons render the frozen 共 N/前 M hint");
check(!renders.ready.includes("共 201 条") && !renders.ready.includes("变化较多"), "untruncated comparisons render no hint");
passed += 5;

// --- internal-leak scan: no tokens, schemas, hashes, refs, secrets ---
{
  const needles = [
    "result_context_token",
    "response_digest",
    "snapshot_token",
    "public_run_token",
    "sha256",
    "sk-",
    "risk_instance_ref",
    "source_locator_ref",
    "risk_anchor_ref",
    "spine_ref",
    "spineRef",
    "spine_id",
    "window_start",
    "window_end",
    "s7-risk-",
    "s7-source-",
    "s7-anchor-",
    "s7-event-",
    "result-context:",
    "run:09",
    "snapshot:09",
    "continuity-row-1",
    "continuity-row-9",
    "正式事实",
    "候选信号",
    "人工复核未完成",
  ];
  for (const needle of needles) {
    for (const [name, html] of Object.entries(renders)) {
      check(!html.includes(needle), `render ${name} excludes ${JSON.stringify(needle)}`);
    }
  }
}

// --- CSS contract: design tokens, responsive breakpoints, no glass ---
{
  const css = fs.readFileSync(path.join(here, "medicalMonitoringContinuityPanel.css"), "utf8");
  check(css.includes("var(--monitoring-product-line)") && css.includes("var(--monitoring-product-orange)"), "panel reuses the r7 product design tokens");
  check(css.includes("font-variant-numeric: tabular-nums"), "key counts use tabular numerals");
  check(css.includes(".monitoring-continuity-count.is-key") && css.includes("var(--monitoring-product-orange)"), "中高风险 is the orange semantic emphasis");
  check(css.includes("@media (max-width: 900px)") && css.includes("@media (max-width: 620px)"), "responsive breakpoints kept at 900/620");
  check(!/linear-gradient|backdrop-filter|blur\(/.test(css), "no gradients or glass effects");
}

console.log(`medicalMonitoringContinuityPanelRender: ${passed} passed`);
