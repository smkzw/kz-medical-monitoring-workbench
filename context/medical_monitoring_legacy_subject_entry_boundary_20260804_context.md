# Task Context: medical_monitoring_legacy_subject_entry_boundary_20260804

Created: 2026-08-04 21:36:44
Objective: Prove active monitoring subject routes use the project-bound MedicalMonitoringSubjectViews components and never re-enter legacy App.jsx subject pages; preserve compatibility-only legacy definitions.
Task type: `code_scoped_patch_plan`
Risk: `high`
Selected agent route: `codex` / `codex-main` / `high`

## Trigger Reason

This task was initialized through the Codex x Hermes complex-task entrypoint because it is expected to involve more than three execution steps, research/writing/report/code/report-visual work, or source-grounded verification.

## Source Of Truth

- `frontend/src/App.jsx` active-page dispatch and retained compatibility-only
  legacy subject-page definitions.
- `frontend/src/features/medical-monitoring/MedicalMonitoringSubjectViews.jsx`
  project-bound Timeline/Profile components and the existing frontend timeline
  contracts.
- Current B6/C14/approved-input/host-identity gates remain closed; this slice
  is source/test-only.

## Scope

- In scope: add a static contract proving active subject routes render
  `MedicalMonitoringSubjectTimelinePage` and
  `MedicalMonitoringPatientProfilePage`, with no JSX entry for the retained
  legacy pages.
- Out of scope: deleting or rewriting legacy compatibility definitions,
  changing subject models, API/backend behavior, runtime/browser/provider/
  Playwright, real projects, SQLite, or medical-writing code.

## Success Criteria

- The new contract distinguishes active project-bound routes from legacy
  definitions and passes focused, adjacent, Node and build regression.
- No reserved port listens and Hermes review-gate is `ok=true` with no
  warnings/errors.

## Risk Boundaries

- Do not write to production paths until Codex review gate passes and writable paths are explicit.
- The delegated agent is not final authority; Codex owns verification and acceptance.
- No test result from this slice grants runtime or medical approval authority.

## Timeout Policy

- Do not mark the delegated agent failed for slow response alone.
- For complex or artifact-heavy work, wait and poll generously; use conference mode when multiple independent model perspectives are needed.
- Failure requires terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.

## Loop Log

- 2026-08-04 21:36:44: Task initialized by `tools/hermes_workflow_guard.py init-task`.
- 2026-08-04 21:37–21:40: Added the static active-route boundary. Focused and
  adjacent frontend contracts passed 72, all 32 monitoring Node contracts
  passed, Vite build passed, reserved ports remained empty, and review-gate
  returned `ok=true` with no warnings/errors.
