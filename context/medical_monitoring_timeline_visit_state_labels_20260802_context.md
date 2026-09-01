# Task Context: medical_monitoring_timeline_visit_state_labels_20260802

Created: 2026-08-02 10:02:43
Objective: Distinguish actual-dated visit anchors from planned-only and unscheduled anchors in Subject Timeline context without inferring completed visits
Task type: `code_scoped_patch_plan`
Risk: `medium`
Selected agent route: `codex` / `codex-main` / `high`

## Trigger Reason

This task was initialized through the Codex x Hermes complex-task entrypoint because it is expected to involve more than three execution steps, research/writing/report/code/report-visual work, or source-grounded verification.

## Source Of Truth

- `frontend/src/features/medical-monitoring/MedicalMonitoringSubjectViews.jsx`:
  `SubjectTimelinePage` context summary currently labels every returned visit
  anchor as an actual visit.
- `frontend/src/features/medical-monitoring/medicalMonitoringSubjectModels.mjs`:
  `plannedVisitAxis()` preserves `date`, `plannedDay`, and `isUnscheduled`, so a
  planned-only anchor is distinguishable without guessing an actual date.
- `tests/test_frontend_timeline_contract.py` and the existing Node subject-model
  tests: current Timeline contracts and planned/actual fixture behavior.
- Frontend `AGENTS.md` Subject Timeline contract: visit-axis based, source-
  grounded, compact, and no semantic conflation of event categories.

Pre-edit source hashes:

```text
6cb55fad653b112d700e4249db787c4e0b177d1bfe2bab409f1597472b29998f  frontend/src/features/medical-monitoring/MedicalMonitoringSubjectViews.jsx
a6576ce85dd7cee30d505627777f773f9995291541bb6f934adc6dc6b8e5abea  tests/test_frontend_timeline_contract.py
```

## Scope

- In scope: distinguish actual-dated anchors, planned-only anchors, and
  unscheduled anchors in the Timeline context summary; add a static contract
  regression; preserve existing axis rendering and event data.
- Out of scope: protocol/listing mapping, date calculation, backend/API,
  runtime, browser, `App.jsx`, `styles.css`, B6/C13/C14, real projects, and the
  parallel medical-writing lane.

## Success Criteria

- The summary never calls a planned-only anchor an actual visit.
- Actual dates, planned-only count, and unscheduled count remain explicit and
  compact; no date or completion state is inferred.
- Existing frontend contracts, subject-model Node tests, and production build
  pass.

## Risk Boundaries

- Do not edit `frontend/src/App.jsx` or `frontend/src/styles.css`.
- Do not start 8911/5174, services, providers, browser, or real projects; do
  not touch SQLite, B6/C13/C14, or medical-writing files.
- Do not compute an actual date from a planned day in this presentation-only
  slice; the source contract already distinguishes `date` and `plannedDay`.
- Codex owns verification and acceptance.

## Timeout Policy

- Do not mark the delegated agent failed for slow response alone.
- For complex or artifact-heavy work, wait and poll generously; use conference mode when multiple independent model perspectives are needed.
- Failure requires terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.

## Loop Log

- 2026-08-02 10:02:43: Task initialized by `tools/hermes_workflow_guard.py init-task`.
- 2026-08-02 10:05 CST: Added presentation-only counts for actual-dated,
  planned-only, and unscheduled visit anchors; added a static regression. No
  date or completion state is inferred.
- 2026-08-02 10:05 CST: Timeline Python contract 18 passed; adjacent Python
  frontend contracts 44 passed; all 22 medical-monitoring Node test files
  passed; Vite 1925 modules transformed and build succeeded. Review-gate
  returned `ok:true` with no warnings/errors.
- 2026-08-02 10:06 CST: Accepted the slice. B6/C13/C14 and runtime boundary
  remain unchanged; 8911/5174 remain stopped. Next safe action is still formal
  B6 outcome followed by aggregate/CAS/source-token revalidation.
