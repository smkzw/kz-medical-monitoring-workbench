# Task Context: medical_monitoring_batch_validation_write_authorization_20260804

Created: 2026-08-04 03:21:49
Objective: 为医学监查批次 validation-evidence 与 verify-derived-snapshot 两个精确校验写入绑定既有 VALIDATE_SOURCE_REVISION/CONFIRM_DERIVED_DATA action，保持全量确认与生命周期 transition policy-gap 未放行
Task type: `code_scoped_patch_plan`
Risk: `high`
Selected agent route: `codex` / `codex-main` / `high`

## Trigger Reason

The intake writes are now bound to `INTAKE_BATCH`. Batch lifecycle inventory
found two semantically exact existing actions: validation evidence maps to
`VALIDATE_SOURCE_REVISION`; derived-snapshot verification maps to
`CONFIRM_DERIVED_DATA`. Full-snapshot confirmation and generic state transition
have no exact action and must remain outside this slice.

## Source Of Truth

- `services/api/app/main.py` batch write route definitions.
- `MonitoringAction.VALIDATE_SOURCE_REVISION` and
  `MonitoringAction.CONFIRM_DERIVED_DATA` role/action matrix.
- `tests/test_monitoring_batch_api.py` and batch lifecycle contracts.
- Closed B6/C14 gates and current P10 LOOP ledger.

## Scope

- In scope: bind validation-evidence to `VALIDATE_SOURCE_REVISION` and
  verify-derived-snapshot to `CONFIRM_DERIVED_DATA`; authorize before batch
  repository/service lookup; derive server identity where a downstream actor
  is accepted; update explicit offline test principal roles; add fail-closed
  and unauthorized-role regressions.
- Out of scope: intake writes (already closed), confirm-full-snapshot,
  transition, batch state mutation policy, disposition/workbench writes,
  source validation confirmation, new action/role, auth provider/middleware,
  frontend, DB/schema/migration, B6/C14, runtime/browser/provider/real projects.

## Success Criteria

- Missing principal returns 503 before lookup for both routes.
- Medical-manager/data-management/statistics roles are permitted only where the
  existing role matrix grants the exact mapped action; an unqualified manager
  cannot silently use a generic intake action.
- Focused, adjacent and full monitoring tests pass; compile and Hermes
  review-gate pass.

## Risk Boundaries

- Do not write to production paths until Codex review gate passes and writable paths are explicit.
- Do not reuse `INTAKE_BATCH` or add a generic write flag for lifecycle actions
  without a semantic action; keep policy-gap endpoints unchanged.
- No service/browser/provider/API login/runtime DB/real project/external agent.
- The delegated agent is not final authority; Codex owns verification and acceptance.

## Timeout Policy

- Do not mark the delegated agent failed for slow response alone.
- For complex or artifact-heavy work, wait and poll generously; use conference mode when multiple independent model perspectives are needed.
- Failure requires terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.

## Loop Log

- 2026-08-04 03:21:49: Task initialized by `tools/hermes_workflow_guard.py init-task`.
