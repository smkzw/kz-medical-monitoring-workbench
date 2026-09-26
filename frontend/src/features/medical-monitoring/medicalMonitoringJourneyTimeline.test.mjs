import assert from "node:assert/strict";
import {
  assignLaneStacks,
  buildTimelineScale,
  DETAIL_DENSITIES,
  eventGeometry,
  eventIsPendingDate,
  layoutJourneyTimeline,
  parseTimelineDate,
  TIME_VIEWPORTS,
  timelineDatePrecision,
  visitAxisDate,
} from "./medicalMonitoringJourneyTimeline.mjs";

assert.equal(parseTimelineDate("2026-04-11"), Date.UTC(2026, 3, 11));
assert.equal(parseTimelineDate(null), null);
// W05-J2 J03：仅年月不返回精确日——不补01当实际日，交给待确认集合。
assert.equal(parseTimelineDate("2026-04"), null);
assert.equal(parseTimelineDate("2026-02-31"), null);
// W05-J2：精度表达——'YYYY-MM'是月精度而非01日实际日期；带数字后缀的
// 日期必须完整拒绝（进待确认集合），不按前缀接受。
assert.equal(parseTimelineDate("2025-09-01-99"), null);
assert.equal(timelineDatePrecision("2026-04-11"), "day");
assert.equal(timelineDatePrecision("2026-04"), "month");
assert.equal(timelineDatePrecision("2025-09-01-99"), null);
assert.equal(timelineDatePrecision(""), null);
// W05-J2 A19：partial（dateState或date_precision）无论start是否完整，
// 一律进入待确认集合。
assert.equal(eventIsPendingDate({ dateState: "partial", start: "2025-09-01" }), true);
assert.equal(eventIsPendingDate({ dateState: "exact", start: "2025-09-01", date_precision: "partial" }), true);
assert.equal(visitAxisDate({ actual_date: "2026-01-10", nominal_date: "2026-01-09" }), "2026-01-10");
assert.equal(visitAxisDate({ actual_date: null, nominal_date: "2026-06-10", date_state: "missing" }), null);
assert.equal(eventIsPendingDate({ dateState: "missing", start: null }), true);
assert.equal(eventIsPendingDate({ dateState: "conflicted", start: "2026-04-10" }), true);
assert.equal(eventGeometry({ dateState: "exact", start: "2026-04-10", end: "2026-04-10" }), "point");
assert.equal(eventGeometry({ dateState: "exact", start: "2026-04-11", end: "2026-04-13" }), "interval");
assert.equal(eventGeometry({ dateState: "missing", start: null }), "pending");

assert.deepEqual(TIME_VIEWPORTS, ["fit", "custom", "focus"]);
assert.deepEqual([...DETAIL_DENSITIES], ["compact", "standard", "detailed"]);

// W05-J1 §3②：删除640下限——fit=实际容器宽。containerWidth=500 → width=500。
const fitScale = buildTimelineScale({
  windowStart: "2026-01-01",
  windowEnd: "2026-08-20",
  visits: [{ actual_date: "2026-01-10", date_state: "exact" }],
  events: [{ dateState: "exact", start: "2026-04-11", end: "2026-04-13" }],
  viewport: "fit",
  containerWidth: 500,
});
assert.equal(fitScale.width, 500, "fit width equals the measured container width, not the removed 640 floor");
assert.ok(fitScale.pad >= 66, "visit labels retain half-width clearance at both timeline endpoints");
assert.ok(fitScale.xFor("2026-01-01") >= fitScale.pad);
assert.ok(fitScale.width - fitScale.xFor("2026-08-20") >= fitScale.pad);
assert.ok(fitScale.xFor("2026-01-01") < fitScale.xFor("2026-04-11"));
assert.ok(fitScale.xFor("2026-04-11") < fitScale.xFor("2026-08-20"));

// 未测得宽度时保持px/day回退画布（等待重测由宿主组件负责）。
const unmeasured = buildTimelineScale({
  windowStart: "2026-01-01",
  windowEnd: "2026-08-20",
  viewport: "fit",
  containerWidth: null,
});
assert.ok(unmeasured.width > 0 && unmeasured.pxPerDay === 8);

// 自选视窗：px/day只由viewport/timeZoom决定（更密=5，更疏=14）。
assert.equal(buildTimelineScale({ windowStart: "2026-01-01", windowEnd: "2026-08-20", viewport: "custom", timeZoom: -1 }).pxPerDay, 5);
assert.equal(buildTimelineScale({ windowStart: "2026-01-01", windowEnd: "2026-08-20", viewport: "custom", timeZoom: 1 }).pxPerDay, 14);
assert.equal(buildTimelineScale({ windowStart: "2026-01-01", windowEnd: "2026-08-20", viewport: "custom", timeZoom: 0 }).pxPerDay, 8);

// 聚焦视窗：scale范围收窄到聚焦窗口。
const focusScale = buildTimelineScale({
  windowStart: "2026-01-01",
  windowEnd: "2026-08-20",
  viewport: "focus",
  focusWindow: { start: "2026-04-01", end: "2026-04-30" },
});
assert.equal(focusScale.windowStartIso, "2026-04-01");
assert.equal(focusScale.windowEndIso, "2026-04-30");

const stacked = assignLaneStacks([
  { eventRef: "a", x: 100, geometry: "point", severity: "high" },
  { eventRef: "b", x: 105, geometry: "point", severity: "low" },
  { eventRef: "c", x: 300, geometry: "point", severity: "medium" },
]);
assert.equal(stacked.find((mark) => mark.eventRef === "a").stackRow, 0);
assert.equal(stacked.find((mark) => mark.eventRef === "b").stackRow, 1);
assert.equal(stacked.find((mark) => mark.eventRef === "c").stackRow, 0);

const domains = [
  { domain: "ae", shape: "rounded_rect", lineStyle: "solid", shortLabel: "AE" },
  { domain: "mh", shape: "bookmark", lineStyle: "dot_dash", shortLabel: "MH" },
  { domain: "ip", shape: "hexagon", lineStyle: "step", shortLabel: "试验药" },
  { domain: "lab_exam", shape: "square", lineStyle: "trend", shortLabel: "检验/检查" },
  { domain: "cm", shape: "capsule", lineStyle: "solid", shortLabel: "合并用药" },
  { domain: "hospital_procedure", shape: "doorframe", lineStyle: "solid", shortLabel: "住院/操作" },
  { domain: "symptom_efficacy", shape: "circle", lineStyle: "trend", shortLabel: "症状/疗效" },
  { domain: "protocol_compliance", shape: "single_flag", lineStyle: "bracket", shortLabel: "方案符合" },
];

const baseLayoutInput = {
  domains,
  windowStart: "2026-01-01",
  windowEnd: "2026-08-20",
  visits: [
    { visit_ref: "v1", actual_date: "2026-01-10", date_state: "exact" },
    { visit_ref: "v6", actual_date: null, nominal_date: "2026-06-10", date_state: "missing" },
  ],
  pendingDates: [{ item_ref: "synthetic-event-mh-01", domain: "mh", date_state: "missing" }],
  risks: [{ riskAnchorRef: "anchor-ae", severity: "high", riskType: "AE" }],
  events: [
    {
      eventRef: "synthetic-event-ae-01",
      domain: "ae",
      domainEncoding: domains[0],
      start: "2026-04-11",
      end: "2026-04-13",
      dateState: "exact",
      eventLabel: "头痛记录",
      riskAnchorRefs: ["anchor-ae"],
      sourceLocatorRefs: ["loc-ae"],
    },
    {
      eventRef: "synthetic-event-mh-01",
      domain: "mh",
      domainEncoding: domains[1],
      start: null,
      end: null,
      dateState: "missing",
      eventLabel: "既往病史后续记录",
      riskAnchorRefs: [],
      sourceLocatorRefs: ["loc-mh"],
    },
    {
      eventRef: "synthetic-event-ip-01",
      domain: "ip",
      domainEncoding: domains[2],
      start: "2026-01-12",
      end: "2026-04-01",
      dateState: "exact",
      eventLabel: "试验药给药",
      riskAnchorRefs: [],
      sourceLocatorRefs: ["loc-ip"],
    },
    {
      eventRef: "synthetic-event-lab-01",
      domain: "lab_exam",
      domainEncoding: domains[3],
      start: "2026-04-10",
      end: "2026-04-10",
      dateState: "exact",
      eventLabel: "实验室检查",
      riskAnchorRefs: [],
      sourceLocatorRefs: ["loc-lab"],
    },
    {
      eventRef: "synthetic-event-lab-02",
      domain: "lab_exam",
      domainEncoding: domains[3],
      start: "2026-04-10",
      end: "2026-04-10",
      dateState: "exact",
      eventLabel: "同日第二次实验室检查",
      riskAnchorRefs: [],
      sourceLocatorRefs: ["loc-lab-2"],
    },
  ],
};

// 结构断言用detailed密度：全部事件可见，逐lane几何可断言。
const layout = layoutJourneyTimeline({ ...baseLayoutInput, viewport: "fit", density: "detailed" });

assert.equal(layout.lanes.length, 8);
assert.equal(layout.visitMarks.length, 1);
assert.equal(layout.pendingVisits.length, 1);
assert.equal(layout.pendingEvents.length, 1);
assert.equal(layout.pendingEvents[0].eventRef, "synthetic-event-mh-01");
const aeLane = layout.lanes.find((lane) => lane.domain === "ae");
assert.equal(aeLane.marks[0].geometry, "interval");
assert.ok(aeLane.marks[0].width > 0);
assert.equal(aeLane.marks[0].severity, "high");
const labLane = layout.lanes.find((lane) => lane.domain === "lab_exam");
assert.equal(labLane.marks[0].geometry, "point");
const ipLane = layout.lanes.find((lane) => lane.domain === "ip");
assert.equal(ipLane.marks[0].geometry, "interval");
assert.ok(layout.visitMarks[0].x < aeLane.marks[0].x);

// --- W05-J1 A17：切换detailDensity，scale四值（startMs/endMs/pxPerDay/width）不变 ---
const densityScales = ["compact", "standard", "detailed"].map((density) => {
  const built = layoutJourneyTimeline({ ...baseLayoutInput, viewport: "fit", density, containerWidth: 500 });
  return built.scale;
});
for (let i = 1; i < densityScales.length; i += 1) {
  assert.equal(densityScales[i].startMs, densityScales[0].startMs, "density switch keeps scale.startMs");
  assert.equal(densityScales[i].endMs, densityScales[0].endMs, "density switch keeps scale.endMs");
  assert.equal(densityScales[i].pxPerDay, densityScales[0].pxPerDay, "density switch keeps scale.pxPerDay");
  assert.equal(densityScales[i].width, densityScales[0].width, "density switch keeps scale.width");
}

// --- 密度只改聚合阈值：compact聚合全部低风险，standard保留单点，detailed全可见 ---
function markCount(density) {
  const built = layoutJourneyTimeline({ ...baseLayoutInput, viewport: "fit", density });
  return built.lanes.reduce((sum, lane) => sum + lane.marks.length, 0);
}
function aggregateCount(density) {
  const built = layoutJourneyTimeline({ ...baseLayoutInput, viewport: "fit", density });
  return built.lanes.reduce((sum, lane) => sum + lane.aggregates.length, 0);
}
assert.ok(markCount("detailed") > markCount("standard"), "detailed density reveals singleton low-risk marks");
assert.ok(aggregateCount("compact") > aggregateCount("standard"), "compact density aggregates more low-risk marks");
// medium/high/critical任何密度都不聚合隐藏。
assert.ok(markCount("detailed") >= markCount("compact"), "priority marks are never aggregate-hidden");

// --- 视窗切换（fit↔custom）：成员不丢，事件总数只由密度决定 ---
const fitLayout = layoutJourneyTimeline({ ...baseLayoutInput, viewport: "fit", density: "standard", containerWidth: 500 });
const customLayout = layoutJourneyTimeline({ ...baseLayoutInput, viewport: "custom", timeZoom: 1, density: "standard" });
const membersOf = (built) => built.lanes
  .flatMap((lane) => [
    ...lane.marks.map((mark) => mark.eventRef),
    ...lane.aggregates.flatMap((aggregate) => aggregate.eventRefs),
  ])
  .sort();
assert.deepEqual(
  membersOf(fitLayout),
  membersOf(customLayout),
  "switching viewport never loses marks or aggregate members",
);
assert.equal(fitLayout.datedEventCount, customLayout.datedEventCount);
// 自选视窗画布按px/day扩展（宽于fit的容器宽）。
assert.ok(customLayout.scale.width > fitLayout.scale.width);

// --- 聚焦视窗：范围收窄但不丢成员 ---
const focusLayout = layoutJourneyTimeline({
  ...baseLayoutInput,
  viewport: "focus",
  density: "standard",
  focusWindow: { start: "2026-03-15", end: "2026-05-15" },
  containerWidth: 500,
});
assert.equal(focusLayout.scale.windowStartIso, "2026-03-15");
assert.deepEqual(membersOf(focusLayout), membersOf(fitLayout), "focus viewport keeps every member visible within its window");

// --- W05-J2 A21：聚合坐标恒为有限number，窗外不再出现'[object Object]px' ---
const beyondWindowInput = {
  ...baseLayoutInput,
  windowStart: "2026-06-01",
  windowEnd: "2026-07-31",
  viewport: "fit",
  density: "compact",
  containerWidth: 500,
};
const beyondLayout = layoutJourneyTimeline(beyondWindowInput);
for (const lane of beyondLayout.lanes) {
  for (const aggregate of lane.aggregates) {
    assert.equal(typeof aggregate.x, "number");
    assert.ok(Number.isFinite(aggregate.x), `aggregate x is a finite number: ${aggregate.x}`);
  }
  for (const mark of lane.marks) {
    assert.equal(typeof mark.x, "number");
    assert.ok(Number.isFinite(mark.x), `mark x is a finite number: ${mark.x}`);
  }
}
// 窗外事件被聚合/标记时携带before/after方向（不伪装同日）。
const beyondDirections = beyondLayout.lanes
  .flatMap((lane) => lane.marks.map((mark) => mark.beyond))
  .filter(Boolean);
assert.ok(beyondDirections.every((direction) => direction === "before" || direction === "after"));

// --- W05-J2 A22：区间end端越界标志 / ongoing与end_unknown开放条形 ---
const spanLayout = layoutJourneyTimeline({
  ...baseLayoutInput,
  windowStart: "2026-01-01",
  windowEnd: "2026-02-28",
  viewport: "fit",
  density: "detailed",
  containerWidth: 500,
});
const ipSpanLane = spanLayout.lanes.find((lane) => lane.domain === "ip");
const ipSpanMark = ipSpanLane.marks.find((mark) => mark.eventRef === "synthetic-event-ip-01");
assert.ok(ipSpanMark, "interval spanning the window end is still laid out");
assert.equal(ipSpanMark.beyondStart, null);
assert.equal(ipSpanMark.beyondEnd, "after", "interval end beyond the window keeps its own end-boundary flag");
assert.ok(ipSpanMark.width > 0);

const openEndInput = {
  ...baseLayoutInput,
  windowStart: "2026-01-01",
  windowEnd: "2026-08-20",
  viewport: "fit",
  density: "detailed",
  containerWidth: 500,
  events: [
    ...baseLayoutInput.events,
    {
      eventRef: "synthetic-event-cm-ongoing",
      domain: "cm",
      domainEncoding: domains[4],
      start: "2026-03-01",
      end: null,
      dateState: "exact",
      ongoing: true,
      eventLabel: "持续用药中",
      riskAnchorRefs: [],
      sourceLocatorRefs: ["loc-cm"],
    },
    {
      eventRef: "synthetic-event-cm-endunknown",
      domain: "cm",
      domainEncoding: domains[4],
      start: "2026-02-01",
      end: null,
      dateState: "exact",
      end_state: "unknown",
      eventLabel: "结束时间未知用药",
      riskAnchorRefs: [],
      sourceLocatorRefs: ["loc-cm-2"],
    },
  ],
};
const openEndLayout = layoutJourneyTimeline({ ...openEndInput, viewport: "fit", density: "detailed", containerWidth: 500 });
const cmLane = openEndLayout.lanes.find((lane) => lane.domain === "cm");
const ongoingMark = cmLane.marks.find((mark) => mark.eventRef === "synthetic-event-cm-ongoing");
const endUnknownMark = cmLane.marks.find((mark) => mark.eventRef === "synthetic-event-cm-endunknown");
assert.ok(ongoingMark && ongoingMark.width > 0, "ongoing renders as an open bar extending to the axis end");
assert.ok(endUnknownMark && endUnknownMark.width > 0, "end_unknown renders as an open bar extending to the axis end");

// --- W05-J2：月精度起点上轴为当月区间（宽度=当月天数×px/day） ---
const monthLayout = layoutJourneyTimeline({
  ...baseLayoutInput,
  viewport: "fit",
  density: "detailed",
  containerWidth: 500,
  events: [
    ...baseLayoutInput.events,
    {
      eventRef: "synthetic-event-cm-monthly",
      domain: "cm",
      domainEncoding: domains[4],
      start: "2026-03",
      end: null,
      dateState: "exact",
      eventLabel: "月精度给药记录",
      riskAnchorRefs: [],
      sourceLocatorRefs: ["loc-cm-3"],
    },
  ],
});
assert.equal(timelineDatePrecision("2026-03"), "month");
// J03合同：月精度不以01日为实际日——不落轴，进待确认集合单独列示。
const monthlyPending = monthLayout.pendingEvents.find(
  (event) => event.eventRef === "synthetic-event-cm-monthly",
);
assert.ok(monthlyPending, "month-precision event stays out of the dated axis");
assert.ok(!monthlyLaneMarks(monthLayout, "synthetic-event-cm-monthly"), "month-precision event renders no axis mark");

function monthlyLaneMarks(built, eventRef) {
  return built.lanes.some((lane) => lane.marks.some((mark) => mark.eventRef === eventRef));
}

// --- W05-J2 A23：全无有效日期→hasValidDates=false（渲染层据此隐藏月份
// 刻度与假窗文案，显示明确空态） ---
const undated = layoutJourneyTimeline({
  domains,
  events: [{ eventRef: "synthetic-event-mh-01", domain: "mh", domainEncoding: domains[1], start: null, end: null, dateState: "missing", eventLabel: "既往病史", riskAnchorRefs: [], sourceLocatorRefs: [] }],
  pendingDates: [{ item_ref: "synthetic-event-mh-01" }],
  viewport: "fit",
  density: "standard",
});
assert.equal(undated.scale.hasValidDates, false);
assert.equal(undated.pendingEventCount, 1);

console.log("medicalMonitoringJourneyTimeline: geometry checks passed");
