# Task Context: medical_monitoring_source_registry_project_identity_contract_20260803

Created: 2026-08-03 13:04:07
Objective: Expose canonical project_id in the source-registry read contract and reject stale source-ledger responses before state commit.
Task type: `finite_code_task`
Risk: `high`
Selected agent route: `opencode-go` / `deepseek-v4-flash` / `max`

## Source Of Truth

- Workbench `/api/projects/{project_id}/sources` handler in
  `services/api/app/main.py`, `PlannedModulePage` source-ledger read in
  `frontend/src/App.jsx`, and source-registry tests.
- `_canonical_project_id` establishes that the endpoint can expose the
  canonical id even when the request uses a route alias.

## Scope

- In scope: add top-level canonical `project_id` to the source-registry read
  payload, require it before `setRegistry`, add API/static regressions, and run
  focused offline checks.
- Out of scope: source entry data, content validation semantics, write routes,
  backend storage, services, providers, browsers, real projects, B6/C14 and
  runtime.

## Success Criteria

- Source-ledger responses carry canonical identity and stale/cross-project
  responses cannot update PlannedModulePage registry state.
- Source-registry/API/frontend contracts, Node suites, Vite and Ruff remain
  green.

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

- 2026-08-03 13:04:07: Task initialized by `tools/hermes_workflow_guard.py init-task`.
- 2026-08-03 13:04:25: Direct Codex selected; no external route dispatched.
