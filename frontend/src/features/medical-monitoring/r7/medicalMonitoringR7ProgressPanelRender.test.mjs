import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import { createRequire } from "node:module";
import { fileURLToPath } from "node:url";
import { buildSync } from "esbuild";
import { findR7ForbiddenTerms } from "./medicalMonitoringR7ProgressProjection.mjs";

let passed = 0;
function check(condition, message) {
  assert.ok(condition, message);
  passed += 1;
}

const here = path.dirname(fileURLToPath(import.meta.url));

// Bundle the JSX render fixture with the already-installed esbuild so the
// panel markup can be asserted without adding a DOM renderer dependency.
// CJS output keeps node builtins requireable; the transient bundle is
// removed right after loading.
const bundlePath = path.join(here, ".r7-progress-panel-render-bundle.cjs");
buildSync({
  entryPoints: [path.join(here, "medicalMonitoringR7ProgressPanelRender.test.jsx")],
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

function stripTags(html) {
  return html.replace(/<[^>]*>/g, " ").replace(/\s+/g, " ").trim();
}

// waiting_start: title, scope line, start action, zeroed progress bar.
check(renders.waiting.includes("本次监查进度"), "title rendered");
check(renders.waiting.includes("日常监查 · 增量 · 2026-08-28 · 第 2 版监查范围"), "scope line rendered");
check(renders.waiting.includes(">开始</button>"), "start action rendered");
check(renders.waiting.includes("is-primary"), "start action uses the primary orange hierarchy");
check(!renders.waiting.includes("确认停止"), "no confirm without user intent");
check(renders.waiting.includes('aria-valuenow="0"'), "progressbar starts at 0");
check(renders.waiting.includes("暂无最新进展"), "empty latest updates copy");

// running: server progress text, stages, current work cap, updates cap.
check(renders.running.includes("已处理 3/8 项（37.5%）"), "server progress text rendered");
check(renders.running.includes(">停止</button>"), "stop action rendered");
check(renders.running.includes("is-stop"), "stop action remains secondary rather than risk red");
check(renders.running.includes('role="progressbar"'), "progressbar role present");
check(
  renders.running.includes('aria-valuemin="0"')
    && renders.running.includes('aria-valuemax="100"')
    && renders.running.includes('aria-valuenow="38"')
    && renders.running.includes('aria-valuetext="已处理 3/8 项（37.5%）"'),
  "progressbar aria attributes",
);
check(renders.running.includes("数据核查") && renders.running.includes("已处理 2/3 项"), "stage rows rendered");
check(renders.running.includes("另有 1 项"), "current work overflow copy");
check(!renders.running.includes("核对访视日期"), "current work capped at 3");
check(renders.running.includes("10:31") && renders.running.includes("审阅合并用药"), "latest updates rendered");
check(!renders.running.includes("10:26"), "latest updates capped at 5");
check(
  renders.running.includes('<p class="r7-progress-status" aria-live="polite">医学监查进行中</p>'),
  "only the status text enters the polite live region",
);
check(renders.running.includes('data-r7-state="running"'), "run state exposed for styling");

// Inline stop confirmation replaces the action set.
check(renders.confirming.includes(">确认停止</button>"), "confirm stop button rendered");
check(renders.confirming.includes("is-confirm"), "confirm stop uses a distinct non-risk treatment");
check(
  renders.confirming.includes("停止后不再开始下一项；当前正在分析的内容可能完成"),
  "confirm hint rendered",
);
check(!renders.confirming.includes(">停止</button>"), "plain stop hidden while confirming");

// In-flight action disables repeat submission.
check(renders.pendingAction.includes(">开始</button>") === false || renders.pendingAction.includes("disabled"), "pending action disables button");
check(renders.pendingAction.includes('disabled=""'), "start button disabled while pending");

// 403: actions hidden, forbidden alert, facts kept.
check(!renders.forbidden.includes(">停止</button>"), "forbidden hides actions");
check(renders.forbidden.includes('role="alert"'), "forbidden uses alert role");
check(renders.forbidden.includes("当前账号不能操作本次监查运行"), "forbidden copy");
check(renders.forbidden.includes("已处理 3/8 项（37.5%）"), "forbidden keeps facts");

// Refresh failure: alert, last-read time, manual refresh action, facts kept.
check(renders.refreshFailed.includes('role="alert"'), "refresh failure uses alert role");
check(renders.refreshFailed.includes("进度刷新失败，最后读取于 14:05"), "refresh failure copy with time");
check(renders.refreshFailed.includes(">重新读取进度</button>"), "manual refresh action rendered");
check(renders.refreshFailed.includes("已处理 3/8 项（37.5%）"), "refresh failure keeps facts");

// Neutral empty state: no request-derived chrome, no progress bar.
check(renders.emptyNoRun.includes("尚无本次监查"), "no-run empty copy");
check(!renders.emptyNoRun.includes("progressbar"), "empty state renders no progress bar");
check(!renders.emptyNoRun.includes('role="alert"'), "empty state is not an alert");

// Loading state: no stale numbers.
check(renders.loading.includes("正在读取本次监查进度"), "loading copy");
check(!renders.loading.includes("progressbar"), "loading renders no progress bar");

// failed: facts kept, server status copy, failure styling hook.
check(renders.failed.includes('data-r7-state="failed"'), "failed state hook for red styling");
check(renders.failed.includes("分析服务连接异常，本项分析未完成"), "failed server copy");
check(renders.failed.includes("已处理 3/8 项（37.5%）"), "failed keeps completed facts");
check(renders.failed.includes("本项未完成"), "failed adds a prominent non-completion badge");

// Forbidden terms must not appear in any rendered state.
for (const [name, html] of Object.entries(renders)) {
  const hits = findR7ForbiddenTerms([stripTags(html)]);
  check(hits.length === 0, `render ${name} excludes forbidden terms${hits.length ? `: ${JSON.stringify(hits)}` : ""}`);
}

// Style contract: single orange accent, red only on failure, reduced motion,
// visible focus, tabular numerals, internal wrapping instead of page overflow.
const css = fs.readFileSync(path.join(here, "medicalMonitoringR7ProgressPanel.css"), "utf8");
check(css.includes("prefers-reduced-motion"), "reduced motion supported");
check(css.includes(":focus-visible"), "visible focus styles");
check(css.includes("font-variant-numeric: tabular-nums"), "tabular numerals");
check(css.includes('data-r7-state="failed"'), "red reserved for failure state");
check(css.includes("r7-progress-outcome"), "terminal outcome badge is visually explicit");
check(
  css.includes('.r7-progress[data-r7-state="failed"] .r7-progress-outcome')
    && css.includes("background: var(--r5-red, #b83b3b)")
    && css.includes("color: #fff"),
  "failed outcome uses a solid risk-red badge rather than an outline chip",
);
check(
  css.includes('.r7-progress[data-r7-state="failed"] .r7-progress-big')
    && css.includes("font-size: 20px")
    && css.includes("font-weight: 700"),
  "failed numeric progress is visually de-emphasized below the outcome",
);
check(!css.includes("is-danger"), "ordinary stop controls do not use risk-red styling");
check(css.includes("flex-wrap: wrap"), "internal wrapping for narrow widths");
check(!/linear-gradient|backdrop-filter|blur\(/.test(css), "no gradients or glass effects");

console.log(`medicalMonitoringR7ProgressPanelRender: ${passed} passed`);
