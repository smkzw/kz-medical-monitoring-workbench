# RUX Timeline Dose-Adjustment Frontend Review Packet - 2026-07-08

## Purpose

Review the minimal frontend design and implementation for the new backend event type:

```text
SubjectTimelineEventType.DOSE_ADJUSTMENT = "dose_adjustment"
```

Current backend accepted behavior:

- RUX ECB `暂停用药` / `重新用药` events now use `dose_adjustment`, not `protocol_deviation`.
- RUX P0 backend is accepted only for verified medical-monitoring anchors.
- RUX frontend/browser surface is not accepted yet.

Hermes participants must not edit source files. Codex will write tests, patch, build, and run browser/QC.

## Existing Product And Visual Contract

From `frontend/AGENTS.md`:

- Subject Timeline must use the existing MG-K10 reference as visual source of truth.
- Timeline is visit-axis based.
- Events are positioned below the axis by study day/date.
- Long event text must not be rendered inside timeline lanes.
- Use compact numbered blocks on the graph, stable lane numbering, hover details, and numbered detail rows below.
- Dense clinical review should show AE, concomitant medication/treatment, medical history, lab/efficacy, and PD/Query events if available.
- Page body must not overflow horizontally; dense internal timeline scrolling is acceptable on narrow screens.

## External Research Summary

See `research/rux_timeline_dose_adjustment_interaction_research_20260708.md`.

The commercial/open-source pattern is:

- patient/subject profiles combine AE, concomitant medications, treatment exposure/dose, lab/vitals, medical history, and visit context;
- dose changes are safety-relevant and should be visible near treatment/exposure, not hidden in lab/efficacy;
- dose adjustment is not automatically a protocol deviation;
- detail text should remain in hover/details, not in dense timeline lane blocks.

## Current Frontend Code Excerpts

Current lane definitions in `frontend/src/App.jsx`:

```jsx
const timelineLaneDefs = [
  { key: "AE", label: "AE", types: ["adverse_event"] },
  { key: "CM", label: "合并用药/治疗", types: ["concomitant_medication"] },
  { key: "MH", label: "病史", types: ["medical_history"] },
  { key: "LAB", label: "实验室/疗效", types: ["lab", "efficacy_score"] },
  { key: "PD_QUERY", label: "PD / Query", types: ["protocol_deviation", "query"] },
];
```

Current event tone:

```jsx
function eventTone(event) {
  if (event.related_risk_ids?.length || ["protocol_deviation", "query"].includes(event.event_type)) return "critical";
  if (event.event_type === "lab" && event.clinical_interpretation) return "warning";
  if (event.event_type === "efficacy_score") return "good";
  if (event.event_type === "medical_history") return "source";
  return "normal";
}
```

Current lane fallback:

```jsx
function laneForEvent(event) {
  return timelineLaneDefs.find((lane) => lane.types.includes(event.event_type))?.key || "LAB";
}
```

Current short labels:

```jsx
function shortTimelineEventLabel(event, laneIndex) {
  const prefix = {
    adverse_event: "AE",
    concomitant_medication: "CM",
    medical_history: "MH",
    lab: "LB",
    efficacy_score: "QS",
    protocol_deviation: "PD",
    query: "Q",
  }[event.event_type] || event.source_domain || "E";
  return `${prefix}${laneIndex + 1}`;
}
```

Current Patient Profile only groups PD/Query explicitly:

```jsx
const pdQueryEvents = relatedTimelineEvents(events, ["protocol_deviation", "query"]);
```

## User Correction Superseding Earlier Candidate

After the first Kimi/DeepSeek advisory outputs, the user corrected the core boundary:

```text
dose_adjustment以及其他试验药物的变更要单列！CM指的是非试验用药！边界要清楚
```

Codex accepts this as the product/domain decision. Any recommendation that places `dose_adjustment` inside the CM lane is superseded. CM must remain reserved for non-investigational concomitant medications/treatments.

## Known Defect

Because `dose_adjustment` is missing from `timelineLaneDefs` and `shortTimelineEventLabel()`:

- it falls into `LAB` through fallback;
- its block prefix becomes source domain or `E`;
- reviewers could confuse protocol-aligned dose management with lab/efficacy findings.

## Decision Questions

1. What should the independent trial-drug lane label be: `试验药物变更`, `试验药物/给药调整`, or another concise clinical label?
2. Should lane key/prefix use `IP` for investigational product lane and `DA` for dose adjustment event blocks?
3. What compact event prefix should be used for `dose_adjustment`: `DA`, `IP`, `给药`, or another option?
4. Should dose adjustment be `normal`, `warning`, or `critical` by default?
5. Should Patient Profile add a separate "给药调整" section now, or should this wait until broader RUX frontend wiring?

## Codex Updated Bias To Review

For this narrow slice, Codex's initial minimal candidate is:

- add a separate `IP` lane for trial-drug/investigational-product changes;
- keep the existing `CM` lane label and semantics for non-investigational concomitant medications/treatments;
- set independent lane label to `试验药物变更` unless Chinese reviewers recommend a better concise label;
- use compact prefix `DA`;
- keep default tone `normal`, while linked risk prompts still become `critical` through existing `related_risk_ids` logic;
- do not add a new Patient Profile section yet; only avoid misrouting in Subject Timeline and keep source/detail rows intact.

## Required Output

Return:

- accepted/rejected decision for each question;
- clinical/Chinese wording comments;
- minimal code/test plan;
- risks that should stay deferred;
- any visible QC checks Codex must run.
