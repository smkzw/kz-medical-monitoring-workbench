import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import { createRequire } from "node:module";
import { fileURLToPath } from "node:url";
import { buildSync } from "esbuild";

const here = path.dirname(fileURLToPath(import.meta.url));
const bundlePath = path.join(here, ".g6-page-render-bundle.cjs");
buildSync({
  entryPoints: [path.join(here, "MedicalMonitoringG6SyntheticPageRender.test.jsx")],
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

let passed = 0;
function check(value, message) {
  assert.equal(Boolean(value), true, message);
  passed += 1;
}
function countOf(html, needle) {
  return (html.match(new RegExp(needle.replace(/[.*+?^${}()|[\]\\]/g, "\\$&"), "g")) || []).length;
}

check(renders.overview.includes('data-g6-synthetic-page="true"'), "overview exposes the G6 page root");
check(renders.overview.includes('data-g6-load-state="ready"'), "overview renders only after canonical bundle load");
check(renders.loading.includes('data-g6-load-state="loading"'), "page stays in loading state before canonical endpoint data arrives");
check(!renders.loading.includes("合成项目甲"), "page does not render a static project fallback before endpoint data arrives");
check(renders.overview.includes("合成医学监查工作台"), "overview uses Chinese-native audience title");
check(renders.overview.includes("开始本轮分析"), "overview exposes the single primary analysis action");
check(renders.overview.includes("合成项目甲") && renders.overview.includes("合成项目乙"), "overview renders both canonical projects");
check(renders.overview.includes("项目中心流向"), "overview exposes the project-center flow section");
check(renders.overview.includes('data-g6-flow-chart="true"'), "overview exposes the structured flow chart hook");
check(renders.overview.includes('data-g6-flow-table="true"'), "overview exposes the same-source flow table hook");
check(countOf(renders.overview, 'data-flow-node=') === 5, "overview renders all canonical flow nodes");
check(countOf(renders.overview, 'data-flow-link=') >= 5 && renders.overview.includes('data-flow-link-count="0"'), "overview renders clickable positive and zero-value flow links");
check(renders.overview.includes("知情同意 → 筛选 → 治疗 → 研究状态"), "overview keeps the required flow reading order");
check(renders.overview.includes("合成中心一") && renders.overview.includes("合成中心三"), "overview shows canonical center differences");
check(!renders.overview.includes("binding_digest") && !renders.overview.includes("synthetic-recorded-provider"), "overview does not expose binding or provider internals");

check(renders.journey.includes('data-g6-journey="true"'), "journey view exposes its structured root");
check(renders.journey.includes('data-g6-journey-axis="true"'), "journey view exposes a horizontal axis hook");
check(renders.journey.includes('data-g6-journey-scroll="true"'), "journey view exposes an explicit scroll container");
check(renders.journey.includes("不良事件") && renders.journey.includes("既往情况") && renders.journey.includes("合并用药记录"), "journey retains canonical clinical lanes");
check(renders.journey.includes("给药记录") && renders.journey.includes("检验检查") && renders.journey.includes("PD观察") && renders.journey.includes("疗效观察") && renders.journey.includes("访视事件"), "journey retains all eight canonical event domains");
check(countOf(renders.journey, 'class="g6-event-marker') === 8, "journey renders all eight subject events");
check(["diamond", "bookmark", "capsule", "hexagon", "square", "triangle", "circle", "ring"].every((shape) => renders.journey.includes(`g6-event-marker ${shape}`)), "journey preserves a distinct marker shape per domain");
check(renders.journey.includes("点击访视轴上的事件"), "journey provides an actionable event detail hint");
check(!renders.journey.includes("provider") && !renders.journey.includes("model"), "journey does not expose execution routing terms");

console.log(`G6 canonical synthetic page render: ${passed} checks passed`);
