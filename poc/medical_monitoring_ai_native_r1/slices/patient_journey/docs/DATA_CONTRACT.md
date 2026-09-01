# Slice 4 Patient Journey — Data Contract

## Purpose

`data/journey_fixture.js` exposes a classic-script payload for the isolated
R1 Patient Journey slice:

```text
window.MM_R1_JOURNEY = {...};
```

The payload is meant to load under `file://` with no `fetch`, no CDN, and no
server. It supplements the accepted Slice 3 `window.MM_R1_DATA` script as a
**read-only** identity/evidence reference. This slice must not copy or edit
Slice 3 files.

Journey rendering consumes contract fields generically. Visit/phase schedule
lives in data as schedule/knowledge anchors; production study semantics are
not hard-coded into the renderer.

## Authorized files (worker 01)

| Path | Role |
|---|---|
| `data/journey_fixture.js` | Synthetic classic script (`window.MM_R1_JOURNEY`) |
| `tests/test_data_contract.py` | Schema / ordering / binding / invariant tests |
| `docs/DATA_CONTRACT.md` | This note |

Slice 3 under `poc/.../slices/aemh_audience_workbench/` remains **read-only**.

## Schema identity

- `schema_version`: `patient_journey_r1_slice4_v1`
- `fixture_marker`: `SYNTHETIC`
- `synthetic_only`: `true`
- Default subject: `SYNTHETIC-SUBJECT-001`
- Shared spine: `spine:SYNTHETIC-RUN-N1:SYNTHETIC-SUBJECT-001`
  (byte-identical identity to Slice 3 Profile/Timeline for the same subject)

## Payload surface

Minimum top-level keys:

- `schema_version` / `fixture_marker` / `synthetic_only` / `disclaimer` / `ai_boundary`
- `project_id` / `run_id` / `snapshot_id` / `snapshot_version`
- `default_subject_id` / `spine_id`
- `shared_view_state` — single selection/window state shared by 旅程总览 /
  指标趋势 / 事件明细 / 风险证据
- `study_schedule` — planned visit/phase **schedule knowledge anchors**
  (`record_kind = schedule_knowledge_anchor`, `is_clinical_fact = false`)
- `subject_journey` — subject projection for the default subject
- `slice3_reference` — pointer to `window.MM_R1_DATA` (not inlined)

### `shared_view_state`

Unique expression of the journey shell state:

`project_id + run_id + snapshot_id + subject_id + spine_id + axis_mode + window_start + window_end + selected_event_id + selected_risk_id`

Default `axis_mode` is `actual_date`. Study day is a derived label on the same
event, not a second authoritative calendar.

### `study_schedule`

Contains:

- `phases[]` — ordered phase bands with `phase_id`, `label_zh`, `start_date`,
  `end_date`, `order`
- `planned_visits[]` — nominal/planned visit anchors with `visit_id`,
  `visit_type = planned`, `nominal_date`, optional `window_start` /
  `window_end`, `phase_id`, `label_zh`

Every schedule record must declare:

- `record_kind: "schedule_knowledge_anchor"`
- `is_clinical_fact: false`
- `fixture_marker: "SYNTHETIC"`

These rows are **not** formal AE/MH facts and must not enter reported-fact
counts.

### `subject_journey`

Minimum keys:

- `subject_id` / `spine_id` / `site_id` / `run_id`
- `temporal_spine` — `{ spine_id, run_id, subject_id, events[] }` with
  actual dates, derived `study_day`, optional `visit_label` / `phase_id`,
  and `source_refs`
- `phase_bands[]` — subject-visible phase intervals aligned to the actual-date
  axis
- `visits[]` — mixed `planned` / `actual` / `unscheduled` visit anchors
- `events[]` — point, closed-interval, open-ended-interval, and pending-date
  cases; producers should provide `clinical_domain`
- `facts[]` — formal AE/MH facts (`record_class = formal_fact`)
- `candidates[]` — under-reporting / risk candidates (`record_class = candidate`)
- `risks[]` — established risks (`record_class = established_risk`)
- `queries[]` — Query drafts bound by `risk_identity_keys`
- `evidence_locators[]` — synthetic source locators used by events/risks/queries

## Visit types

| `visit_type` | Meaning |
|---|---|
| `planned` | Nominal/protocol schedule anchor (knowledge). May lack an actual date. |
| `actual` | Observed visit occurrence on the actual-date axis. |
| `unscheduled` | Real-date visit not on the planned schedule; enters the subject axis by actual date. |

Planned-only anchors must not invent clinical occurrence. Actual and
unscheduled visits require `actual_date`.

## Event geometry

| `geometry` | Required fields | Notes |
|---|---|---|
| `point` | `actual_date` | Single-day marker |
| `interval` | `start_date`, `end_date` | Closed interval; `end_date >= start_date` |
| `interval_open` | `start_date`, `end_date = null`, `open_ended = true` | Open-ended; must not fake a precise end |
| `pending` | `date_status` in `{missing, partial, conflicted}`, no forced axis date | Lives on the pending-date surface |

Pending events keep `placement = "pending_date_surface"` and must not be
force-snapped onto the continuous axis.

## Record classes and marker semantics

| `record_class` | Marker contract | Formal AE/MH? |
|---|---|---|
| `formal_fact` | `shape = fact`, `line_style = solid` | yes (`is_formal_ae_mh_fact = true`) |
| `candidate` | `shape = candidate`, `line_style = dashed` | no |
| `established_risk` | `shape = established_risk` (diamond in UI) | no |

Candidates and established risks never inflate reported AE/MH counts.
`candidate_not_counted_as_reported` remains `true` for non-fact classes.

`record_class` is an internal state/evidence distinction, not an audience legend.
The UI must never collapse all source records into “已记录事项” or all risks into
“风险提示”.

## Clinical-domain display contract

Events and risks are primarily distinguished by their medical-monitoring domain:

| `clinical_domain` | Audience label | Event marker |
|---|---|---|
| `ae` | AE | circle + `AE` |
| `mh` | MH | square + `MH` |
| `cm` | CM/合并用药 | capsule + `CM` |
| `ip` | IP给药 | hexagon + `IP` |
| `lab` | 实验室/检查（含生命体征、ECG） | triangle + `检` |
| `hospitalization` | 住院/操作 | cross + `住` |
| `symptom` | 症状/体征线索 | dashed circle + `症` |

Risk markers retain the same domain code/color, use a diamond to distinguish a
risk from a source event, and add a visible high/medium/low label. Thus domain,
event-vs-risk and severity are not encoded by color alone.

For this v1 synthetic fixture, the projection may derive `clinical_domain` from
the standardized `event_type`/`risk_type` when the explicit field is absent.
Subsequent producers must emit `clinical_domain`; unknown values fail to `other`
rather than being silently classified as AE/MH/CM/IP.

## Risk and Query binding

Each established risk must declare:

- stable `risk_id` / `identity_key`
- `anchor_event_id` pointing at a dated journey event
- `severity` with at least one `medium` or higher case in the fixture
- `evidence_refs[]` using synthetic locators
- `query_ids[]` when a Query draft exists

Each Query must declare:

- `query_id`
- `risk_identity_keys[]` overlapping the bound risk identity
- evidence refs that intersect the risk evidence set

Consumers must not guess Query binding from `subject_id` alone.

## Evidence locators

- Prefer existing Slice 3 locators when the clinical/listing row truly exists
  (prefix `SYNTHETIC|snapshot=...|table=...|row=...`).
- New journey-only schedule or interval scaffolding uses
  `SYNTHETIC|journey=slice4|...` and remains conspicuously synthetic.
- No absolute filesystem paths.
- Audience UI must not expose raw locator strings as primary labels; the
  fixture still carries them for evidence drill-down tests.

## Same-spine semantics

For the default subject:

1. `subject_journey.spine_id` equals top-level `spine_id`.
2. `shared_view_state.spine_id` equals the same value.
3. `temporal_spine.spine_id` equals the same value.
4. The identity matches Slice 3 `temporal_spine_id` for
   `SYNTHETIC-SUBJECT-001`.

Profile/Timeline/Journey projections share this spine; they do not mint a
second subject-time identity.

## Determinism / offline guards

1. Fixture is a static classic script assignment ending with `;\n`.
2. No `fetch(`, no remote URL requirements, no absolute local paths.
3. All subject/record identifiers remain visibly `SYNTHETIC`.
4. Candidate IDs and formal fact IDs are disjoint.
5. Date-ordered collections (`phase_bands`, dated visits, dated events,
   temporal spine events) are sorted ascending by their axis date keys.
   Visit axis key is `nominal_date` for `planned` and `actual_date` for
   `actual` / `unscheduled`, with `order` as the stable tie-breaker.

## Verify

```bash
.venv/bin/python -m pytest -q \
  poc/medical_monitoring_ai_native_r1/slices/patient_journey/tests/test_data_contract.py
```
