# Task Context: medical_monitoring_risk_disposition_high_risk_authorization_20260804

Created: 2026-08-04 03:51:28
Objective: 为两个医学监查风险处置写入绑定既有 CHANGE_RISK_DISPOSITION，并要求服务器身份、高风险重新认证与电子签名证据；不触碰通用 inbox action 或跨模块 policy-gap
Task type: `code_scoped_patch_plan`
Risk: `high`
Selected agent route: `codex` / `codex-main` / `high`

## Trigger Reason

The two workbench risk-disposition routes are controlled writes with an exact
existing action (`CHANGE_RISK_DISPOSITION`) and a high-risk context. They were
still callable without a server principal, reauthentication or signature
evidence. This slice closes only that boundary and leaves generic inbox
actions/cross-module reads for separate policy decisions.

## Source Of Truth

- `services/api/app/main.py` route handlers and the shared
  `_authorize_legacy_monitoring_action` helper.
- `packages/contracts/workbench_contracts/models.py`
  `RuxRiskDispositionActionRequest`.
- Existing `CHANGE_RISK_DISPOSITION` role matrix and high-risk
  reauthentication/e-signature contract.
- `tests/test_monitoring_risk_index_api.py`, disposition service tests and the
  closed B6/C14/P10 evidence.

## Scope

- In scope: add explicit reauthentication/signature fields to the compatibility
  request model; bind both risk-disposition routes to server identity,
  `CHANGE_RISK_DISPOSITION`, `high_risk=True`; derive the server actor; add
  fail-closed, high-risk and actor-override regressions; run full monitoring
  verification and review-gate.
- Out of scope: generic inbox mark-read action, dashboard/workbench-inbox GET,
  source registration, AI routes, new action/role, auth middleware/provider,
  frontend reauth UX, DB/schema/migration, services/browser/provider/API
  login, real projects, B6/C14 or Playwright/UAT activation.

## Success Criteria

- Missing principal returns 503 before the disposition service.
- Missing reauthentication/signature returns the existing 403 reason codes.
- A valid offline principal reaches the existing service with
  `principal.server_actor`, never the payload actor.
- Focused/full tests, compile and Hermes review-gate pass.

## Risk Boundaries

- Do not write to production paths until Codex review gate passes and writable paths are explicit.
- Do not lower the high-risk contract, accept a client actor as authoritative,
  or reuse an unrelated action.
- The delegated agent is not final authority; Codex owns verification and acceptance.

## Timeout Policy

- Do not mark the delegated agent failed for slow response alone.
- For complex or artifact-heavy work, wait and poll generously; use conference mode when multiple independent model perspectives are needed.
- Failure requires terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.

## Loop Log

- 2026-08-04 03:51:28: Task initialized by `tools/hermes_workflow_guard.py init-task`.
- 2026-08-04: Added high-risk server-principal guards, request evidence fields
  and offline regressions; focused authorization/disposition suite passed 37
  tests.
- 2026-08-04: Full `tests/test_monitoring*.py` passed **1943 tests, 25 existing
  warnings, 500.72s**; the review-gate is the remaining formal closure check.
