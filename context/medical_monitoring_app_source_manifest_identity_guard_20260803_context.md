# Task Context: medical_monitoring_app_source_manifest_identity_guard_20260803

Created: 2026-08-03 12:54:35
Objective: Reject cross-project source-manifest responses before active-manifest state commit.
Task type: `finite_code_task`
Risk: `high`
Selected agent route: `opencode-go` / `deepseek-v4-flash` / `max`

## Source Of Truth

- `frontend/src/App.jsx` App source-manifest fetch and
  `tests/test_frontend_source_manifest_contract.py`.
- `services/api/app/project_source_manifest.py` and
  `tests/test_project_source_manifest.py` establish that public manifests
  expose canonical `project_id`, including alias-backed MY009 manifests.

## Scope

- In scope: guard the App source-manifest read response by the active
  canonical project id, add a static regression, and run focused offline
  checks.
- Out of scope: backend/API contracts, manifest generation, route aliases,
  writes, services, providers, browsers, API login, real projects, B6/C14 and
  runtime state.

## Success Criteria

- A wrong or missing manifest identity cannot populate `sourceManifests`.
- Correct canonical manifests remain accepted without changing alias routing.
- Frontend source-manifest/project contract tests and the existing frontend
  Node/build checks remain green.

## Risk Boundaries

- Keep the change limited to the workbench source and static tests. No service
  or provider may be started; no B6/C14 authority or release claim is granted.
- The route is recorded for audit only and will not be dispatched; direct Codex
  owns verification and acceptance.

## Timeout Policy

- Do not mark the delegated agent failed for slow response alone.
- For complex or artifact-heavy work, wait and poll generously; use conference mode when multiple independent model perspectives are needed.
- Failure requires terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.

## Loop Log

- 2026-08-03 12:54:35: Task initialized by `tools/hermes_workflow_guard.py init-task`.
- 2026-08-03 12:55:00: Direct Codex selected; no external route dispatched.
