# Task Context: medical_monitoring_app_ai_runs_identity_guard_20260803

Created: 2026-08-03 13:07:43
Objective: Reject stale or cross-project AI-run list responses before App state commits.
Task type: `finite_code_task`
Risk: `high`
Selected agent route: `opencode-go` / `deepseek-v4-flash` / `max`

## Source Of Truth

- Workbench `frontend/src/App.jsx` App AI-run list effect and the
  `public_ai_run`/`/api/projects/{project_id}/ai-runs` contract.

## Scope

- In scope: require every listed AI run to carry the current canonical project
  identity before `setAiRuns`, add a static assertion and focused API check.
- Out of scope: AI execution/provider behavior, run writes, artifacts, backend
  storage, services, browsers, real projects, B6/C14 and runtime.

## Success Criteria

- A stale, cross-project or malformed AI-run list cannot populate App state;
  valid empty and canonical lists remain accepted.
- AI execution/API, frontend contracts, Node suites, Vite and Ruff remain green.

## Risk Boundaries

- No service/provider/browser/API login/real-project/runtime write; no B6/C14
  authority or release claim.
- Route is recorded for audit only and will not be dispatched; direct Codex owns
  verification and acceptance.

## Timeout Policy

- Do not mark the delegated agent failed for slow response alone.
- For complex or artifact-heavy work, wait and poll generously; use conference mode when multiple independent model perspectives are needed.
- Failure requires terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.

## Loop Log

- 2026-08-03 13:07:43: Task initialized by `tools/hermes_workflow_guard.py init-task`.
- 2026-08-03 13:08:00: Direct Codex selected; no external route dispatched.
