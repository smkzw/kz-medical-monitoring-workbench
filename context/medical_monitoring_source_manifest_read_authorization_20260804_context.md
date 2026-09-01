# Task Context: medical_monitoring_source_manifest_read_authorization_20260804

Created: 2026-08-04 04:39:14
Objective: 为 source-manifest GET 路由绑定既有 READ_SOURCE_EVIDENCE action，身份缺失时在 manifest service 读取前 fail-closed；不扩展 module-catalog/shared facts 或来源写入
Task type: `code_scoped_patch_plan`
Risk: `high`
Selected agent route: `codex` / `codex-main` / `high`

## Trigger Reason

The project source manifest GET exposes source roles, route bindings and source
metadata and has the exact existing `READ_SOURCE_EVIDENCE` action. It was still
unauthenticated. This slice protects only the manifest route and keeps module
catalog/shared facts and source writes separate.

## Source Of Truth

- `services/api/app/main.py` `/source-manifest` route and shared legacy
  authorization helper.
- Existing `MonitoringAction.READ_SOURCE_EVIDENCE` matrix.
- `tests/test_project_source_manifest.py` and
  `tests/test_monitoring_risk_index_api.py`.

## Scope

- In scope: require server principal and `READ_SOURCE_EVIDENCE` before public
  manifest reads; preserve canonical alias behavior; add no-principal
  regression and an explicit D001 principal in the API test.
- Out of scope: `/module-catalog`, `/shared-protocol-facts`, source catalog or
  content projection, source uploads/registration, new action/role,
  middleware/provider, frontend, DB/schema/migration, services/browser/API
  login, real projects, B6/C14 or Playwright/UAT activation.

## Success Criteria

- Missing principal returns 503 before manifest service access.
- A project-scoped medical-manager principal reads the D001 alias manifest via
  the existing evidence-read action.
- Focused/full tests, compile and Hermes review-gate pass.

## Risk Boundaries

- Do not write to production paths until Codex review gate passes and writable paths are explicit.
- Do not broaden this guard to generic module metadata or source writes.
- The delegated agent is not final authority; Codex owns verification and acceptance.

## Timeout Policy

- Do not mark the delegated agent failed for slow response alone.
- For complex or artifact-heavy work, wait and poll generously; use conference mode when multiple independent model perspectives are needed.
- Failure requires terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.

## Loop Log

- 2026-08-04 04:39:14: Task initialized by `tools/hermes_workflow_guard.py init-task`.
- 2026-08-04: Added the exact evidence-read guard, preserved canonical alias
  behavior and updated the D001 API fixture; focused tests passed 22.
- 2026-08-04: Full `tests/test_monitoring*.py` passed 1945 with 25 existing
  warnings in 494.33s (exit code 0). Hermes review-gate passed; slice closed.
