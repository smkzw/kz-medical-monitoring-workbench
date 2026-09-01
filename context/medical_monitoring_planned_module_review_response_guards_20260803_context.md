# Task Context: medical_monitoring_planned_module_review_response_guards_20260803

Created: 2026-08-03 13:01:13
Objective: Reject stale or cross-project evidence, TFL and safety review-workbench responses before PlannedModulePage state commits.
Task type: `finite_code_task`
Risk: `high`
Selected agent route: `opencode-go` / `deepseek-v4-flash` / `max`

## Source Of Truth

- Workbench `frontend/src/App.jsx` `PlannedModulePage` read effects.
- Local API contracts for evidence-design, TFL and safety review workbenches,
  each of which exposes canonical `project_id`.

## Scope

- In scope: add one current canonical project ref and guards for evidence
  manifest, TFL manifest/review and safety review read commits; add static
  assertions.
- Out of scope: source registry response (no project id in current payload),
  backend/API contracts, review actions/writes, services, providers, browser
  login, real projects, B6/C14 and runtime.

## Success Criteria

- Stale or cross-project responses cannot enter the four review-workbench state
  surfaces; valid canonical responses remain accepted across project changes.
- Focused frontend contracts, Node suites, Vite and Ruff remain green.

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

- 2026-08-03 13:01:13: Task initialized by `tools/hermes_workflow_guard.py init-task`.
- 2026-08-03 13:01:30: Direct Codex selected; no external route dispatched.
