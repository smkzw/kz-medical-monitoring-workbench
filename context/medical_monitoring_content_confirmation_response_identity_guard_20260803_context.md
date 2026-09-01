# Task Context: medical_monitoring_content_confirmation_response_identity_guard_20260803

Created: 2026-08-03 13:13:33
Objective: Reject a wrong-project source content-confirmation response before committing confirmed medical-review state.
Task type: `finite_code_task`
Risk: `high`
Selected agent route: `opencode-go` / `deepseek-v4-flash` / `max`

## Source Of Truth

- Workbench `frontend/src/App.jsx` `submitContentConfirmation` and the public
  `_public_source_validation` contract, which includes canonical `project_id`.

## Scope

- In scope: require confirmation response identity before committing
  `confirmedRecord` or retrying monitoring rules; add static regression and
  offline checks.
- Out of scope: executing confirmation, source validation storage, intake,
  services, providers, browsers, real projects, B6/C14 and runtime.

## Success Criteria

- A wrong or missing confirmation response identity fails closed before the
  UI records medical confirmation state or retries rules; valid canonical
  responses preserve current behavior.
- Monitoring contracts, Node suites, Vite and Ruff remain green.

## Risk Boundaries

- No confirmation/intake execution, provider, browser, API login, real-project
  or runtime write; no B6/C14 authority or release claim.
- Route is recorded for audit only and will not be dispatched; direct Codex owns
  verification and acceptance.

## Timeout Policy

- Do not mark the delegated agent failed for slow response alone.
- For complex or artifact-heavy work, wait and poll generously; use conference mode when multiple independent model perspectives are needed.
- Failure requires terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.

## Loop Log

- 2026-08-03 13:13:33: Task initialized by `tools/hermes_workflow_guard.py init-task`.
- 2026-08-03 13:13:50: Direct Codex selected; no external route dispatched.
