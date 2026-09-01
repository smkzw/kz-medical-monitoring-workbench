import assert from "node:assert/strict";
import {
  assignLaneStacks,
  buildTimelineScale,
  eventGeometry,
  eventIsPendingDate,
  layoutJourneyTimeline,
  parseTimelineDate,
  visitAxisDate,
} from "./medicalMonitoringJourneyTimeline.mjs";

assert.equal(parseTimelineDate("2026-04-11"), Date.UTC(2026, 3, 11));
assert.equal(parseTimelineDate("2026-04"), Date.UTC(2026, 3, 1));
assert.equal(parseTimelineDate(null), null);
assert.equal(parseTimelineDate("2026-02-31"), null);
assert.equal(visitAxisDate({ actual_date: "2026-01-10", nominal_date: "2026-01-09" }), "2026-01-10");
assert.equal(visitAxisDate({ actual_date: null, nominal_date: "2026-06-10", date_state: "missing" }), null);
assert.equal(eventIsPendingDate({ dateState: "missing", start: null }), true);
assert.equal(eventIsPendingDate({ dateState: "conflicted", start: "2026-04-10" }), true);
assert.equal(eventGeometry({ dateState: "exact", start: "2026-04-10", end: "2026-04-10" }), "point");
assert.equal(eventGeometry({ dateState: "exact", start: "2026-04-11", end: "2026-04-13" }), "interval");
assert.equal(eventGeometry({ dateState: "missing", start: null }), "pending");

const scale = buildTimelineScale({
  windowStart: "2026-01-01",
  windowEnd: "2026-08-20",
  visits: [{ actual_date: "2026-01-10", date_state: "exact" }],
  events: [{ dateState: "exact", start: "2026-04-11", end: "2026-04-13" }],
  zoomLevel: 0,
});
assert.ok(scale.width >= 640);
assert.ok(scale.xFor("2026-01-01") < scale.xFor("2026-04-11"));
assert.ok(scale.xFor("2026-04-11") < scale.xFor("2026-08-20"));

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

const layout = layoutJourneyTimeline({
  domains,
  windowStart: "2026-01-01",
  windowEnd: "2026-08-20",
  zoomLevel: 0,
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
  ],
});

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

console.log("medicalMonitoringJourneyTimeline: geometry checks passed");
