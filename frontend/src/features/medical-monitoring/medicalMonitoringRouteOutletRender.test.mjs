// R30-03 render contract: 来源清单在途/失败期间，监查模块落地页不得
// 渲染「功能未配置」或激活引导（恢复期中间态曾诱导对已配置项目重复
// 激活）；只有清单读到且确无绑定时才落未配置。No DOM, no browser, no
// server.

import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import { createRequire } from "node:module";
import { fileURLToPath } from "node:url";
import { buildSync } from "esbuild";

const here = path.dirname(fileURLToPath(import.meta.url));
const bundlePath = path.join(here, ".monitoring-route-outlet-bundle.cjs");
buildSync({
  entryPoints: [path.join(here, "medicalMonitoringRouteOutletRender.test.jsx")],
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

// 在途：读取中，不得出现「功能未配置」。
assert.ok(renders.pending.includes("正在读取项目与模块配置"), "pending manifest should show loading");
assert.ok(!renders.pending.includes("功能未配置"), "pending manifest must not show unconfigured");

// 列表仍在读取：同样读取中。
assert.ok(renders.listPending.includes("正在读取项目与模块配置"), "pending project list should show loading");
assert.ok(!renders.listPending.includes("功能未配置"), "pending project list must not show unconfigured");

// 读取失败：诚实报错+重试入口；不渲染未配置、不提供激活按钮。
assert.ok(renders.error.includes("项目模块配置读取失败"), "failed manifest read should explain itself");
assert.ok(renders.error.includes("重试读取配置"), "failed manifest read should offer retry");
assert.ok(!renders.error.includes("功能未配置"), "failed manifest read must not show unconfigured");
assert.ok(!renders.error.includes("启用该模块"), "failed manifest read must not offer activation");

// 清单读到且无监查绑定：才渲染未配置（真未配置口径不变）。
assert.ok(renders.unconfigured.includes("功能未配置"), "ready manifest without binding should show unconfigured");

// 已解析出监查路由：渲染工作区出口，不走未配置。
assert.ok(!renders.routed.includes("功能未配置"), "routed workspace must not show unconfigured");

console.log("medicalMonitoringRouteOutletRender: recovery intermediate states passed");
