# Task Context: medical_monitoring_source_content_projection_read_authorization_20260804

Created: 2026-08-04 04:28:17
Objective: 为 source-contents 证据投影 GET 路由绑定既有 READ_SOURCE_EVIDENCE action，身份缺失时在 projection service 读取前 fail-closed；不扩展 source catalog 或写入
Task type: `code_scoped_patch_plan`
Risk: `high`
Selected agent route: `codex` / `codex-main` / `high`

## Trigger Reason

The source-content projection GET exposes project-scoped source bindings and
metadata and has the exact existing `READ_SOURCE_EVIDENCE` action. It was still
unauthenticated. This slice protects only that projection route; the catalog
and all source writes remain separate slices.

## Source Of Truth

- `services/api/app/main.py` `/source-contents` route and shared legacy
  authorization helper.
- Existing `MonitoringAction.READ_SOURCE_EVIDENCE` matrix.
- `tests/test_source_content_projection_api.py` and
  `tests/test_monitoring_risk_index_api.py`.

## Scope

- In scope: require server principal and `READ_SOURCE_EVIDENCE` before source
  projection service reads; update the offline projection client; add a
  no-principal regression.
- Out of scope: `/sources`, `/source-manifest`, source uploads/registration,
  content confirmation writes, AI runs, new action/role, middleware/provider,
  frontend, DB/schema/migration, services/browser/API login, real projects,
  B6/C14 or Playwright/UAT activation.

## Success Criteria

- Missing principal returns 503 before projection service access.
- An explicit project-scoped medical-manager principal can read canonical and
  alias projections via the existing evidence-read action.
- Focused/full tests, compile and Hermes review-gate pass.

## Risk Boundaries

- Do not write to production paths until Codex review gate passes and writable paths are explicit.
- Do not broaden this guard to unrelated project metadata or source writes.
- The delegated agent is not final authority; Codex owns verification and acceptance.

## Timeout Policy

- Do not mark the delegated agent failed for slow response alone.
- For complex or artifact-heavy work, wait and poll generously; use conference mode when multiple independent model perspectives are needed.
- Failure requires terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.

## Loop Log

- 2026-08-04 04:28:17: Task initialized by `tools/hermes_workflow_guard.py init-task`.
- 2026-08-04: Added the exact evidence-read guard, explicit projection test
  principal and no-principal regression; focused tests passed 13.
- 2026-08-04: Full `tests/test_monitoring*.py` passed **1945 tests, 25 existing
  warnings, 502.89s**; the review-gate is the remaining formal closure check.
