# Task Context: medical_monitoring_action_response_identity_guards_20260803

## Objective

Require canonical project identity on MonitoringPage mark-read and medical-risk
disposition action responses before refreshing inbox/snapshot state or showing a
success message.

## Source and scope

- Workbench `frontend/src/App.jsx` `markRiskRead` and
  `applyRiskDisposition`; backend action contracts in `services/api/app/main.py`
  and `services/api/app/workbench_inbox.py` are read-only evidence.
- In scope: response identity guard, visible fail-closed action error and static
  regressions/offline checks.
- Out of scope: backend changes, action execution, writes, service/provider/
  browser/API login, real projects, B6/C14, clinical/scientific conclusions.

## Success criteria

- Missing or wrong `project_id` never triggers inbox/snapshot refresh or a
  success message; the user sees an explicit identity failure.
- Valid action responses retain existing refresh and status behavior.
- Focused contracts, Node suites, Vite and Ruff remain green.

## Risk boundary and route

No action endpoint or runtime was called. Workflow route is recorded for audit
only and not dispatched; direct Codex owns implementation and acceptance.

## Loop log

- 2026-08-03 13:29:39: `tools/hermes_workflow_guard.py init-task` completed.

Created: 2026-08-03 13:29:39
Objective: Require canonical project identity on MonitoringPage mark-read and risk-disposition action responses before refresh or success state, with visible fail-closed UX and offline regression evidence
Task type: `finite_code_task`
Risk: `high`
Selected agent route: `opencode-go` / `deepseek-v4-flash` / `max`

## Trigger Reason

This task was initialized through the Codex x Hermes complex-task entrypoint because it is expected to involve more than three execution steps, research/writing/report/code/report-visual work, or source-grounded verification.

## Source Of Truth

- Workbench `frontend/src/App.jsx` MonitoringPage action handlers and the
  existing action response contracts in `services/api/app/main.py` and
  `services/api/app/workbench_inbox.py`.
- No production, service, provider, browser or runtime path was opened.

## Scope

- In scope: canonical response identity checks, visible fail-closed action
  errors, static regressions and offline checks.
- Out of scope: backend changes, action execution, writes, service/provider/
  browser/API login, real projects, B6/C14 and clinical/scientific conclusions.

## Success Criteria

- Missing or wrong response `project_id` must block refresh and success state;
  valid responses must retain existing behavior.

## Risk Boundaries

- No action endpoint or runtime write; route recorded only and not dispatched.
- Codex is final authority and owns verification and acceptance.

## Timeout Policy

- Do not mark the delegated agent failed for slow response alone.
- For complex or artifact-heavy work, wait and poll generously; use conference mode when multiple independent model perspectives are needed.
- Failure requires terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.

## Loop Log

- 2026-08-03 13:29:39: Task initialized by `tools/hermes_workflow_guard.py init-task`.
- 2026-08-03 13:32:05: Both action handlers now reject missing or mismatched
  response identity before inbox/snapshot refresh or success messaging.
- 2026-08-03 13:33:20: Final focused Python set passed (115 passed, 17 existing
  warnings); Node 22 suites, Vite, focused Ruff, workbench inbox/disposition
  tests (28 passed) passed. No action endpoint, provider, browser or runtime
  route was opened.
