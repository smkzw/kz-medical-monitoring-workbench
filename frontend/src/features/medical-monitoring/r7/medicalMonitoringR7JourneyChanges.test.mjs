// R7 Slice-08C-3 pure-function tests (contract §7.1): same-identity
// same-window filtering, event/risk binding, server-order preservation,
// primary marker, multi-change handling, severity wording and the drawer
// route-close patch. The same-window cases must cover equal boundaries, true
// containment, partial overlap, disjoint windows and missing window fields.
// No DOM: these are the functions the Journey lane renderer and drawer bind to.
//
// Contract source:
// - context/medical_monitoring_r7_slice08c3_journey_changes_drawer_contract_20260829.md
// - reviews/medical_monitoring_r7_slice08c_chinese_continuity_visual_contract_v0_2_20260829.md (v0.2 wins)

import assert from "node:assert/strict";

import {
  R7_JOURNEY_CHANGE_KIND_VISUAL,
  R7_JOURNEY_CHANGE_TONES,
  R7_JOURNEY_DRAWER_FALLBACK_TEXTS,
  R7_JOURNEY_DRAWER_KEYS,
  R7_JOURNEY_DRAWER_SECTION_ORDER,
  R7_JOURNEY_TRUNCATION_PREFIX,
  R7_JOURNEY_TRUNCATION_SUFFIX,
  bindR7ContinuityRowsToJourney,
  filterR7ContinuityRowsForJourney,
  r7EventChangeMarker,
  r7EventChangeRows,
  r7JourneyAxisWindow,
  r7JourneyBeforeAfterModel,
  r7JourneyContinuityRows,
  r7JourneyDrawerClosePatch,
  r7JourneyDrawerCurrentRow,
  r7JourneyQueryDraft,
  r7JourneySeverityLabel,
  r7JourneyTruncationText,
  r7JourneyWindowContains,
  r7RiskChangeRows,
} from "./medicalMonitoringR7JourneyChanges.mjs";
import {
  R7_CONTINUITY_CHANGE_KIND_TEXTS,
  R7_CONTINUITY_CHANGE_KINDS,
  R7_CONTINUITY_FIRST_ANALYSIS_TEXT,
} from "./medicalMonitoringR7ContinuityProjection.mjs";
import { r7ContinuityRowSeverityLabel } from "./medicalMonitoringR7ContinuityFilter.mjs";

let passed = 0;
function check(condition, message) {
  assert.equal(Boolean(condition), true, message);
  passed += 1;
}

// --- minimal row/event/risk builders (full row shape is the projection
// validator's contract; these functions only read the fields they need) ---

function riskRow(overrides = {}) {
  return {
    object_type: "risk",
    change_kind: "new",
    change_text: "新增",
    severity_before_text: "",
    severity_after_text: "高",
    ordinal: 0,
    site_ref: "site/01",
    subject_ref: "S/01",
    subject_label: "受试者 001",
    window_start: "2026-01-01",
    window_end: "2026-03-31",
    risk_instance_ref: "risk-i-1",
    risk_anchor_ref: "risk-a-1",
    event_ref: "event-1",
    source_locator_ref: "source-1",
    reason_text: "上轮未覆盖",
    ...overrides,
  };
}

function journeyEvent(overrides = {}) {
  return {
    eventRef: "event-1",
    domain: "ae",
    eventLabel: "发热",
    riskAnchorRefs: ["risk-a-1"],
    ...overrides,
  };
}

function journeyRisk(overrides = {}) {
  return {
    riskInstanceRef: "risk-i-1",
    riskAnchorRef: "risk-a-1",
    eventRef: "event-1",
    severity: "high",
    ...overrides,
  };
}

// --- seven-kind visual model (§4.3): icon + Chinese + semantic tone ---
{
  check(
    JSON.stringify(R7_CONTINUITY_CHANGE_KINDS) === JSON.stringify(Object.keys(R7_JOURNEY_CHANGE_KIND_VISUAL)),
    "visual model covers exactly the frozen seven kinds",
  );
  const expectedIcons = {
    new: "CirclePlus",
    upgraded: "CircleArrowUp",
    continued: "CircleDot",
    downgraded: "CircleArrowDown",
    closed: "CircleCheck",
    reopened: "RotateCcw",
    needs_rejudgment: "CircleHelp",
  };
  for (const kind of R7_CONTINUITY_CHANGE_KINDS) {
    check(
      R7_JOURNEY_CHANGE_KIND_VISUAL[kind].icon === expectedIcons[kind],
      `${kind} uses the frozen Lucide icon ${expectedIcons[kind]}`,
    );
    check(
      R7_JOURNEY_CHANGE_KIND_VISUAL[kind].label === R7_CONTINUITY_CHANGE_KIND_TEXTS[kind],
      `${kind} label is the frozen Chinese wording`,
    );
    check(
      R7_JOURNEY_CHANGE_TONES.includes(R7_JOURNEY_CHANGE_KIND_VISUAL[kind].tone),
      `${kind} tone is inside the closed semantic tone set`,
    );
  }
  check(
    R7_JOURNEY_CHANGE_KIND_VISUAL.upgraded.tone === "danger" && R7_JOURNEY_CHANGE_KIND_VISUAL.reopened.tone === "danger",
    "升级 and 重开 carry the danger tone",
  );
  check(
    R7_JOURNEY_CHANGE_KIND_VISUAL.downgraded.tone === "success" && R7_JOURNEY_CHANGE_KIND_VISUAL.closed.tone === "success",
    "降级 and 关闭 carry the success tone",
  );
  check(
    R7_JOURNEY_CHANGE_KIND_VISUAL.needs_rejudgment.tone === "warning",
    "需重新判断 carries the warning tone",
  );
  check(R7_JOURNEY_CHANGE_KIND_VISUAL.new.tone === "info", "新增 carries the info tone");
  check(R7_JOURNEY_CHANGE_KIND_VISUAL.continued.tone === "neutral", "持续 carries the neutral tone");
  check(
    r7JourneySeverityLabel === r7ContinuityRowSeverityLabel,
    "severity wording re-export is the 08C-2 function",
  );
  check(R7_JOURNEY_CHANGE_KIND_VISUAL.unknown === undefined, "unknown kinds are not in the visual model");
  passed += 30;
}

// --- drawer fixed content order and fallback texts (§5.2) ---
{
  check(
    JSON.stringify(R7_JOURNEY_DRAWER_SECTION_ORDER)
      === JSON.stringify(["title", "event_category", "risk_level", "change", "date", "before_after", "related_records", "query_draft", "source"]),
    "drawer section order is the frozen nine-item sequence",
  );
  check(R7_JOURNEY_DRAWER_FALLBACK_TEXTS.eventCategory === "类别待确认", "category fallback is fixed");
  check(R7_JOURNEY_DRAWER_FALLBACK_TEXTS.riskLevel === "风险等级待确认", "risk-level fallback is fixed");
  check(R7_JOURNEY_DRAWER_FALLBACK_TEXTS.change === "本轮变化待确认", "change fallback is fixed");
  check(R7_JOURNEY_DRAWER_FALLBACK_TEXTS.date === "日期待确认", "date fallback is fixed");
  check(R7_JOURNEY_DRAWER_FALLBACK_TEXTS.beforeAfter === "本轮未提供前后比较依据", "before/after fallback is fixed");
  check(R7_JOURNEY_DRAWER_FALLBACK_TEXTS.relatedRecords === "本轮未提供关联记录", "related-records fallback is fixed");
  check(R7_JOURNEY_DRAWER_FALLBACK_TEXTS.queryDraft === "本轮未提供 Query 草稿", "query-draft fallback is fixed");
  check(R7_JOURNEY_DRAWER_FALLBACK_TEXTS.source === "原始记录位置待确认", "source fallback is fixed");
  passed += 9;
}

// --- axis window resolution (§3.2): temporalSpine wins, route falls back ---
{
  const spinePayload = {
    projection: {
      temporalSpine: { windowStart: "2026-01-01", windowEnd: "2026-03-31" },
    },
  };
  const route = { window_start: "2025-12-01", window_end: "2026-04-30" };
  check(
    JSON.stringify(r7JourneyAxisWindow(spinePayload, route))
      === JSON.stringify({ windowStart: "2026-01-01", windowEnd: "2026-03-31" }),
    "temporalSpine window is the only axis window source when present",
  );
  const snakePayload = {
    projection: { temporalSpine: { window_start: "2026-02-01", window_end: "2026-02-28" } },
  };
  check(
    JSON.stringify(r7JourneyAxisWindow(snakePayload, route))
      === JSON.stringify({ windowStart: "2026-02-01", windowEnd: "2026-02-28" }),
    "snake_case temporalSpine window fields are accepted",
  );
  check(
    JSON.stringify(r7JourneyAxisWindow({ projection: { temporalSpine: {} } }, route))
      === JSON.stringify({ windowStart: "2025-12-01", windowEnd: "2026-04-30" }),
    "missing server axis window falls back to the route window",
  );
  check(
    JSON.stringify(r7JourneyAxisWindow(
      { projection: { temporalSpine: { windowStart: "2026-01-01" } } },
      route,
    ))
      === JSON.stringify({ windowStart: "2025-12-01", windowEnd: "2026-04-30" }),
    "half-provided server axis window falls back to the route window entirely",
  );
  check(r7JourneyAxisWindow(null, route) && r7JourneyAxisWindow(null, route).windowStart === "2025-12-01", "missing payload still falls back to the route window");
  check(
    r7JourneyAxisWindow({ projection: {} }, {}) === null,
    "no axis window anywhere resolves to null",
  );
  check(
    r7JourneyAxisWindow(null, { window_start: "2026-01-01" }) === null,
    "half-provided route window resolves to null",
  );
  passed += 7;
}

// --- same-window containment: equal, true containment, partial overlap,
// disjoint, missing fields (§3.2) ---
{
  const axis = { windowStart: "2026-01-01", windowEnd: "2026-03-31" };
  check(
    r7JourneyWindowContains(riskRow({ window_start: "2026-01-01", window_end: "2026-03-31" }), axis),
    "equal boundaries are inside the axis window",
  );
  check(
    r7JourneyWindowContains(riskRow({ window_start: "2026-01-15", window_end: "2026-03-15" }), axis),
    "true containment is inside the axis window",
  );
  check(
    !r7JourneyWindowContains(riskRow({ window_start: "2026-03-01", window_end: "2026-04-30" }), axis),
    "partial overlap is outside the axis window",
  );
  check(
    !r7JourneyWindowContains(riskRow({ window_start: "2026-04-01", window_end: "2026-06-30" }), axis),
    "disjoint windows are outside the axis window",
  );
  check(
    !r7JourneyWindowContains(riskRow({ window_start: "2025-12-01", window_end: "2025-12-31" }), axis),
    "window ending before the axis start is outside",
  );
  check(
    !r7JourneyWindowContains(riskRow({ window_start: "", window_end: "2026-03-31" }), axis),
    "missing row window_start stays outside",
  );
  check(
    !r7JourneyWindowContains(riskRow({ window_start: "2026-01-01", window_end: "" }), axis),
    "missing row window_end stays outside",
  );
  check(
    !r7JourneyWindowContains(riskRow(), { windowStart: "", windowEnd: "2026-03-31" }),
    "missing axis windowStart keeps every row outside",
  );
  check(
    !r7JourneyWindowContains(riskRow(), { windowStart: "2026-01-01", windowEnd: "" }),
    "missing axis windowEnd keeps every row outside",
  );
  check(!r7JourneyWindowContains(null, axis), "null rows stay outside");
  check(!r7JourneyWindowContains(riskRow(), null), "null axis keeps rows outside");
  passed += 11;
}

// --- same-identity same-window filter (§3.2): identity, window cases, order ---
{
  const AXIS = { windowStart: "2026-01-01", windowEnd: "2026-03-31" };
  const rows = [
    riskRow({ ordinal: 0, window_start: "2026-01-01", window_end: "2026-03-31" }), // equal
    riskRow({ ordinal: 1, window_start: "2026-01-15", window_end: "2026-03-15" }), // containment
    riskRow({ ordinal: 2, window_start: "2026-03-01", window_end: "2026-04-30" }), // partial overlap
    riskRow({ ordinal: 3, window_start: "2026-04-01", window_end: "2026-06-30" }), // disjoint
    riskRow({ ordinal: 4, window_start: "", window_end: "2026-03-31" }), // missing start
    riskRow({ ordinal: 5, window_start: "2026-01-01", window_end: "" }), // missing end
    riskRow({ ordinal: 6, subject_ref: "S/99", window_start: "2026-01-01", window_end: "2026-03-31" }), // other subject
    riskRow({ ordinal: 7, site_ref: "site/99", window_start: "2026-01-01", window_end: "2026-03-31" }), // other site
    {
      object_type: "query_draft",
      ordinal: 8,
      site_ref: "site/01",
      subject_ref: "S/01",
      window_start: "2026-01-01",
      window_end: "2026-03-31",
      event_ref: "event-q",
    }, // non-risk inside the window
    {
      object_type: "monitoring_output",
      ordinal: 9,
      site_ref: "site/01",
      subject_ref: "S/01",
      window_start: "2026-01-01",
      window_end: "2026-03-31",
      event_ref: "event-o",
    }, // non-risk inside the window
  ];
  const filtered = filterR7ContinuityRowsForJourney(rows, {
    siteRef: "site/01",
    subjectRef: "S/01",
    windowStart: AXIS.windowStart,
    windowEnd: AXIS.windowEnd,
  });
  check(filtered.length === 2, "only the equal and true-containment rows of the same identity pass");
  check(
    filtered.every((row) => row.ordinal <= 1),
    "non-risk, cross-identity, overlapping and missing-date rows are all excluded",
  );
  check(
    JSON.stringify(filtered.map((row) => row.ordinal)) === JSON.stringify([0, 1]),
    "filter preserves the server-authoritative order",
  );
  check(filterR7ContinuityRowsForJourney(rows, {}).length === 0, "missing journey identity fails closed");
  check(
    filterR7ContinuityRowsForJourney(rows, { siteRef: "site/01", subjectRef: "S/01", windowStart: "", windowEnd: "" }).length === 0,
    "missing axis window fails closed",
  );
  check(filterR7ContinuityRowsForJourney(null, { siteRef: "site/01", subjectRef: "S/01", windowStart: "2026-01-01", windowEnd: "2026-03-31" }).length === 0, "null rows filter to an empty list");
  check(
    filterR7ContinuityRowsForJourney([riskRow({ subject_ref: "  S/01  " })], { siteRef: "site/01", subjectRef: "S/01", windowStart: "2026-01-01", windowEnd: "2026-03-31" }).length === 1,
    "row identity is trim-normalized before comparison",
  );
  passed += 7;
}

// --- combined reader (§3.2/§3.4): verified envelopes only, no fabricated markers ---
{
  const envelope = {
    ok: true,
    value: {
      kind: "continuity",
      comparison: {
        rows: [
          riskRow({ ordinal: 0 }),
          riskRow({ ordinal: 1, subject_ref: "S/99" }),
          riskRow({ ordinal: 2, window_start: "2026-04-01", window_end: "2026-06-30" }),
          { object_type: "query_draft", ordinal: 3, site_ref: "site/01", subject_ref: "S/01", window_start: "2026-01-01", window_end: "2026-03-31", event_ref: "event-q" },
        ],
      },
    },
  };
  const payload = {
    projection: { temporalSpine: { windowStart: "2026-01-01", windowEnd: "2026-03-31" } },
  };
  const route = { site_ref: "site/01", subject_ref: "S/01", window_start: "2025-01-01", window_end: "2025-12-31" };
  const selected = r7JourneyContinuityRows(envelope, payload, route);
  check(selected.length === 1 && selected[0].ordinal === 0, "combined reader selects only the same-identity same-window risk row");
  check(r7JourneyContinuityRows({ ok: false, text: "本轮变化暂不可查看" }, payload, route).length === 0, "failed envelopes yield no markers");
  check(r7JourneyContinuityRows(null, payload, route).length === 0, "null envelopes yield no markers");
  check(
    r7JourneyContinuityRows({ ok: true, value: { kind: "unavailable" } }, payload, route).length === 0,
    "non-continuity values yield no markers",
  );
  check(
    r7JourneyContinuityRows(envelope, { projection: {} }, route).length === 0,
    "missing axis window yields no markers even with a verified envelope",
  );
  check(
    r7JourneyContinuityRows(envelope, payload, {}).length === 0,
    "missing journey identity yields no markers",
  );
  passed += 6;
}

// --- event/risk binding (§3.5): event_ref, anchor fallback, risk fallback, unbound ---
{
  const events = [
    journeyEvent({ eventRef: "event-1" }),
    journeyEvent({ eventRef: "event-2", riskAnchorRefs: ["risk-a-2"] }),
    journeyEvent({ eventRef: "event-3", riskAnchorRefs: undefined, risk_anchor_refs: ["risk-a-3"] }),
  ];
  const risks = [journeyRisk({ riskInstanceRef: "risk-i-9" })];
  const rows = [
    riskRow({ ordinal: 0, event_ref: "event-1" }), // exact event_ref
    riskRow({ ordinal: 1, event_ref: "", risk_anchor_ref: "risk-a-2" }), // anchor fallback (camelCase)
    riskRow({ ordinal: 2, event_ref: "", risk_anchor_ref: "risk-a-3" }), // anchor fallback (snake_case)
    riskRow({ ordinal: 3, event_ref: "", risk_anchor_ref: "", risk_instance_ref: "risk-i-9" }), // risk fallback
    riskRow({ ordinal: 4, event_ref: "", risk_anchor_ref: "", risk_instance_ref: "" }), // unbound
    riskRow({ ordinal: 5, event_ref: "event-missing", risk_anchor_ref: "", risk_instance_ref: "" }), // unknown event_ref
  ];
  const binding = bindR7ContinuityRowsToJourney(rows, events, risks);
  check(binding.events.length === 3, "three events carry bound rows");
  check(
    JSON.stringify(r7EventChangeRows(binding, "event-1").map((row) => row.ordinal)) === JSON.stringify([0]),
    "exact event_ref binds the row to that event",
  );
  check(
    JSON.stringify(r7EventChangeRows(binding, "event-2").map((row) => row.ordinal)) === JSON.stringify([1]),
    "risk_anchor_ref binds to the event already carrying the anchor (camelCase)",
  );
  check(
    JSON.stringify(r7EventChangeRows(binding, "event-3").map((row) => row.ordinal)) === JSON.stringify([2]),
    "risk_anchor_ref binds to the event already carrying the anchor (snake_case)",
  );
  check(
    JSON.stringify(r7RiskChangeRows(binding, "risk-i-9").map((row) => row.ordinal)) === JSON.stringify([3]),
    "risk_instance_ref binds to the current risk when no event matches",
  );
  check(binding.unbound.length === 2, "unbound rows stay listed and never create virtual nodes");
  check(
    JSON.stringify(binding.unbound.map((row) => row.ordinal)) === JSON.stringify([4, 5]),
    "unbound rows keep server order",
  );
  check(r7EventChangeRows(binding, "event-4").length === 0, "unknown events return an empty row set");
  check(r7RiskChangeRows(binding, "risk-i-99").length === 0, "unknown risks return an empty row set");
  check(r7EventChangeRows(null, "event-1").length === 0, "null bindings return an empty row set");
  check(r7RiskChangeRows(binding, "").length === 0, "empty risk refs return an empty row set");
  passed += 10;
}

// --- binding priority (§3.5): exact event_ref wins over the anchor fallback ---
{
  const events = [
    journeyEvent({ eventRef: "event-1", riskAnchorRefs: ["risk-a-1", "risk-a-2"] }),
    journeyEvent({ eventRef: "event-2", riskAnchorRefs: ["risk-a-2"] }),
  ];
  const rows = [riskRow({ ordinal: 0, event_ref: "event-1", risk_anchor_ref: "risk-a-2" })];
  const binding = bindR7ContinuityRowsToJourney(rows, events, []);
  check(
    r7EventChangeRows(binding, "event-1").length === 1 && r7EventChangeRows(binding, "event-2").length === 0,
    "exact event_ref takes priority even when the anchor also matches another event",
  );
  const anchorOnly = bindR7ContinuityRowsToJourney(
    [riskRow({ ordinal: 0, event_ref: "", risk_anchor_ref: "risk-a-2" })],
    events,
    [],
  );
  check(
    anchorOnly.events.length === 1 && anchorOnly.events[0].eventRef === "event-1",
    "anchor fallback binds to the first event carrying the anchor",
  );
  check(
    r7EventChangeRows(anchorOnly, "event-1").length === 1 && r7EventChangeRows(anchorOnly, "event-2").length === 0,
    "anchor fallback binds to the first carrying event only",
  );
  passed += 3;
}

// --- primary marker (§4.5): minimal ordinal, count suffix, multi-change ---
{
  const single = r7EventChangeMarker([riskRow({ ordinal: 3, change_kind: "upgraded" })]);
  check(
    single && single.changeKind === "upgraded" && single.changeText === "升级" && single.icon === "CircleArrowUp",
    "single-change marker shows the frozen word and icon",
  );
  check(single.total === 1 && single.countSuffix === "", "single-change marker states no count suffix");
  check(single.row.ordinal === 3, "single-change marker keeps the bound row");

  const multi = r7EventChangeMarker([
    riskRow({ ordinal: 5, change_kind: "continued" }),
    riskRow({ ordinal: 2, change_kind: "new" }),
    riskRow({ ordinal: 9, change_kind: "closed" }),
  ]);
  check(
    multi && multi.changeKind === "new" && multi.changeText === "新增",
    "multi-change marker picks the row with the minimal server ordinal",
  );
  check(multi.row.ordinal === 2, "minimal-ordinal row is the primary row");
  check(multi.total === 3 && multi.countSuffix === "，共 3 条变化", "multi-change marker states the total in the accessible suffix");
  check(multi.icon === "CirclePlus" && multi.tone === "info", "primary marker carries the primary row's visual model");

  const repeated = r7EventChangeMarker([
    riskRow({ ordinal: 1, change_kind: "continued" }),
    riskRow({ ordinal: 1, change_kind: "closed" }),
    riskRow({ ordinal: 0, change_kind: "reopened" }),
  ]);
  check(repeated.changeKind === "reopened", "duplicate ordinals still select by ordinal order");

  check(r7EventChangeMarker([]) === null, "empty row sets render no marker");
  check(r7EventChangeMarker(null) === null, "null row sets render no marker");
  check(
    r7EventChangeMarker([riskRow({ change_kind: "not_a_kind" })]) === null,
    "kinds outside the closed set render no marker",
  );
  check(r7EventChangeMarker([null, "x"]) === null, "malformed rows render no marker");
  passed += 8;
}

// --- drawer current-row selection (§5.2): route risk_instance_ref wins, else first ---
{
  const rows = [
    riskRow({ ordinal: 0, risk_instance_ref: "risk-i-1" }),
    riskRow({ ordinal: 1, risk_instance_ref: "risk-i-2" }),
    riskRow({ ordinal: 2, risk_instance_ref: "risk-i-3" }),
  ];
  const picked = r7JourneyDrawerCurrentRow(rows, { risk_instance_ref: "risk-i-2" });
  check(picked && picked.ordinal === 1, "current row prefers the route risk_instance_ref");
  const first = r7JourneyDrawerCurrentRow(rows, {});
  check(first && first.ordinal === 0, "current row falls back to the first bound row in server order");
  const unmatched = r7JourneyDrawerCurrentRow(rows, { risk_instance_ref: "risk-i-99" });
  check(unmatched && unmatched.ordinal === 0, "unmatched route ref falls back to the first row");
  check(r7JourneyDrawerCurrentRow([], {}) === null, "empty row sets have no current row");
  check(r7JourneyDrawerCurrentRow(null, {}) === null, "null row sets have no current row");
  passed += 5;
}

// --- severity wording (§4.4): explicit text, never color/single-character only ---
{
  check(r7ContinuityRowSeverityLabel(riskRow({ change_kind: "upgraded", severity_before_text: "中", severity_after_text: "高" })) === "中 → 高", "upgraded shows 前等级 → 后等级");
  check(r7ContinuityRowSeverityLabel(riskRow({ change_kind: "closed", severity_before_text: "高", severity_after_text: "" })) === "高（已关闭）", "closed shows 前等级（已关闭）");
  check(r7ContinuityRowSeverityLabel(riskRow({ change_kind: "reopened", severity_after_text: "高" })) === "高", "reopened shows the current level");
  check(r7ContinuityRowSeverityLabel(riskRow({ change_kind: "continued", severity_before_text: "低", severity_after_text: "低" })) === "低 → 低", "continued shows the explicit before → after");
  check(r7ContinuityRowSeverityLabel(riskRow({ change_kind: "new", severity_after_text: "" })) === "等级变化待确认", "missing level falls back to the frozen confirm text");
  passed += 5;
}

// --- before/after basis and query draft (§6) ---
{
  const compared = { comparison_text: "已与上次监查结果比较" };
  const detail = r7JourneyBeforeAfterModel(compared, riskRow({
    severity_before_text: "中",
    severity_after_text: "高",
    reason_text: "实验室复查确认",
  }));
  check(
    detail.state === "detail"
      && detail.before === "中"
      && detail.after === "高"
      && detail.reason === "实验室复查确认",
    "before/after model separates prior level, current level and reason",
  );
  check(
    detail.text === "上轮 中；本轮 高；变化原因：实验室复查确认",
    "before/after detail text distinguishes the three parts",
  );
  const firstAnalysis = r7JourneyBeforeAfterModel({ comparison_text: R7_CONTINUITY_FIRST_ANALYSIS_TEXT }, riskRow());
  check(
    firstAnalysis.state === "first_analysis" && firstAnalysis.text === R7_CONTINUITY_FIRST_ANALYSIS_TEXT,
    "first analysis shows the frozen 首次全面分析 baseline text",
  );
  const empty = r7JourneyBeforeAfterModel(compared, riskRow({ severity_before_text: "", severity_after_text: "", reason_text: "" }));
  check(
    empty.state === "none" && empty.text === "本轮未提供前后比较依据",
    "missing before/after detail uses the fixed fallback",
  );
  check(
    r7JourneyBeforeAfterModel(compared, null).text === "本轮未提供前后比较依据",
    "null rows use the fixed fallback",
  );
  const queryRisk = { evidenceSummary: { query_draft: "请核实发热与实验室结果的时间顺序" } };
  check(
    r7JourneyQueryDraft(queryRisk) === "请核实发热与实验室结果的时间顺序",
    "query draft is taken from the selected R5 risk evidenceSummary.query_draft",
  );
  check(r7JourneyQueryDraft({ evidence_summary: { query_draft: "snake 草稿" } }) === "snake 草稿", "snake_case evidence summary is accepted");
  check(r7JourneyQueryDraft({}) === "", "missing query draft yields an empty string for the fallback");
  check(r7JourneyQueryDraft(null) === "", "null risks yield no query draft");
  passed += 8;
}

// --- drawer route-close patch (§5.1): clears the four keys, preserves identity ---
{
  const route = {
    project_ref: "project/01",
    result_context_token: "result-context:abc",
    site_ref: "site/01",
    subject_ref: "S/01",
    spine_ref: "spine/01",
    window_start: "2026-01-01",
    window_end: "2026-03-31",
    view: "journey",
    visit_ref: "visit-1",
    event_ref: "event-1",
    risk_anchor_ref: "risk-a-1",
    risk_instance_ref: "risk-i-1",
    axis_mode: "calendar",
  };
  const closed = r7JourneyDrawerClosePatch(route);
  check(
    JSON.stringify(R7_JOURNEY_DRAWER_KEYS) === JSON.stringify(["event_ref", "risk_instance_ref", "risk_anchor_ref", "visit_ref"]),
    "drawer close clears exactly the four frozen keys",
  );
  for (const key of R7_JOURNEY_DRAWER_KEYS) {
    check(closed[key] === "", `route close patch clears ${key}`);
  }
  check(closed.project_ref === "project/01", "route close patch preserves the project");
  check(closed.result_context_token === "result-context:abc", "route close patch preserves the result context");
  check(closed.site_ref === "site/01", "route close patch preserves the center");
  check(closed.subject_ref === "S/01", "route close patch preserves the subject");
  check(closed.spine_ref === "spine/01", "route close patch preserves the spine");
  check(closed.window_start === "2026-01-01" && closed.window_end === "2026-03-31", "route close patch preserves the axis window");
  check(closed.view === "journey", "route close patch preserves the journey/profile/timeline view");
  check(closed.axis_mode === "calendar", "route close patch preserves untouched keys");
  check(
    JSON.stringify(r7JourneyDrawerClosePatch({ view: "timeline" })) === JSON.stringify({ view: "timeline", event_ref: "", risk_instance_ref: "", risk_anchor_ref: "", visit_ref: "" }),
    "route close patch is idempotent on already-clear routes",
  );
  check(
    JSON.stringify(r7JourneyDrawerClosePatch(null)) === JSON.stringify({}),
    "route close patch handles null routes",
  );
  check(
    JSON.stringify(r7JourneyDrawerClosePatch({ event_ref: "e" })) === JSON.stringify({ event_ref: "", risk_instance_ref: "", risk_anchor_ref: "", visit_ref: "" }),
    "route close patch never mutates the input object",
  );
  check(
    Object.isFrozen(r7JourneyDrawerClosePatch(route)),
    "route close patch returns a frozen patch",
  );
  passed += 14;
}

// --- truncation hint (§3.6): fixed prompt, axis markers never imply fullness ---
{
  const hint = r7JourneyTruncationText({ truncated: true, shown_count: 12, total_count: 80 });
  check(
    hint === `${R7_JOURNEY_TRUNCATION_PREFIX} 12 ${R7_JOURNEY_TRUNCATION_SUFFIX}`,
    "truncated comparisons render the frozen M-prompt",
  );
  check(hint.includes("本轮变化较多，当前仅显示服务端已返回的前 12 条"), "truncation prompt quotes the returned row count");
  check(hint.includes("请返回项目或中心概览查看完整范围说明。"), "truncation prompt points to the full-scope surface");
  check(r7JourneyTruncationText({ truncated: false, shown_count: 12 }) === "", "untruncated comparisons render no hint");
  check(r7JourneyTruncationText(null) === "", "missing comparisons render no hint");
  check(
    r7JourneyTruncationText({ truncated: true, shown_count: 1.5 }) === `${R7_JOURNEY_TRUNCATION_PREFIX} 0 ${R7_JOURNEY_TRUNCATION_SUFFIX}`,
    "malformed counts degrade to zero instead of leaking raw values",
  );
  passed += 6;
}

console.log(`medicalMonitoringR7JourneyChanges: ${passed} passed`);
