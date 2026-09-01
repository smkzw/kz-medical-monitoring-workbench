// R7 Slice-08C-3 render contract (contract §7.2/§7.3): bundles the fixture
// with esbuild (single React copy) and asserts static markup for the shared
// horizontal axis with R7-only change markers, the legacy-R5 untouched axis,
// the overlay/push drawer (role/aria-modal/aria-labelledby, stable ids, fixed
// section order, fallback texts, multi-change switcher, live region) and the
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

function countOf(html, needle) {
  return (html.match(new RegExp(needle.replace(/[.*+?^${}()|[\]\\]/g, "\\$&"), "g")) || []).length;
}

function positionOf(html, needle) {
  const index = html.indexOf(needle);
  return index < 0 ? -1 : index;
}

const here = path.dirname(fileURLToPath(import.meta.url));
const bundlePath = path.join(here, ".monitoring-journey-drawer-render-bundle.cjs");
buildSync({
  entryPoints: [path.join(here, "medicalMonitoringJourneyDrawerRender.test.jsx")],
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
let expected;
try {
  const require = createRequire(import.meta.url);
  ({ renders, expected } = require(bundlePath));
} finally {
  fs.rmSync(bundlePath, { force: true });
}

const {
  axis,
  legacyAxis,
  riskRowWithMarker,
  overlayDrawer,
  pushDrawer,
  closedDrawer,
  fallbackDrawer,
  firstAnalysisDrawer,
  sevenMarkers,
} = renders;

// --- axis: one shared horizontal axis with the eight domain lanes (§7.2) ---
check(countOf(axis, 'data-timeline-mode="shared-horizontal"') === 1, "exactly one shared horizontal axis");
for (const domain of ["ae", "mh", "cm", "ip", "lab_exam", "hospital_procedure", "symptom_efficacy", "protocol_compliance"]) {
  check(axis.includes(`data-domain-track="${domain}"`), `eight-domain geometry keeps the ${domain} lane`);
}
check(axis.includes('id="monitoring-journey-axis-title"'), "shared axis title carries the stable focus-restore id");
check(axis.includes('tabindex="-1"'), "axis title is focusable as the drawer restore target");
check(axis.includes("筛选访视") && axis.includes("第 2 次访视"), "visit axis nodes render on the same axis");
for (const label of ["合并用药", "试验用药", "检验检查", "诊疗操作", "疗效/症状", "方案执行"]) {
  check(axis.includes(label), `axis uses the frozen Chinese-native domain label ${label}`);
}
passed += 11;

// --- axis: R7-only change markers (icon + word + tone) and count suffix (§4.3/§4.5) ---
check(countOf(axis, 'data-change-marker="true"') === 2, "exactly the two event-bound markers render on the axis");
check(axis.includes('data-change-kind="upgraded"'), "primary marker of the two-row event is 升级 (first ordinal)");
check(axis.includes('data-change-kind="continued"'), "single-row event marker is 持续");
check(axis.includes("，本轮变化：升级，共 2 条变化"), "accessible name states the change word and the total count");
check(axis.includes("，本轮变化：持续"), "single-change accessible name states the change word");
check(axis.includes("monitoring-journey-tone-danger") && axis.includes("monitoring-journey-tone-neutral"), "marker tone classes render for 升级/持续");
check(!axis.includes("既往史补录核查"), "risk-only unbound change never creates a virtual axis node");
passed += 6;

// --- axis: pending dates sink to the pending zone, never the axis (§4.2) ---
check(axis.includes('data-timeline-geometry="pending"'), "pending event keeps the pending geometry");
check(axis.includes("monitoring-pending-date"), "pending zone renders");
check(axis.includes("合并用药日期待确认"), "pending event appears in the pending zone");
check(axis.includes("未按实际日期吸附到共享时间轴，单独列示"), "pending copy stays explicit");
passed += 4;

// --- axis: truncation prompt under the shared axis title (§3.6) ---
check(axis.includes("monitoring-journey-truncation") && axis.includes('role="status"'), "truncation prompt renders with status role");
check(axis.includes("本轮变化较多，当前仅显示服务端已返回的前 3 条"), "truncation prompt uses the frozen wording");
check(positionOf(axis, "monitoring-journey-truncation") > positionOf(axis, "monitoring-axis-heading"), "truncation prompt sits under the axis heading");
passed += 3;

// --- legacy R5 axis: geometry unchanged, no markers/drawer hooks ---
check(countOf(legacyAxis, 'data-timeline-mode="shared-horizontal"') === 1, "legacy axis still renders the single shared axis");
check(countOf(legacyAxis, 'data-domain-track="') === 8, "legacy axis keeps the eight lanes");
check(!legacyAxis.includes("monitoring-journey-marker"), "legacy axis renders no R7-only markers");
check(!legacyAxis.includes("monitoring-journey-axis-title"), "legacy axis title carries no drawer restore id");
check(!legacyAxis.includes("monitoring-journey-truncation"), "legacy axis renders no truncation prompt");
check(legacyAxis.includes('data-timeline-geometry="pending"'), "legacy axis keeps the pending sink");
passed += 6;

// --- risk row marker (§3.5): right-side risk list carries bound changes ---
check(riskRowWithMarker.includes("monitoring-journey-marker"), "risk row renders the R7-only marker");
check(riskRowWithMarker.includes('data-change-kind="continued"'), "risk row marker kind is preserved");
check(riskRowWithMarker.includes("monitoring-journey-sr-only"), "risk row carries the visually hidden change wording");
check(riskRowWithMarker.includes("，本轮变化：持续"), "sr-only wording enters the accessible name");
check(riskRowWithMarker.includes("monitoring-risk-tail"), "risk row keeps the R7 change tail wrapper");
check(!/<span class="monitoring-change-label">/.test(riskRowWithMarker), "marker row does not duplicate the visible R5 change label");
passed += 6;

// --- overlay drawer (§5.3): dialog semantics, stable title id, close/backdrop ---
check(overlayDrawer.includes('data-journey-drawer-mode="overlay"'), "overlay mode hook present");
check(overlayDrawer.includes('role="dialog"') && overlayDrawer.includes('aria-modal="true"'), "overlay is a modal dialog");
check(overlayDrawer.includes('aria-labelledby="monitoring-journey-drawer-title"'), "overlay labels by the stable title id");
check(overlayDrawer.includes('id="monitoring-journey-drawer-title"'), "stable title id is on the h2");
check(overlayDrawer.includes('data-journey-backdrop="true"'), "overlay backdrop present for click-to-close");
check(overlayDrawer.includes('data-journey-close="true"') && overlayDrawer.includes('aria-label="关闭详情"'), "close button present with an accessible label");
check(overlayDrawer.includes("monitoring-journey-overlay"), "overlay wrapper present");
check(overlayDrawer.includes("monitoring-journey-drawer-body"), "drawer content area scrolls independently");
passed += 8;

// --- push drawer (§5.3): non-modal aside, same stable title id, no trap ---
check(pushDrawer.includes('data-journey-drawer-mode="push"'), "push mode hook present");
check(pushDrawer.includes("monitoring-journey-drawer-push"), "push aside class present");
check(!pushDrawer.includes("aria-modal") && !pushDrawer.includes('role="dialog"'), "push drawer is non-modal (no aria-modal, no dialog role)");
check(pushDrawer.includes('aria-labelledby="monitoring-journey-drawer-title"'), "push drawer shares the stable title id");
check(!pushDrawer.includes("monitoring-journey-overlay") && !pushDrawer.includes("monitoring-journey-backdrop"), "push drawer renders no backdrop");
passed += 5;

// --- fixed content order (§5.2): title first, then the eight sections ---
{
  const order = [
    ["title", "风险定位"],
    ["event_category", 'data-drawer-section="event_category"'],
    ["risk_level", 'data-drawer-section="risk_level"'],
    ["change", 'data-drawer-section="change"'],
    ["date", 'data-drawer-section="date"'],
    ["before_after", 'data-drawer-section="before_after"'],
    ["related_records", 'data-drawer-section="related_records"'],
    ["query_draft", 'data-drawer-section="query_draft"'],
    ["source", 'data-drawer-section="source"'],
  ];
  let cursor = -1;
  for (const [name, needle] of order) {
    const found = positionOf(overlayDrawer, needle);
    check(found > cursor, `${name} section follows the frozen order`);
    cursor = found;
  }
  for (const label of ["事件类别", "风险等级", "本轮变化", "日期", "前后依据", "关联记录", "Query 草稿"]) {
    check(overlayDrawer.includes(`<dt>${label}</dt>`), `section label ${label} rendered`);
  }
}
passed += 8;

// --- drawer content: event facts + current continuity row (§6) ---
check(overlayDrawer.includes(">发热伴感染</h2>"), "title is the current event label");
check(overlayDrawer.includes("<dd>AE</dd>"), "event category comes from the current event");
check(overlayDrawer.includes("<dd>中 → 高</dd>"), "risk level shows 前等级 → 后等级");
check(overlayDrawer.includes("<dd>升级</dd>"), "this-round change word rendered");
check(overlayDrawer.includes("<dd>2026-02-01 · 第 2 次访视</dd>"), "date keeps the event date and visit");
check(overlayDrawer.includes("上轮 中；本轮 高；变化原因：本轮体温记录修订，等级升高。"), "before/after basis separates prior level, current level and reason");
check(overlayDrawer.includes("<dd>关联原始记录 1 条</dd>"), "related records show the current event source count");
check(overlayDrawer.includes("请核实发热记录与检验结果的一致性。"), "Query draft comes from the selected risk evidenceSummary");
check(overlayDrawer.includes(">查看来源证据</button>") && !overlayDrawer.includes('data-journey-source="true" disabled=""'), "source entry enabled with the usable locator pair");
passed += 9;

// --- multi-change switcher (§4.5/§5.2): server order, compact controls ---
check(countOf(overlayDrawer, 'data-change-row="') === 2, "switcher shows all bound rows");
check(overlayDrawer.includes("1/2") && overlayDrawer.includes("2/2"), "switcher labels show position over total");
check(overlayDrawer.includes('data-change-row="0"' ) && overlayDrawer.includes('aria-pressed="true"'), "current row is the first by server order");
check(overlayDrawer.includes('aria-label="本轮变化切换"'), "switcher group has an accessible label");
passed += 4;

// --- closed risk level wording (§4.4) ---
check(closedDrawer.includes("<dd>高（已关闭）</dd>"), "closed risk shows 前等级（已关闭）");
check(closedDrawer.includes("<dd>关闭</dd>"), "closed risk shows the 关闭 change word");
passed += 2;

// --- fixed fallback texts (§5.2) ---
for (const text of [
  "类别待确认",
  "风险等级待确认",
  "本轮变化待确认",
  "日期待确认",
  "本轮未提供前后比较依据",
  "本轮未提供关联记录",
  "本轮未提供 Query 草稿",
  "原始记录位置待确认",
]) {
  check(fallbackDrawer.includes(text), `fallback drawer shows ${text}`);
}
check(fallbackDrawer.includes('data-journey-source="true" disabled=""'), "fallback source entry is disabled");
check(fallbackDrawer.includes(">本轮变化详情</h2>"), "fallback title is the neutral 本轮变化详情");
passed += 10;

// --- first-analysis basis (§6) ---
check(firstAnalysisDrawer.includes("本轮为首次全面分析，无比较基线"), "first analysis shows the frozen no-baseline text");
passed += 1;

// --- live region (§7.3): aria-live=polite announces the current title ---
check(overlayDrawer.includes('aria-live="polite"') && overlayDrawer.includes("data-journey-live"), "live region present with polite announcements");
check(overlayDrawer.includes("发热伴感染 · 中 → 高 · 升级"), "live region text carries title · risk level · change");
passed += 2;

// --- seven-kind marker integrity (§4.3): icon + word + tone for all kinds ---
for (const kind of expected.changeKinds) {
  check(sevenMarkers.includes(`data-change-kind="${kind}"`), `marker render covers ${kind}`);
  check(sevenMarkers.includes(`monitoring-journey-tone-`), `marker tone class present for ${kind}`);
  check(sevenMarkers.includes(`>${expected.changeKindTexts[kind]}</span>`), `marker Chinese word ${expected.changeKindTexts[kind]} rendered for ${kind}`);
}
check(countOf(sevenMarkers, "data-change-kind=") === 7, "exactly the seven frozen kinds render");
passed += 8;

// --- risk-only drawer sections (§3.5): title/category/level/date from risk + row ---
check(pushDrawer.includes(">既往史补录核查</h2>"), "risk-only drawer title is the risk type");
check(pushDrawer.includes("<dd>MH</dd>"), "risk-only drawer category comes from the risk domain");
check(pushDrawer.includes("<dd>中</dd>"), "risk-only drawer level shows the current 高/中/低 text");
check(pushDrawer.includes("<dd>新增</dd>"), "risk-only drawer change word rendered");
passed += 4;

// --- internal-leak scan: no tokens, schemas, hashes, refs, secrets ---
{
  const needles = [
    "result_context_token",
    "response_digest",
    "snapshot_token",
    "public_run_token",
    "sha256",
    "sk-proj-",
    "api_key=",
    "risk_instance_ref",
    "source_locator_ref",
    "risk_anchor_ref",
    "spine_ref",
    "spineRef",
    "spine_id",
    "window_start",
    "window_end",
    "risk-i-",
    "anchor-",
    "src-",
    "site/01",
    "S/01",
    "result-context:",
    "journey-row-",
    "s7-",
    "evidence_summary",
    "正式事实",
    "候选信号",
    "人工复核未完成",
  ];
  for (const needle of needles) {
    // riskRowWithMarker is the legacy R5 row surface and keeps its
    // pre-existing data-risk-instance-ref attribute; the new drawer and axis
    // surfaces are the ones that must stay free of internal references.
    for (const [name, html] of Object.entries(renders).filter(([key]) => key !== "riskRowWithMarker")) {
      check(!html.includes(needle), `render ${name} excludes ${JSON.stringify(needle)}`);
    }
  }
  passed += needles.length * (Object.keys(renders).length - 1);
}

// --- CSS contract: shared thresholds, tones, reduced-motion, no glass ---
{
  const css = fs.readFileSync(path.join(here, "medicalMonitoringJourneyDrawer.css"), "utf8");
  check(css.includes("max-width: 480px"), "overlay drawer caps at 480px");
  check(css.includes("width: 420px"), "push drawer is 420px");
  check(css.includes(".monitoring-subject-columns.is-monitoring-drawer-push") && css.includes("minmax(760px, 1fr) 420px"), "push mode keeps a 760px timeline column and a 420px inspector/drawer column");
  check(css.includes("prefers-reduced-motion: reduce") && css.includes("transition: none"), "reduced-motion makes open/close transitions instant");
  check(css.includes("--monitoring-journey-danger") && css.includes("--monitoring-journey-warning") && css.includes("--monitoring-journey-success") && css.includes("--monitoring-journey-info") && css.includes("--monitoring-journey-neutral"), "five semantic tones defined");
  check(css.includes(".monitoring-journey-live"), "live region style present");
  check(css.includes(".monitoring-journey-sr-only"), "sr-only style present");
  check(!/linear-gradient|backdrop-filter|blur\(/.test(css), "no gradients or glass effects");
}

// --- integration source contract: keyboard navigation + continuity row switch ---
{
  const pageSource = fs.readFileSync(path.join(here, "MedicalMonitoringWorkspace.jsx"), "utf8");
  const productSource = fs.readFileSync(path.join(here, "MedicalMonitoringProductLoop.jsx"), "utf8");
  check(pageSource.includes('keyboardEvent.key !== "ArrowLeft" && keyboardEvent.key !== "ArrowRight"'), "timeline event buttons support left/right arrow navigation");
  check(productSource.includes('onJourneyRowSelect={selectResultContinuityRow}'), "R7 product route supplies the row-switch callback");
  check(productSource.includes("const selectResultContinuityRow = useCallback((row) =>"), "continuity row switching has a route-preserving ProductLoop callback");
  check(productSource.includes('event_ref: row.event_ref || ""') && productSource.includes('risk_anchor_ref: row.risk_anchor_ref || ""') && productSource.includes('visit_ref: row.visit_ref || ""'), "row switch replaces all row selection keys and clears stale event/anchor/visit values");
  check(pageSource.includes('const [selectedJourneyRowRef, setSelectedJourneyRowRef] = useState("")') && pageSource.includes("setSelectedJourneyRowRef(text(row.row_ref))"), "row switch keeps the exact active continuity row without remounting the workspace");
  check(pageSource.includes("const drawerRows = selectedRiskRows.length && route.risk_instance_ref"), "risk context exposes all rows bound to the selected risk instead of truncating to event rows");
  check(!productSource.includes("route.event_ref, route.risk_anchor_ref, route.risk_instance_ref, route.site_ref"), "drawer selection keys do not retrigger the subject result request");
  check(productSource.includes('risk_instance_ref: "",\n  }), [navigate, routeView]);'), "direct event selection clears a stale risk context before event rows are resolved");
  check(pageSource.includes("const selectWorkspaceRisk = (risk) =>") && pageSource.includes("const selectWorkspaceEvent = (event) =>"), "direct risk/event selection clears the locally selected change row");
}

console.log(`medicalMonitoringJourneyDrawerRender: ${passed} passed`);
