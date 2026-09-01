# Task Context: medical_monitoring_intake_post_response_identity_guard_20260803

Created: 2026-08-03 13:10:33
Objective: Reject a wrong-project monitoring intake POST response before committing intake result or generated-risk state.
Task type: `finite_code_task`
Risk: `high`
Selected agent route: `opencode-go` / `deepseek-v4-flash` / `max`

## Source Of Truth

- Workbench `frontend/src/App.jsx` `runMonitoringRules` POST response handling
  and `MonitoringIntakeResult.project_id` contract.

## Scope

- In scope: require the intake response project id to match the current
  canonical monitoring project before committing `intakeResult` or generated
  risk selection; add static regression and offline checks.
- Out of scope: executing intake, source confirmation, backend intake logic,
  writes, services, providers, browsers, real projects, B6/C14 and runtime.

## Success Criteria

- A wrong or missing intake response identity fails closed before state commit;
  valid canonical responses retain the existing result/risk behavior.
- Frontend monitoring contracts, Node suites, Vite and Ruff remain green.

## Risk Boundaries

- No intake execution/provider/browser/API login/real-project/runtime write; no
  B6/C14 authority or release claim.
- Route is recorded for audit only and will not be dispatched; direct Codex owns
  verification and acceptance.

## Timeout Policy

- Do not mark the delegated agent failed for slow response alone.
- For complex or artifact-heavy work, wait and poll generously; use conference mode when multiple independent model perspectives are needed.
- Failure requires terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.

## Loop Log

- 2026-08-03 13:10:33: Task initialized by `tools/hermes_workflow_guard.py init-task`.
- 2026-08-03 13:10:50: Direct Codex selected; no external route dispatched.
