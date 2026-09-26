// W01-R26 A12/A13 render contract (finding card navigation): bundles the
// fixture with esbuild (single React copy) and asserts static markup for the
// real Finding cards (subject/site, 事件与时间窗, 状态, 分类型claims, 逐条
// source refs入口) with the exact jump-target attributes the product loop's
// navigation handlers read (data-query-finding / data-event-ref /
// data-source-evidence-id), plus the explicit empty set and the legacy
// draft-shape presentation. No DOM, no browser, no server.

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
const bundlePath = path.join(here, ".monitoring-finding-card-render-bundle.cjs");
buildSync({
  entryPoints: [path.join(here, "medicalMonitoringFindingCardRender.test.jsx")],
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
try {
  const require = createRequire(import.meta.url);
  ({ renders } = require(bundlePath));
} finally {
  fs.rmSync(bundlePath, { force: true });
}

const { findingCard, empty, legacy } = renders;

// --- Finding卡：身份/subject/site/状态/时间窗逐字段呈现 ---
check(findingCard.includes('data-query-finding="finding-001"'), "finding card carries the stable finding id anchor");
check(findingCard.includes('data-finding-state="open"'), "finding card exposes the finding state");
check(findingCard.includes("s7-subject-06021"), "finding card shows the subject");
check(findingCard.includes("s7-site-006"), "finding card shows the site");
check(findingCard.includes("2026-01-01 — 2026-03-31"), "finding card shows the frozen time window");
check(findingCard.includes('data-finding-event-ref="s7-event-001"'), "finding card binds the event anchor");
passed += 6;

// --- Finding卡：分类型claims（依据/发现/行动项） ---
check(findingCard.includes('data-claim-kind="basis"') && findingCard.includes("依据：方案要求报告不良事件。"), "basis claim renders with its kind");
check(findingCard.includes('data-claim-kind="finding"') && findingCard.includes("发现：受试者出现未记录的不良反应。"), "finding claim renders with its kind");
check(findingCard.includes('data-claim-kind="action"') && findingCard.includes("行动项：请核实并补录。"), "action claim renders with its kind");
passed += 3;

// --- Finding卡：逐条source refs入口 + 事件锚跳转按钮 ---
check(findingCard.includes('data-source-evidence-id="ev-listing-001"'), "each source ref renders its own entry");
check(findingCard.includes("AE.AETERM") && findingCard.includes("rec-001"), "source entry shows the raw locator fields");
check((findingCard.match(/来源定位/g) || []).length >= 1, "source locator jump entry is present");
check(findingCard.includes('data-event-ref="s7-event-001"'), "event jump button carries the exact event anchor the loop handler reads");
check(findingCard.includes("定位关联事件"), "event jump entry is present");
passed += 5;

// --- 零发现：显式空集文案（A13） ---
check(empty.includes('data-monitoring-findings-empty'), "zero findings renders the explicit empty marker");
check(empty.includes("本轮零发现"), "zero findings keeps the explicit empty-set wording");
check(!empty.includes('data-query-finding="finding-001"'), "zero findings renders no finding cards");
passed += 3;

// --- 旧形态：drafts如实呈现并标注来源形态，不伪造Finding（⑤） ---
check(legacy.includes("data-monitoring-findings-legacy-note"), "legacy payload renders the source-shape note");
check(legacy.includes("旧版载荷形态") && legacy.includes("不伪造Finding"), "legacy note states drafts are shown as-is");
check(legacy.includes('data-query-draft="qd-legacy-001"'), "legacy drafts keep their own query draft id");
check(legacy.includes("finding-legacy"), "legacy draft shows its finding reference");
check(!legacy.includes('data-query-finding='), "legacy payload never fabricates finding cards");
passed += 5;

console.log(`medicalMonitoringFindingCardRender: ${passed} passed`);
