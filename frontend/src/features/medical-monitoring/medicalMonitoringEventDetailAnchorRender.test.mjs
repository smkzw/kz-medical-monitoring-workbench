// R29-06 render contract: 带风险锚点进入「事件明细」不得崩溃（R29-06根因
// = riskSeverityLabel悬空引用ReferenceError），且对照组（无锚点timeline/
// 带锚点journey）保持正常；选中事件行出现并携带诚实等级徽章。No DOM,
// no browser, no server.

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
const bundlePath = path.join(here, ".monitoring-event-detail-anchor-bundle.cjs");
buildSync({
  entryPoints: [path.join(here, "medicalMonitoringEventDetailAnchorRender.test.jsx")],
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

const { timelineWithoutAnchor, timelineWithAnchor, journeyWithAnchor, timelineWithPendingRisk } = renders;

// --- 对照组保持正常（R29报告对照组） ---
check(timelineWithoutAnchor.ok, `无锚点 view=timeline 正常渲染（实际：${timelineWithoutAnchor.error || "ok"}）`);
check(journeyWithAnchor.ok, `带锚点 view=journey 正常渲染（实际：${journeyWithAnchor.error || "ok"}）`);

// --- R29-06主路径：带锚点 view=timeline 不再落入错误边界 ---
check(timelineWithAnchor.ok, `带锚点 view=timeline 不抛错（实际：${timelineWithAnchor.error || "ok"}）`);
check(
  timelineWithAnchor.html.includes("monitoring-event-lane"),
  "带锚点进入事件明细渲染「选中事件明细」行",
);
check(timelineWithAnchor.html.includes("V2 访视"), "选中事件行展示事件名");
check(timelineWithAnchor.html.includes("高风险"), "选中事件行携带诚实等级徽章（高风险）");
check(
  timelineWithAnchor.html.includes("monitoring-domain-track") || timelineWithAnchor.html.includes("monitoring-domain-tracks"),
  "事件明细页同时保留八域泳道时间轴",
);

// --- 同类隐患：待确认区pending事件带risk也不崩（原1051行悬空引用） ---
check(timelineWithPendingRisk.ok, `待确认区pending事件带risk不抛错（实际：${timelineWithPendingRisk.error || "ok"}）`);
check(timelineWithPendingRisk.html.includes("高风险"), "pending事件risk徽章按riskSeverityInfo诚实呈现");

console.log(`medicalMonitoringEventDetailAnchorRender: ${passed} passed`);
