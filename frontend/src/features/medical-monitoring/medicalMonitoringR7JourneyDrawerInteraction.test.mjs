// R7 Slice-08C-3 interaction model tests (contract §7.3/§5.3): the shared
// overlay/push threshold, the overlay focus-trap step, the keyboard decision
// model (Esc / Tab / Shift+Tab per mode), the focus-restore decision and the
// drawer section model (fixed order, fallback texts, per-row switching,
// before/after basis, Query draft source). Pure functions only; the DOM
// effects that consume them (body scroll lock, initial focus, trap) stay for
// 08C-4 real-browser verification per contract §7.6.
//
// Contract source:
// - context/medical_monitoring_r7_slice08c3_journey_changes_drawer_contract_20260829.md
// - reviews/medical_monitoring_r7_slice08c_chinese_continuity_visual_contract_v0_2_20260829.md (v0.2 wins)

import assert from "node:assert/strict";

import {
  R7_JOURNEY_CONTENT_MIN_WIDTH,
  R7_JOURNEY_DRAWER_GAP,
  R7_JOURNEY_DRAWER_WIDTH,
  R7_JOURNEY_DRAWER_FOCUSABLE_SELECTOR,
  R7_JOURNEY_OVERLAY_DRAWER_MAX_WIDTH,
  R7_JOURNEY_VIEWPORT_PUSH_MIN,
  r7JourneyDrawerKeyAction,
  r7JourneyDrawerLayoutMode,
  r7JourneyDrawerSections,
  r7JourneyFocusStep,
  r7JourneyRestoreTarget,
} from "./medicalMonitoringR7JourneyDrawerModel.mjs";
import {
  R7_JOURNEY_DRAWER_FALLBACK_TEXTS,
  R7_JOURNEY_DRAWER_SECTION_ORDER,
  R7_JOURNEY_CHANGE_KIND_VISUAL,
  r7JourneyBeforeAfterModel,
} from "./medicalMonitoringR7JourneyChanges.mjs";
import {
  R7_CONTINUITY_CHANGE_KINDS,
  R7_CONTINUITY_FIRST_ANALYSIS_TEXT,
} from "./medicalMonitoringR7ContinuityProjection.mjs";

let passed = 0;
function check(condition, message) {
  assert.equal(Boolean(condition), true, message);
  passed += 1;
}

// --- shared threshold constants (§5.3): single source for tests + 08C-4 ---
check(R7_JOURNEY_VIEWPORT_PUSH_MIN === 1440, "push requires viewport >= 1440px");
check(R7_JOURNEY_DRAWER_WIDTH === 420, "push drawer width is 420px");
check(R7_JOURNEY_DRAWER_GAP === 16, "drawer gap is 16px");
check(R7_JOURNEY_CONTENT_MIN_WIDTH === 760, "main content keeps >= 760px");
check(R7_JOURNEY_OVERLAY_DRAWER_MAX_WIDTH === 480, "overlay drawer caps at 480px");
passed += 5;

// --- layout mode: viewport rule first, then the host content rule (§5.3) ---
{
  check(r7JourneyDrawerLayoutMode({ viewportWidth: 1280, hostContentWidth: 1200 }) === "overlay", "1280 is always overlay");
  check(r7JourneyDrawerLayoutMode({ viewportWidth: 1439, hostContentWidth: 1600 }) === "overlay", "1439 is still overlay even with a wide host");
  check(r7JourneyDrawerLayoutMode({ viewportWidth: 1440, hostContentWidth: 1196 }) === "push", "1440 + 1196 host keeps exactly 760px main content -> push");
  check(r7JourneyDrawerLayoutMode({ viewportWidth: 1440, hostContentWidth: 1195 }) === "overlay", "1440 + 1195 host leaves 759px -> overlay");
  check(r7JourneyDrawerLayoutMode({ viewportWidth: 1920, hostContentWidth: 1600 }) === "push", "1920 with a wide host pushes");
  check(r7JourneyDrawerLayoutMode({ viewportWidth: 1440, hostContentWidth: 800 }) === "overlay", "narrow host content forces overlay at 1440");
  check(r7JourneyDrawerLayoutMode({ viewportWidth: 0, hostContentWidth: 0 }) === "overlay", "unmeasured sizes default to overlay");
  check(r7JourneyDrawerLayoutMode({}) === "overlay", "missing sizes default to overlay");
  check(r7JourneyDrawerLayoutMode({ viewportWidth: 1440, hostContentWidth: "abc" }) === "overlay", "non-numeric host width defaults to overlay");
  const pushHost = R7_JOURNEY_CONTENT_MIN_WIDTH + R7_JOURNEY_DRAWER_WIDTH + R7_JOURNEY_DRAWER_GAP;
  check(r7JourneyDrawerLayoutMode({ viewportWidth: 1600, hostContentWidth: pushHost }) === "push", "boundary host width pushes");
  check(r7JourneyDrawerLayoutMode({ viewportWidth: 1600, hostContentWidth: pushHost - 1 }) === "overlay", "one px below the boundary host width overlays");
}
passed += 11;

// --- focus trap step (§5.3 overlay): wrap both directions ---
{
  check(r7JourneyFocusStep(0, 0) === -1, "empty focusable list yields -1");
  check(r7JourneyFocusStep(3, -1, { forward: true }) === 0, "no current index moves to the first control");
  check(r7JourneyFocusStep(3, -1, { forward: false }) === 2, "no current index + shift moves to the last control");
  check(r7JourneyFocusStep(3, 0) === 1, "forward moves to the next control");
  check(r7JourneyFocusStep(3, 2) === 0, "forward wraps from the last to the first");
  check(r7JourneyFocusStep(3, 0, { forward: false }) === 2, "backward wraps from the first to the last");
  check(r7JourneyFocusStep(3, 1, { forward: false }) === 0, "backward moves to the previous control");
  check(r7JourneyFocusStep(2, 1) === 0, "two-control trap wraps forward");
  check(r7JourneyFocusStep(2, 1, { forward: false }) === 0, "two-control trap wraps backward");
}
passed += 9;

// --- keyboard decision model (§5.3): Esc closes both modes; Tab trapped
// only in overlay; push lets the native tab order pass through ---
{
  check(r7JourneyDrawerKeyAction({ key: "Escape", mode: "overlay" }) === "close", "overlay Esc closes");
  check(r7JourneyDrawerKeyAction({ key: "Escape", mode: "push" }) === "close", "push Esc closes");
  check(r7JourneyDrawerKeyAction({ key: "Tab", mode: "overlay" }) === "next_focus", "overlay Tab is trapped forward");
  check(r7JourneyDrawerKeyAction({ key: "Tab", shiftKey: true, mode: "overlay" }) === "prev_focus", "overlay Shift+Tab is trapped backward");
  check(r7JourneyDrawerKeyAction({ key: "Tab", mode: "push" }) === null, "push Tab is not trapped");
  check(r7JourneyDrawerKeyAction({ key: "Tab", shiftKey: true, mode: "push" }) === null, "push Shift+Tab is not trapped");
  check(r7JourneyDrawerKeyAction({ key: "ArrowDown", mode: "overlay" }) === null, "non-relevant keys pass through");
  check(r7JourneyDrawerKeyAction({ key: "Enter", mode: "push" }) === null, "Enter passes through in both modes");
}
passed += 8;

// --- focus-restore decision (§5.1): trigger first, then the shared axis title ---
{
  check(r7JourneyRestoreTarget({ triggerConnected: true }) === "trigger", "connected trigger wins");
  check(r7JourneyRestoreTarget({ triggerConnected: true, axisTitleExists: true }) === "trigger", "trigger wins over the axis title");
  check(r7JourneyRestoreTarget({ triggerConnected: false, axisTitleExists: true }) === "axis_title", "missing trigger falls back to the axis title");
  check(r7JourneyRestoreTarget({ triggerConnected: false, axisTitleExists: false }) === null, "no target means no restore");
}
passed += 4;

// --- focusable selector: close + switcher + source are the trap universe ---
{
  check(R7_JOURNEY_DRAWER_FOCUSABLE_SELECTOR.includes("data-journey-close"), "close button is focusable");
  check(R7_JOURNEY_DRAWER_FOCUSABLE_SELECTOR.includes("data-change-row"), "change switcher is focusable");
  check(R7_JOURNEY_DRAWER_FOCUSABLE_SELECTOR.includes("data-journey-source"), "source entry is focusable");
  check(R7_JOURNEY_DRAWER_FOCUSABLE_SELECTOR.split(",").length === 3, "exactly the three drawer controls are focusable");
}
passed += 4;

// --- drawer section model (§5.2/§6): fixed order, fallbacks, per-row values ---
{
  const fallbackSections = r7JourneyDrawerSections({ event: null, risk: null, currentRow: null, comparison: null });
  check(
    fallbackSections.eventCategory === R7_JOURNEY_DRAWER_FALLBACK_TEXTS.eventCategory
      && fallbackSections.riskLevel === R7_JOURNEY_DRAWER_FALLBACK_TEXTS.riskLevel
      && fallbackSections.change === R7_JOURNEY_DRAWER_FALLBACK_TEXTS.change
      && fallbackSections.date === R7_JOURNEY_DRAWER_FALLBACK_TEXTS.date
      && fallbackSections.beforeAfter === R7_JOURNEY_DRAWER_FALLBACK_TEXTS.beforeAfter
      && fallbackSections.relatedRecords === R7_JOURNEY_DRAWER_FALLBACK_TEXTS.relatedRecords
      && fallbackSections.queryDraft === R7_JOURNEY_DRAWER_FALLBACK_TEXTS.queryDraft
      && fallbackSections.sourceText === R7_JOURNEY_DRAWER_FALLBACK_TEXTS.source,
    "all fixed fallback texts apply when no event/risk/row is available",
  );
  check(fallbackSections.sourceEnabled === false, "fallback source entry is disabled");
  const sectionKeys = Object.keys(fallbackSections).filter((key) => key !== "sourceEnabled");
  const expectedOrder = ["title", "eventCategory", "riskLevel", "change", "date", "beforeAfter", "relatedRecords", "queryDraft", "sourceText"];
  check(
    JSON.stringify(sectionKeys) === JSON.stringify(expectedOrder),
    "model fields follow the frozen section order",
  );
  check(
    JSON.stringify(R7_JOURNEY_DRAWER_SECTION_ORDER) === JSON.stringify(["title", "event_category", "risk_level", "change", "date", "before_after", "related_records", "query_draft", "source"]),
    "frozen section order is the contract order",
  );
}
passed += 4;

// --- per-row switching (§5.2): risk level/change/basis/draft follow the row
// while title/category/date stay with the current event ---
{
  const event = {
    eventRef: "evt-1",
    domain: "ae",
    domainEncoding: { domain: "ae", shortLabel: "AE" },
    eventLabel: "发热",
    start: "2026-02-01",
    dateState: "exact",
    dateLabel: "精确日期",
    visitLabel: "第 2 次访视",
    sourceLocatorRefs: ["src-1"],
  };
  const upgradedRow = {
    object_type: "risk",
    change_kind: "upgraded",
    change_text: "升级",
    severity_before_text: "中",
    severity_after_text: "高",
    title: "发热与记录一致性",
    reason_text: "记录修订。",
    risk_instance_ref: "risk-i-1",
    source_locator_ref: "src-1",
    source_count: 2,
  };
  const closedRow = {
    object_type: "risk",
    change_kind: "closed",
    change_text: "关闭",
    severity_before_text: "高",
    severity_after_text: "",
    title: "发热风险关闭",
    reason_text: "证据充分。",
    risk_instance_ref: "risk-i-2",
    source_locator_ref: "",
    source_count: 0,
  };
  const comparison = { comparison_text: "已与上次监查结果比较" };
  const upgradedSections = r7JourneyDrawerSections({ event, risk: null, currentRow: upgradedRow, comparison });
  const closedSections = r7JourneyDrawerSections({ event, risk: null, currentRow: closedRow, comparison });
  check(upgradedSections.title === "发热" && closedSections.title === "发热", "title stays with the current event across rows");
  check(upgradedSections.eventCategory === "AE" && closedSections.eventCategory === "AE", "category stays with the current event");
  check(upgradedSections.date === "2026-02-01 · 第 2 次访视" && closedSections.date === "2026-02-01 · 第 2 次访视", "date stays with the current event");
  check(upgradedSections.riskLevel === "中 → 高", "upgraded row shows 前等级 → 后等级");
  check(closedSections.riskLevel === "高（已关闭）", "closed row shows 前等级（已关闭）");
  check(upgradedSections.change === "升级" && closedSections.change === "关闭", "change word follows the row");
  check(upgradedSections.beforeAfter.includes("变化原因：记录修订。"), "reason text enters the before/after basis");
  check(upgradedSections.relatedRecords === "关联原始记录 2 条", "related records switch with the current continuity row");
  const noSourceEvent = { ...event, sourceLocatorRefs: [] };
  const closedNoSource = r7JourneyDrawerSections({ event: noSourceEvent, risk: null, currentRow: closedRow, comparison });
  check(closedNoSource.relatedRecords === R7_JOURNEY_DRAWER_FALLBACK_TEXTS.relatedRecords, "no source count falls back");
  check(upgradedSections.sourceEnabled === true && closedSections.sourceEnabled === false, "source pair gate: enabled only with instance + locator");
}
passed += 10;

// --- Query draft source (§6): only the selected risk evidenceSummary ---
{
  const risk = {
    riskType: "发热风险",
    severityLabel: "高",
    evidenceSummary: { query_draft: "请核实。" },
    sourceLocatorRef: "src-1",
    riskInstanceRef: "risk-i-1",
  };
  const row = {
    object_type: "risk",
    change_kind: "new",
    change_text: "新增",
    severity_after_text: "高",
    risk_instance_ref: "risk-i-1",
    source_locator_ref: "src-1",
  };
  const withRisk = r7JourneyDrawerSections({ event: null, risk, currentRow: row, comparison: null });
  check(withRisk.queryDraft === "请核实。", "draft comes from the selected risk evidenceSummary");
  check(withRisk.sourceEnabled === true, "risk pair enables the source entry");
  const noDraft = r7JourneyDrawerSections({ event: null, risk: { ...risk, evidenceSummary: null }, currentRow: row, comparison: null });
  check(noDraft.queryDraft === R7_JOURNEY_DRAWER_FALLBACK_TEXTS.queryDraft, "empty draft falls back");
}
passed += 3;

// --- before/after basis (§6): first analysis has no baseline ---
{
  const row = {
    object_type: "risk",
    change_kind: "new",
    change_text: "新增",
    severity_before_text: "",
    severity_after_text: "高",
  };
  const first = r7JourneyBeforeAfterModel({ comparison_text: R7_CONTINUITY_FIRST_ANALYSIS_TEXT }, row);
  check(first.state === "first_analysis" && first.text === R7_CONTINUITY_FIRST_ANALYSIS_TEXT, "first analysis shows the frozen no-baseline text");
  const sections = r7JourneyDrawerSections({ event: null, risk: null, currentRow: row, comparison: { comparison_text: R7_CONTINUITY_FIRST_ANALYSIS_TEXT } });
  check(sections.beforeAfter === R7_CONTINUITY_FIRST_ANALYSIS_TEXT, "drawer sections carry the first-analysis basis");
}
passed += 2;

// --- seven-kind visual model remains the closed set (§4.3) ---
{
  check(
    JSON.stringify(Object.keys(R7_JOURNEY_CHANGE_KIND_VISUAL)) === JSON.stringify(R7_CONTINUITY_CHANGE_KINDS),
    "visual model keys are exactly the seven frozen kinds",
  );
  const tones = new Set(Object.values(R7_JOURNEY_CHANGE_KIND_VISUAL).map((entry) => entry.tone));
  check([...tones].every((tone) => ["danger", "warning", "success", "info", "neutral"].includes(tone)), "tones stay inside the five-key closed set");
  for (const kind of R7_CONTINUITY_CHANGE_KINDS) {
    check(R7_JOURNEY_CHANGE_KIND_VISUAL[kind].icon.startsWith("Circle") || R7_JOURNEY_CHANGE_KIND_VISUAL[kind].icon === "RotateCcw", `${kind} uses an official Lucide icon`);
  }
}
passed += 3;

console.log(`medicalMonitoringR7JourneyDrawerInteraction: ${passed} passed`);
