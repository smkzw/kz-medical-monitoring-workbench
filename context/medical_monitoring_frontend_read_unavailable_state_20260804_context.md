# Task Context: medical_monitoring_frontend_read_unavailable_state_20260804

Created: 2026-08-04 13:53:11
Objective: Prevent fail-closed medical-monitoring dashboard, inbox and AI-read failures from rendering as empty clinical data; add explicit unavailable-state UI without changing backend routes
Task type: `code_scoped_patch_plan`
Risk: `high`
Selected agent route: `codex` / `codex-main` / `high`

## Trigger Reason

This task was initialized through the Codex x Hermes complex-task entrypoint because it is expected to involve more than three execution steps, research/writing/report/code/report-visual work, or source-grounded verification.

## Source Of Truth

- `frontend/src/App.jsx`: dashboard, workbench-inbox, AI-run and subject/profile
  fetch state plus Overview/Monitoring rendering.
- `frontend/src/styles.css`: existing panel/gate/error visual contract.
- `services/api/app/main.py`: canonical/reference dashboard, inbox and AI GET
  routes intentionally fail closed with explicit policy/identity errors.
- `tests/test_monitoring_risk_index_api.py` and frontend static/QC contracts:
  backend no-principal behavior and current user-facing labels.
- The preceding exact read-action contract slice, which is not yet wired to
  HTTP routes.

## Scope

- In scope: preserve structured API error code/status in the frontend, map
  monitoring identity/policy failures to explicit Chinese unavailable-state
  messages, prevent dashboard/inbox/AI/subject reads from silently becoming
  zero/empty clinical data, and add focused source/behavior assertions.
- In scope: minimal panel styling using the current visual language; preserve
  user-created medical-writing flows and successful monitoring responses.
- Out of scope: backend route activation, authentication middleware, API or
  browser login, service/provider startup, runtime DB, real projects, B6/C14,
  source admission, AI execution, or Playwright UAT.

## Success Criteria

- A 403/503 policy or principal failure is rendered as unavailable with a
  reason and no misleading empty count/list.
- Successful payloads still render unchanged; project/response identity checks
  remain fail-closed.
- Frontend build and focused monitoring/static checks pass; no reserved port is
  started; review-gate is green.

## Risk Boundaries

- Do not write to production paths until Codex review gate passes and writable paths are explicit.
- The delegated agent is not final authority; Codex owns verification and acceptance.

## Timeout Policy

- Do not mark the delegated agent failed for slow response alone.
- For complex or artifact-heavy work, wait and poll generously; use conference mode when multiple independent model perspectives are needed.
- Failure requires terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.

## Loop Log

- 2026-08-04 13:53:11: Task initialized by `tools/hermes_workflow_guard.py init-task`.
- 2026-08-04: Audit found dashboard/inbox/AI/subject catches reset state to empty or silently ignore errors. That is unsafe for a data-sensitive medical monitor when backend correctly fails closed. The patch will change only UI error-state rendering and error-code preservation.
- 2026-08-04: Implemented explicit unavailable-state UI, structured error-code propagation, client-side response project-identity blocking, monitoring-route inbox isolation, and `—` metrics for project loading/failure. Added a pure static contract test. Build and 31 pure medical-monitoring test files pass; reserved ports remain stopped.
- 2026-08-04: Skeptical review found a conditional-Hook risk from the dashboard unavailable early return; moved `OverviewPage` action state before the branch, added a static assertion, and reran the static test plus production build successfully.
- 2026-08-04: Further review separated monitoring inbox, subject-catalog and subject-profile errors so unrelated success responses cannot clear an unresolved failure; removed monitoring-page fallback to the active-project inbox and labeled client contract mismatches accurately. Static test, 31 pure monitoring test files and build all passed again.
