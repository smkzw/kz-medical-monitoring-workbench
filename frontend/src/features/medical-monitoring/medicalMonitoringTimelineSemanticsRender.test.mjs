// W05-J2 render contract (时间语义必需项): bundles the fixture with esbuild
// (single React copy) and asserts static markup for——窗外继续符号+方向读屏
// 文案（A21）、partial/待确认区精度标注（A19）、ongoing/end_unknown开-end
// 视觉（A22）、月精度区间标注，以及全无日期时的明确空态（A23：无月份刻度/
// 无假窗文案）。No DOM, no browser, no server.

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
const bundlePath = path.join(here, ".monitoring-timeline-semantics-bundle.cjs");
buildSync({
  entryPoints: [path.join(here, "medicalMonitoringTimelineSemanticsRender.test.jsx")],
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

const { semantics, empty } = renders;

// --- A21/A22：窗外事件——继续符号 + 方向读屏文案 + 原始日期保留 ---
check(semantics.includes('data-finding-beyond="before"'), "beyond-before event exposes its direction channel");
check(semantics.includes("开始于时间窗之前"), "beyond event copy states the direction in user language");
check(semantics.includes("2026-01-05"), "beyond event keeps its raw date visible (no same-day disguise)");
check(semantics.includes("monitoring-track-event-beyond"), "beyond event carries the continue-symbol style hook");
passed += 4;

// --- A22：ongoing/end_unknown开放条形——与point明确区分 ---
check(semantics.includes('data-timeline-geometry="ongoing"'), "ongoing geometry is exposed");
check(semantics.includes("monitoring-track-event-open-end"), "ongoing/end_unknown bars carry the open-end visual");
check(semantics.includes("monitoring-track-event-span"), "open-ended marks render as spans, not points");
check(semantics.includes("持续用药中"), "ongoing event label renders");
passed += 4;

// --- 精度表达：月精度仅进待确认区并标注精度，不以01日为实际日（J03） ---
check(semantics.includes('data-date-precision="month"'), "month-precision pending row exposes its precision");
check(semantics.includes("月精度：2026-07"), "month-precision note shows the raw YYYY-MM value");
check(semantics.includes("不以01日为实际日"), "month-precision note states the no-fabricated-day rule");
check(!semantics.includes("2026-07-01（"), "month-precision start is not presented as a fabricated day-01 exact date");
passed += 4;

// --- A23：全无有效日期→明确空态（无月份刻度/无假窗文案） ---
check(empty.includes("无有效日期"), "undated timeline states 无有效日期 explicitly");
check(empty.includes("data-monitoring-timeline-empty"), "undated timeline renders the explicit empty-state marker");
check(empty.includes("月份刻度与时间窗已隐藏"), "undated timeline explains that ticks and the fake window are hidden");
check(!empty.includes("1月") && !empty.includes("2月") && !empty.includes("3月"), "undated timeline renders no month ticks");
check(!empty.includes("2026-01-01 — "), "undated timeline renders no fabricated window range");
passed += 5;

console.log(`medicalMonitoringTimelineSemanticsRender: ${passed} passed`);
