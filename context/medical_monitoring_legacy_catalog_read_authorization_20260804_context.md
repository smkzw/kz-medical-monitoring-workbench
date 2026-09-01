# Task Context: medical_monitoring_legacy_catalog_read_authorization_20260804

Created: 2026-08-04 03:36:34
Objective: 为旧项目 risks 与 data-batches 目录读取绑定既有 READ_MONITORING action；身份缺失时在仓储查询前 fail-closed，不扩展跨模块 dashboard/inbox policy-gap
Task type: `code_scoped_patch_plan`
Risk: `high`
Selected agent route: `codex` / `codex-main` / `high`

## Trigger Reason

The offline legacy-route inventory found two remaining catalog reads whose
semantics are unambiguously medical-monitoring reads and therefore map to the
existing `MonitoringAction.READ_MONITORING`. They can be protected without
inventing a new action or changing the closed B6/C14 runtime gates.

## Source Of Truth

- `services/api/app/main.py` route definitions for `/risks` and `/data-batches`
  and `_authorize_legacy_monitoring_action`.
- Existing `MonitoringAction.READ_MONITORING` role/action matrix and canonical
  project resolver.
- `tests/test_monitoring_risk_index_api.py` and `tests/test_contracts.py`.
- Closed B6 review gate, blocked C14 activation gate, and P10 LOOP ledger.

## Scope

- In scope: add server-principal authorization to the two legacy catalog GETs;
  canonicalize before repository access; add fail-closed and authorized-path
  regressions; record verification and ledger evidence.
- Out of scope: dashboard, workbench inbox, source registration, AI legacy
  routes, lifecycle/disposition writes, new action/role, middleware/provider,
  frontend, DB/schema/migration, services, browser/provider/API login, real
  projects, B6/C14 or Playwright/UAT activation.

## Success Criteria

- Missing server principal returns 503 `monitoring_principal_unavailable`
  before the risk or batch repository is queried.
- An explicit project-scoped medical-manager principal can read both catalogs
  through the existing `READ_MONITORING` action.
- Focused tests, compile and Hermes review-gate pass; no unrelated route or
  policy behavior changes.

## Risk Boundaries

- Do not write to production paths until Codex review gate passes and writable paths are explicit.
- Do not reuse a generic write action, add a new permission, or grant
  cross-module dashboard/inbox access as part of this read slice.
- The delegated agent is not final authority; Codex owns verification and acceptance.

## Timeout Policy

- Do not mark the delegated agent failed for slow response alone.
- For complex or artifact-heavy work, wait and poll generously; use conference mode when multiple independent model perspectives are needed.
- Failure requires terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.

## Loop Log

- 2026-08-04 03:36:34: Task initialized by `tools/hermes_workflow_guard.py init-task`.
- 2026-08-04: Added `READ_MONITORING` guards to both catalog reads, updated
  offline principal-backed tests and no-principal regressions, and verified the
  focused suite.
- 2026-08-04: Full `tests/test_monitoring*.py` passed **1940 tests, 25 existing
  warnings, 539.76s**; review-gate is the remaining closure check.
