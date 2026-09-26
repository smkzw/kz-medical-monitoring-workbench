// E1工作列表负载回归（node直接运行，stub数据，0模型调用）：
// 用合成正式Finding冻结DTO构造1200条工作列表，走真实
// buildFindingCards（过滤+规范化）与真实QueryWorkspaceView渲染，
// 断言：过滤只剔坏行、顺序（排序）稳定不重排、渲染锚点完整、
// 规范化/渲染耗时在显式预算内（不劣化的回归天花板）。
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
const bundlePath = path.join(here, ".monitoring-finding-worklist-load-bundle.cjs");
buildSync({
  entryPoints: [path.join(here, "medicalMonitoringFindingWorklistLoad.test.jsx")],
  bundle: true,
  outfile: bundlePath,
  format: "cjs",
  platform: "node",
  jsx: "automatic",
  loader: { ".css": "empty" },
  define: { "process.env.NODE_ENV": '"test"' },
  logLevel: "silent",
});
let renderWorklist;
try {
  const require = createRequire(import.meta.url);
  ({ renderWorklist } = require(bundlePath));
} finally {
  fs.rmSync(bundlePath, { force: true });
}

// --- 合成正式Finding DTO工作列表：1200条 + 5条坏行 ---
const TOTAL = 1200;
const STATES = ["open", "confirmed", "closed"];
function syntheticFinding(index) {
  const state = STATES[index % STATES.length];
  return {
    finding_id: `finding-load-${String(index + 1).padStart(4, "0")}`,
    risk_id: `risk-load-${(index % 40) + 1}`,
    subject_ref: `subj-load-${(index % 240) + 1}`,
    site_ref: `site-load-${(index % 6) + 1}`,
    scope_kind: "subject",
    event_ref: `event-load-${(index % 300) + 1}`,
    window_start: "2026-01-01",
    window_end: "2026-03-31",
    finding_state: state,
    claims: [
      { kind: "basis", text: `依据：方案条款#${(index % 12) + 1}。`, evidence_ids: [`ev-${index}-a`] },
      { kind: "finding", text: `发现：受试者记录${index + 1}存在未闭环异常。`, evidence_ids: [`ev-${index}-b`] },
      { kind: "action", text: "行动项：请核对原始记录并补录。" },
    ],
    source_refs: [
      { evidence_id: `ev-${index}-a`, path: "AE.AETERM", record_id: `rec-${index}-a`, field: "AETERM" },
      { evidence_id: `ev-${index}-b`, path: "LB.LBORRES", record_id: `rec-${index}-b`, field: "LBORRES" },
    ],
    locator: { path: "AE.AETERM", record_id: `rec-${index}-a`, field: "AETERM" },
    data_cutoff: "2026-03-31",
    source_revision_id: "rev-load-1",
  };
}
const raw = {
  query_findings: [
    ...Array.from({ length: TOTAL }, (_, index) => syntheticFinding(index)),
    // 5条坏行：无finding_id且无title——真实过滤谓词应剔除且仅剔除这些
    { note: "no identity" },
    "not-a-record-but-string",
    42,
    null,
    { finding_id: "", title: "" },
  ],
};

const { markup, findingCards, normalizedMs, renderMs } = renderWorklist(raw);

// --- 筛选：只剔坏行，1200条全部保留 ---
check(findingCards.length === TOTAL, `filter keeps all ${TOTAL} valid findings and drops only bad rows (got ${findingCards.length})`);

// --- 排序（顺序稳定性）：规范化不重排，与输入顺序逐条对齐 ---
check(findingCards[0].findingId === "finding-load-0001", "first card keeps server order (stable sort)");
check(findingCards[TOTAL - 1].findingId === `finding-load-${String(TOTAL).padStart(4, "0")}`, "last card keeps server order (stable sort)");
let orderStable = true;
for (let index = 0; index < TOTAL; index += 1) {
  if (findingCards[index].findingId !== syntheticFinding(index).finding_id) { orderStable = false; break; }
}
check(orderStable, "normalization preserves work-list order end to end");

// --- 渲染：真实QueryWorkspaceView完整渲染，锚点与计数完整 ---
check(markup.includes(`发现（${TOTAL} 条`), "work-list header reports the full count");
const anchors = markup.split('data-query-finding=').length - 1;
check(anchors === TOTAL, `every finding renders its stable anchor (got ${anchors})`);
check(markup.includes('data-query-finding="finding-load-0001"'), "first anchor renders");
check(markup.includes(`data-query-finding="finding-load-${String(TOTAL).padStart(4, "0")}"`), "last anchor renders");
check(markup.includes('data-monitoring-finding-cards'), "work list section renders");

// --- 不劣化预算（回归天花板；本机实测远低于预算）---
check(normalizedMs < 2_000, `normalization of ${TOTAL} findings within 2s budget (took ${normalizedMs.toFixed(0)}ms)`);
check(renderMs < 15_000, `static render of ${TOTAL} cards within 15s budget (took ${renderMs.toFixed(0)}ms)`);

console.log(`[worklist-load] findings=${TOTAL} normalizedMs=${normalizedMs.toFixed(0)} renderMs=${renderMs.toFixed(0)} checks=${passed}`);
process.exitCode = 0;
