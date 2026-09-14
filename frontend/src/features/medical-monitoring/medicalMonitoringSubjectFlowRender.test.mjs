import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import { createRequire } from "node:module";
import { fileURLToPath } from "node:url";
import { buildSync } from "esbuild";

let passed = 0;
function check(condition, message) {
  assert.ok(condition, message);
  passed += 1;
}

function countOccurrences(html, marker) {
  return html.split(marker).length - 1;
}

const here = path.dirname(fileURLToPath(import.meta.url));

// 与 R7 进度面板渲染测试相同的离线策略：用已安装的 esbuild 打包 JSX 渲染夹具，
// 以静态标记断言受试者阶段流向看板，不新增 DOM 渲染依赖，不启动服务或浏览器。
const bundlePath = path.join(here, ".monitoring-subject-flow-render-bundle.cjs");
buildSync({
  entryPoints: [path.join(here, "medicalMonitoringSubjectFlowRender.test.jsx")],
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
let selectors;
try {
  const require = createRequire(import.meta.url);
  ({ renders, selectors } = require(bundlePath));
} finally {
  fs.rmSync(bundlePath, { force: true });
}

// ---- 合同 §7 守恒门禁：12 人示例，图、表与风险集合一致 ----
const flow = selectors.flow;
check(flow.subjects.length === 12, "subject flow fixture carries 12 subjects");
check(flow.stages.every((stage) => stage.column_order >= 0 && stage.column_order <= 5), "synthetic stage catalog stays within 6 columns");
const entryStages = flow.stages.filter((stage) => stage.is_entry);
check(entryStages.length === 1 && entryStages[0].reached_count === 12, "single entry stage reaches 12 subjects");
const currentTotal = flow.stages.reduce((sum, stage) => sum + stage.current_count, 0);
check(currentTotal === 12, "current stays sum to 12 across nodes");
for (const stage of flow.stages) {
  const outbound = flow.links.filter((link) => link.from_stage_ref === stage.stage_ref).reduce((sum, link) => sum + link.count, 0);
  check(stage.reached_count === stage.current_count + outbound, `node ${stage.stage_ref} keeps reached = current + outbound`);
  const currentRisk = flow.subjects.filter((subject) => subject.current_stage_ref === stage.stage_ref && subject.mid_high_risk).length;
  check(stage.mid_high_risk_count === currentRisk, `node ${stage.stage_ref} risk count equals the mid-high intersection`);
}
for (const link of flow.links) {
  const traversing = flow.subjects.filter((subject) => {
    const path = subject.path_stage_refs;
    return path.some((ref, index) => ref === link.from_stage_ref && path[index + 1] === link.to_stage_ref);
  });
  check(traversing.length === link.count, `link ${link.link_ref} count equals subjects traversing the adjacent pair`);
  check(link.mid_high_risk_count === traversing.filter((subject) => subject.mid_high_risk).length, `link ${link.link_ref} risk count equals its mid-high intersection`);
}
check(flow.reconciliation.state === "matched" && flow.reconciliation.entry_total === 12, "reconciliation binds entry total to 12");

// ---- 正常渲染：ECharts 桑基容器、节点/连线 a11y、风险摘要、范围条、默认折叠 ----
const ready = renders.ready;
check(ready.includes('data-monitoring-flow-state="ready"'), "ready state is exposed for styling");
check(ready.includes("连线表示截至本次截止点的规范阶段路径"), "fixed path explanation copy rendered");
check(ready.includes('class="kz-chart mm-kz-chart"'), "flow chart mounts through the kz ECharts container");
check(ready.includes('aria-label="受试者阶段流向图（知情同意到研究状态）"'), "chart container exposes a Chinese aria label");
check(countOccurrences(ready, 'data-flow-node="') === 7, "renders every catalog stage as an accessible node");
check(countOccurrences(ready, 'data-flow-link="') === 6, "renders every canonical link as an accessible control");
check(ready.includes("筛选失败：到达 2 人，当前 2 人，中高风险 1 人"), "node a11y text follows the contract wording");
check(ready.includes("从治疗到完成研究：3 人，中高风险 0 人"), "link a11y text states the exact risk wording");
check(ready.includes("中高风险变化摘要") && ready.includes("新增 2 · 升级 1 · 持续 1"), "scope-level risk change summary rendered");
check(ready.includes("范围受试者 12 人"), "scope bar shows the global total");
check(!ready.includes("路径完整"), "check-state path-complete chip is not shown as monitor chrome");
check(!ready.includes("阶段人数已核对一致"), "reconciliation matched chip is not shown as monitor chrome");
check(ready.includes("当前项目/中心整体范围"), "scope bar states the project/site scope");
check(ready.includes('aria-expanded="false"') && ready.includes("展开明细"), "detail table collapses to one summary row by default");
check(!ready.includes("进入医学旅程"), "collapsed table hides subject rows and jump actions");
check(!/sankey/i.test(ready.replace(/path_throughput_sankey|受试者阶段流向/g, "")), "user-facing markup avoids chart-libary jargon");

// ---- 三类筛选与表格、风险集合精确对账 ----
const treatment = renders.currentTreatment;
check(treatment.includes("共 12 人 · 当前筛选 5 人"), "current selection states the filtered count");
check(countOccurrences(treatment, "data-flow-subject-ref=") === 5, "current treatment table shows exactly 5 rows");
check(treatment.includes("受试者 006") && treatment.includes("中风险 · 检验趋势需结合访视核对"), "current table carries the per-subject risk summary");
check(treatment.includes("入组/随机"), "previous stage column shows the canonical prior step");
check(treatment.includes("阶段前进") === false && treatment.includes("首次纳入"), "stage-change column uses Chinese labels");

const reached = renders.reachedScreening;
check(countOccurrences(reached, "data-flow-subject-ref=") === 12, "reached screening selection keeps all 12 subjects");
check(reached.includes("已筛选：筛选 · 累计到达"), "selection summary names the stage and metric");

const link = renders.linkCompleted;
check(countOccurrences(link, "data-flow-subject-ref=") === 3, "link selection table shows exactly the traversing subjects");
check(link.includes("已筛选：治疗 → 完成研究"), "link selection summary names both stages");
check(countOccurrences(link, ">进入医学旅程</button>") === 2, "rows with a usable jump window offer the journey action");
check(link.includes(">时间窗待确认</button>"), "row without usable dates keeps a disabled jump labeled 时间窗待确认");
check(link.includes("disabled"), "missing-date jump is disabled rather than sending an empty window");

const bandWithStage = renders.riskBandWithStage;
check(countOccurrences(bandWithStage, "data-flow-subject-ref=") === 2, "risk band intersects with the current-stage selection");
const bandAlone = renders.riskBandAlone;
check(countOccurrences(bandAlone, "data-flow-subject-ref=") === 4, "restored risk band filters mid-high subjects on its own");
check(bandAlone.includes('aria-pressed="true"'), "risk band chip reflects the pressed state");

// 纯选择器：筛选行集合与选择集合一致
check(selectors.selectRows(selectors.ready, selectors.selection).length === 2, "selector intersects current stage with the risk band");
check(selectors.selectRows(selectors.ready, selectors.linkSelection).length === 2, "selector resolves link selection to its subject set");
check(selectors.selection.stageRef === "flow-stage-treatment" && selectors.selection.metric === "current", "route keys map to the mutual-exclusive selection");
check(selectors.normalizedReady.stages.length === flow.stages.length, "adapter-normalized camelCase stages remain visible to the page model");
check(selectors.normalizedReady.links.length === flow.links.length, "adapter-normalized camelCase links remain visible to the page model");
check(selectors.normalizedReady.rows.every((row) => row.pathRefs.length > 0), "adapter-normalized subject paths remain available for reached and link filtering");

// ---- 三种非正常展示互不混淆 ----
const notProvided = renders.notProvided;
check(notProvided.includes("本次数据未提供研究状态"), "not-provided state copy");
check(notProvided.includes("本次运行未提供阶段路径数据。"), "not-provided carries the Chinese reason");
check(!notProvided.includes("0 人"), "not-provided DOM never shows 0 人");
check(!notProvided.includes("data-flow-node") && !notProvided.includes("<table"), "not-provided renders no nodes and no table");

const legacy = renders.legacyAbsent;
check(legacy.includes("本次数据未提供研究状态"), "legacy packet without flow fields shows the not-provided state");
check(!legacy.includes("0 人") && !legacy.includes("data-flow-node"), "legacy not-provided shows no fabricated chart");

const blocked = renders.blocked;
check(blocked.includes("阶段人数暂无法核对，请检查本次数据范围"), "blocked state copy");
check(blocked.includes("筛选阶段到达人数与路径记录相差 2 条，无法核对。"), "blocked state shows the Chinese gap");
check(!blocked.includes("data-flow-node"), "blocked state renders no contradictory chart");

const empty = renders.empty;
check(empty.includes("当前项目/中心在本次截止点暂无受试者"), "empty range copy");
check(!empty.includes("data-flow-node"), "empty range renders no zero-valued chart");
check(!empty.includes("0 人"), "empty range DOM never shows 0 人");

// ---- 键盘隔离与中文 CSS 合同 ----
const pageSource = fs.readFileSync(path.join(here, "MedicalMonitoringWorkspace.jsx"), "utf8");
const chartSource = fs.readFileSync(path.join(here, "medicalMonitoringKzChart.jsx"), "utf8");
check(chartSource.includes("本截止点无人到达"), "zero-count catalog stage is visibly explained in the sankey node label");
check(pageSource.includes('data-monitoring-flow-scope="true"'), "flow section marks its interactive scope");
check(pageSource.includes('event.target instanceof SVGElement') && pageSource.includes('event.target.closest("[data-monitoring-flow-scope]")'), "document-level shortcuts skip the flow scope");
check(pageSource.includes('event.key === "Escape"'), "escape clears the flow selection");
check(pageSource.includes("ArrowRight") && pageSource.includes("ArrowLeft"), "arrow keys move focus across nodes and links");
check(pageSource.includes('event.target instanceof Element && event.target.closest("[data-monitoring-flow-scope]")'), "risk-list shortcuts stay isolated from flow controls");
check(pageSource.includes("const sameColumn = from.x === to.x") && pageSource.includes('value.endsWith("数据未提供")'), "same-column branches and long Chinese labels use dedicated readable geometry");

const css = fs.readFileSync(path.join(here, "medicalMonitoringWorkspace.css"), "utf8");
const flowCss = css.slice(css.indexOf("受试者阶段流向：全宽横向流向图"));
check(flowCss.includes(".monitoring-flow-svg"), "styles define the flow svg canvas");
check(flowCss.includes("g[data-flow-node]:focus-visible") && flowCss.includes("g[data-flow-link]:focus-visible"), "nodes and links keep a visible focus style");
check(flowCss.includes(".monitoring-flow-node-counts") && flowCss.includes("font-variant-numeric: tabular-nums"), "counts use tabular numerals");
check(flowCss.includes(".monitoring-flow-table-wrap") && flowCss.includes("overflow-x: auto"), "detail table scrolls internally instead of the page");
check(css.includes(".monitoring-flow-table-hrail") && css.includes(".monitoring-timeline-vrail"), "painted scroll rails remain visible when OS overlay scrollbars hide");
check(css.includes(".monitoring-flow-table-scroll.is-overflow .monitoring-flow-table-wrap") && css.includes("scrollbar-width: none"), "overflow table hides native bar when custom hrail paints");
check(css.includes(".monitoring-timeline-scroll-shell.is-overflow-y .monitoring-timeline-scroll") && /is-overflow-y[\s\S]{0,180}scrollbar-width:\s*none/.test(css), "overflow timeline hides native bar when custom vrail paints");
check(pageSource.includes("左右滑动查看完整明细"), "table overflow cue uses Chinese-native monitor wording");
check(pageSource.includes("FlowTableScroll") || pageSource.includes("data-monitoring-table-hrail"), "homologous table paints a linked horizontal scroll affordance");
check(pageSource.includes('aria-label="左右滑动查看完整明细"'), "table hrail exposes a Chinese accessible label");
check(pageSource.includes('aria-label="上下滑动查看完整时间轴泳道"'), "journey vrail exposes a Chinese accessible label");
check(pageSource.includes("--monitoring-edge-clip"), "table sync clips mid-glyph header at overflow edge");
check(pageSource.includes("scrollToRatio"), "custom rails are linked to the real overflow scroller");
check(flowCss.includes(".monitoring-flow-notice.is-blocked"), "blocked notice has a distinct visual treatment");
check(flowCss.includes('data-monitoring-state="waiting_start"') && flowCss.includes("max-height: 118px"), "wide overview keeps the idle progress and flow canvas compact");
check(!/linear-gradient|backdrop-filter/.test(flowCss), "flow styles stay flat and restrained");

console.log(`medicalMonitoringSubjectFlowRender: ${passed} checks passed`);
