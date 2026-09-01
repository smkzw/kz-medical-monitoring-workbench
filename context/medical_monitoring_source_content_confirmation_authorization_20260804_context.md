# Task Context: medical_monitoring_source_content_confirmation_authorization_20260804

Created: 2026-08-04 04:04:41
Objective: 为来源内容确认写入绑定既有 VALIDATE_SOURCE_REVISION action，使用服务器身份覆盖 actor；离线测试明确既有 DATA_MANAGEMENT 角色，不扩展角色矩阵或其他来源写面
Task type: `code_scoped_patch_plan`
Risk: `high`
Selected agent route: `codex` / `codex-main` / `high`

## Trigger Reason

The shared source-content confirmation route writes a new validation revision
and has an exact existing action, `VALIDATE_SOURCE_REVISION`. It still accepted
the payload actor and had no server-principal boundary. This slice protects
only that confirmation write; source registration and eligibility refresh stay
out of scope.

## Source Of Truth

- `services/api/app/main.py` source confirmation route and shared legacy
  authorization helper.
- `MonitoringAction.VALIDATE_SOURCE_REVISION` role/action matrix.
- `packages/contracts/workbench_contracts/models.py` confirmation request.
- `tests/test_source_content_validation.py` and
  `tests/test_monitoring_risk_index_api.py`.

## Scope

- In scope: require server principal and `VALIDATE_SOURCE_REVISION` before
  source registry mutation; replace actor with the server principal; make the
  offline test principal explicitly include existing `DATA_MANAGEMENT`; add
  fail-closed/role-denied/actor-override regressions.
- Out of scope: role-matrix changes, high-risk e-signature, source registration
  uploads, eligibility refresh, AI runs, frontend, DB/schema/migration,
  middleware/provider, services/browser/API login, real projects, B6/C14 or
  Playwright/UAT activation.

## Success Criteria

- Missing principal returns 503 before source registry mutation.
- Medical-manager-only principal receives existing 403 role denial; an
  explicit data-management role can reach the confirmation path.
- The persisted confirmation actor is the server principal, not payload actor.
- Focused/full tests, compile and Hermes review-gate pass.

## Risk Boundaries

- Do not write to production paths until Codex review gate passes and writable paths are explicit.
- Do not add a new action or silently expand the data-management role matrix.
- The delegated agent is not final authority; Codex owns verification and acceptance.

## Timeout Policy

- Do not mark the delegated agent failed for slow response alone.
- For complex or artifact-heavy work, wait and poll generously; use conference mode when multiple independent model perspectives are needed.
- Failure requires terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.

## Loop Log

- 2026-08-04 04:04:41: Task initialized by `tools/hermes_workflow_guard.py init-task`.
- 2026-08-04: Added the exact validation action guard, server actor override,
  explicit offline role and regressions; focused source-validation/risk-index
  tests passed 32.
- 2026-08-04: Full `tests/test_monitoring*.py` passed **1945 tests, 25 existing
  warnings, 513.72s**; the review-gate is the remaining formal closure check.
