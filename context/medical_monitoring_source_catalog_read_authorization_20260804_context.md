# Task Context: medical_monitoring_source_catalog_read_authorization_20260804

Created: 2026-08-04 04:17:08
Objective: 为共享来源目录 GET /api/projects/{project_id}/sources 绑定既有 READ_SOURCE_EVIDENCE action，身份缺失时在 registry 读取前 fail-closed；不扩展 source-contents 或来源写入
Task type: `code_scoped_patch_plan`
Risk: `high`
Selected agent route: `codex` / `codex-main` / `high`

## Trigger Reason

The shared source catalog GET exposes source entries, spans and validation
history and has an exact existing read action, `READ_SOURCE_EVIDENCE`. It was
still unauthenticated. This slice protects only that catalog route and leaves
the narrower source-content projection and all source writes separate.

## Source Of Truth

- `services/api/app/main.py` `/sources` route and the shared legacy
  authorization helper.
- Existing `MonitoringAction.READ_SOURCE_EVIDENCE` role/action matrix.
- `tests/test_source_registry.py` and `tests/test_monitoring_risk_index_api.py`.
- Closed B6/C14/P10 evidence and current LOOP ledger.

## Scope

- In scope: require server principal and `READ_SOURCE_EVIDENCE` before source
  registry reads; update offline source-registry clients with an explicit
  project-scoped principal; add no-principal regression.
- Out of scope: `/source-contents`, `/source-manifest`, source uploads/
  registration, content confirmation writes, AI runs, new action/role,
  middleware/provider, frontend, DB/schema/migration, services/browser/API
  login, real projects, B6/C14 or Playwright/UAT activation.

## Success Criteria

- Missing principal returns 503 before `source_registry.list_entries`.
- An explicit project-scoped medical-manager principal can read the catalog via
  the existing action.
- Focused/full tests, compile and Hermes review-gate pass.

## Risk Boundaries

- Do not write to production paths until Codex review gate passes and writable paths are explicit.
- Do not broaden the route to source uploads or content projections, and do not
  invent a source-specific action.
- The delegated agent is not final authority; Codex owns verification and acceptance.

## Timeout Policy

- Do not mark the delegated agent failed for slow response alone.
- For complex or artifact-heavy work, wait and poll generously; use conference mode when multiple independent model perspectives are needed.
- Failure requires terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.

## Loop Log

- 2026-08-04 04:17:08: Task initialized by `tools/hermes_workflow_guard.py init-task`.
- 2026-08-04: Added the exact read-action guard, explicit source-registry test
  principal and no-principal regression; focused tests passed 32.
- 2026-08-04: Full `tests/test_monitoring*.py` passed **1945 tests, 25 existing
  warnings, 492.80s**; the review-gate is the remaining formal closure check.
