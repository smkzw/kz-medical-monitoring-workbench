# Task Context: medical_monitoring_timeline_event_inspector_20260806

Created: 2026-08-06 05:24:26
Objective: Make Subject Timeline event blocks keyboard/click reachable with an explicit raw-event inspector while preserving source-bound and risk-context semantics
Task type: `code_scoped_patch_plan`
Risk: `medium`
Selected agent route: `codex` / `codex-main` / `high`

## Trigger Reason

This task was initialized through the Codex x Hermes complex-task entrypoint because it is expected to involve more than three execution steps, research/writing/report/code/report-visual work, or source-grounded verification.

## Source Of Truth

- `docs/medical_monitoring_manual/医学监查子系统_PRD审阅与差距矩阵.md:69-83`
  and `:133-138` define the Timeline/Patient Profile interaction and P1-01
  density/positioning expectation.
- `frontend/src/features/medical-monitoring/MedicalMonitoringSubjectViews.jsx`
  is the production Subject Timeline SVG and detail workspace.
- `frontend/src/features/medical-monitoring/medicalMonitoringSubjectModels.mjs`
  supplies explicit event category, source locator, risk IDs and timeline
  coverage semantics.
- `records/active_slices/medical_monitoring_real_loop_gate_audit_20260804/CURRENT_REAL_LOOP_GATE_AUDIT.json`
  is the runtime authority source: `read_only / blocked`, all activation,
  provider and write flags false.

## Scope

- In scope: click/keyboard selection of dated Subject Timeline event blocks,
  explicit event fact/source/risk inspector, selected-state styling, focused
  static contract and derived build output/evidence records.
- Out of scope: backend/API/event semantics, source ingestion, medical risk
  confirmation, P8/B6/C14, Safety/PV, App ownership migration,
  medical-writing assets, providers, services, browser/Playwright sessions,
  real projects, runtime/SQLite/CAS writes and ports.

## Success Criteria

- Event blocks remain positioned by actual date and lane; selecting one does
  not filter away the other event context.
- Click/Enter/Space on a dated event opens a compact inspector containing
  explicit event fact, date/visit, severity/relationship/outcome,
  source body, source locator and related risk IDs.
- Missing source/risk fields remain explicit unknowns and never become a
  no-risk or source-validity conclusion.
- Focused/static/full frontend tests, build, review-gate and reserved-port
  checks pass without runtime activation.

## Risk Boundaries

- Do not write to production paths until Codex review gate passes and writable paths are explicit.
- The delegated agent is not final authority; Codex owns verification and acceptance.
- This is direct Codex work; no delegated agent or provider session is used.
- No live browser or runtime acceptance is claimed under the blocked gate.

## Timeout Policy

- Do not mark the delegated agent failed for slow response alone.
- For complex or artifact-heavy work, wait and poll generously; use conference mode when multiple independent model perspectives are needed.
- Failure requires terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.

## Loop Log

- 2026-08-06 05:24:26: Task initialized by `tools/hermes_workflow_guard.py init-task`.
- 2026-08-06: Reviewed the current SVG implementation: event blocks had only
  hover `<title>` and lower detail rows; no direct visual event selection path.
