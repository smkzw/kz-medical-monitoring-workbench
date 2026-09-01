# Task Context: medical_monitoring_subject_view_readiness_gate_20260804

Created: 2026-08-04 21:39:49
Objective: Ensure subject Timeline/Profile deep links fail closed when the project medical-monitoring source is not execution-ready; preserve loading behavior for active project profiles and protect medical-writing.
Task type: `code_scoped_patch_plan`
Risk: `high`
Selected agent route: `codex` / `codex-main` / `high`

## Trigger Reason

This task was initialized through the Codex x Hermes complex-task entrypoint because it is expected to involve more than three execution steps, research/writing/report/code/report-visual work, or source-grounded verification.

## Source Of Truth

- `frontend/src/App.jsx` project readiness derivation and subject Timeline/Profile
  page dispatch.
- `frontend/src/features/medical-monitoring/medicalMonitoringSourceReadiness.mjs`
  readiness semantics: `source_manifest_only` is non-readable and
  non-executable; `real_source_slice` is active.
- Existing frontend monitoring/timeline contracts and current closed B6/C14
  gate artifacts.

## Scope

- In scope: add a readiness guard before the active subject Timeline/Profile
  feature components so non-executable source bindings return the existing
  unavailable boundary.
- Out of scope: changing readiness statuses, profile loading for active
  projects, subject models, API/backend behavior, runtime/provider/browser/
  Playwright, real projects, SQLite or medical-writing code.

## Success Criteria

- A source-only or unconfirmed project cannot render subject Timeline/Profile
  components through a deep link.
- Active projects retain current feature components and loading behavior.
- Focused/adjacent frontend contracts, monitoring Node contracts, Vite build,
  port checks and review-gate pass.

## Risk Boundaries

- Do not write to production paths until Codex review gate passes and writable paths are explicit.
- The delegated agent is not final authority; Codex owns verification and acceptance.
- This guard does not grant execution or medical authority; it only consumes the
  existing readiness decision.

## Timeout Policy

- Do not mark the delegated agent failed for slow response alone.
- For complex or artifact-heavy work, wait and poll generously; use conference mode when multiple independent model perspectives are needed.
- Failure requires terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.

## Loop Log

- 2026-08-04 21:39:49: Task initialized by `tools/hermes_workflow_guard.py init-task`.
- 2026-08-04 21:40–21:43: Added readiness checks before both subject-view
  branches. Frontend contracts passed 73, all 32 monitoring Node contracts
  passed, Vite build passed, reserved ports remained empty, and review-gate
  returned `ok=true` with no warnings/errors.
