# Task Context: medical_monitoring_app_dashboard_inbox_identity_guards_20260803

Created: 2026-08-03 12:58:03
Objective: Reject cross-project dashboard and workbench-inbox read responses before App state commits, including refreshDashboard.
Task type: `finite_code_task`
Risk: `high`
Selected agent route: `opencode-go` / `deepseek-v4-flash` / `max`

## Source Of Truth

- Workbench `frontend/src/App.jsx` App dashboard, refreshDashboard, workbench
  inbox and monitoring inbox reads.
- `services/api/app/main.py` and contracts establish dashboard identity under
  `data.project.project_id` and inbox identity under top-level `project_id`.

## Scope

- In scope: add canonical project guards before dashboard and inbox state
  commits, including the refreshDashboard callback, and add static assertions.
- Out of scope: backend/API contracts, source manifests, route aliases,
  service/provider/browser/API login, real projects, writes, B6/C14 and runtime.

## Success Criteria

- Wrong or missing project identities cannot update dashboard or either inbox
  state; valid canonical responses remain accepted.
- Focused frontend/project contracts, Node suites, Vite and Ruff remain green.

## Risk Boundaries

- No services, providers, browsers, API login, real projects or runtime writes;
  no B6/C14 authority or release claim.
- Route is recorded for audit only and will not be dispatched; direct Codex owns
  verification and acceptance.

## Timeout Policy

- Do not mark the delegated agent failed for slow response alone.
- For complex or artifact-heavy work, wait and poll generously; use conference mode when multiple independent model perspectives are needed.
- Failure requires terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.

## Loop Log

- 2026-08-03 12:58:03: Task initialized by `tools/hermes_workflow_guard.py init-task`.
- 2026-08-03 12:58:20: Direct Codex selected; no external route dispatched.
