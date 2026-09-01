# Task Context: medical_monitoring_project_action_success_identity_20260803

## Objective

Require project identity on Overview inbox mark-read, source registration and
AI-run creation responses before success messaging or refresh.

## Source and scope

- Workbench `frontend/src/App.jsx` OverviewPage and PlannedModulePage action
  handlers.
- Existing backend contracts expose identity through the inbox/action result,
  nested source-registration entry and public AI-run result.
- In scope: success-response identity guards and visible Overview failure.
- Out of scope: backend/API changes, actions, source registration, provider
  execution, browser/API login, real projects, B6/C14, runtime and clinical
  conclusions.

## Success criteria

- Wrong or missing identity cannot refresh the current inbox or show a false
  success message.
- Overview action failure is visible and does not navigate away before the user
  can see the warning.
- Focused Python contracts, Node suites, Vite and Ruff pass.

## Risk boundary and route

No action, source-registration request or AI provider was called. Workflow
route is recorded only and not dispatched; direct Codex owns implementation and
acceptance.

## Final evidence

- Direct Codex added the Overview failure surface and three response identity
  guards.
- Focused Python/source set passed (153 passed, 17 existing warnings), all 22
  medical-monitoring Node suites passed, Vite build passed, and Ruff passed on
  changed contract files.
- No browser/runtime/live authority check was run because B6/C14 remain closed.

## Risk boundaries

- 8911 and 5174 remain stopped; B6 and C14 remain blocked and unchanged.
- This is not runtime, scientific, UAT or commercial acceptance.
