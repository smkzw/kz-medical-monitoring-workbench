# Task Context: medical_monitoring_source_metadata_read_authorization_20260804

Created: 2026-08-04 05:03:20
Objective: 为 module-catalog 与 shared-protocol-facts 读面绑定既有 READ_SOURCE_EVIDENCE action，并离线记录 dashboard/inbox/AI/source-registration 无精确 action 的 policy gap；不扩展跨模块写入或运行态 gates
Task type: `code_scoped_patch_plan`
Risk: `high`
Selected agent route: `codex` / `codex-main` / `high`

## Trigger Reason

This task was initialized through the Codex x Hermes complex-task entrypoint because it is expected to involve more than three execution steps, research/writing/report/code/report-visual work, or source-grounded verification.

## Source Of Truth

- `services/api/app/main.py`: `/module-catalog` and
  `/shared-protocol-facts` handlers, plus the existing legacy authorization
  helper.
- `services/api/app/monitoring_identity_authorization.py`: the immutable
  `READ_SOURCE_EVIDENCE` action and role matrix.
- `tests/test_contracts.py`, `tests/test_shared_protocol_fact_projection_api.py`
  and `tests/test_monitoring_risk_index_api.py`.
- P10/B6/C14 gate records: B6 remains `pending_review`; C14 remains
  `blocked_pending_b6_review`; no runtime activation is permitted.

## Scope

- In scope: require a server-verified, project-scoped principal and
  `READ_SOURCE_EVIDENCE` before module-catalog and shared-protocol-facts
  projection reads; preserve alias/canonical behavior; add no-principal and
  scoped-principal regressions; record policy classification for adjacent
  routes.
- Out of scope: dashboard/inbox/AI run reads or writes, source registration and
  eligibility admission writes, new action/role, auth middleware/provider,
  frontend, DB/schema/migration, services/browser/API login, real projects,
  external dispatch, B6/C14 or Playwright/UAT activation.

## Success Criteria

- Missing principal returns 503 before either projection service is accessed.
- A project-scoped medical-manager principal can read both projections through
  the existing evidence-read action; cross-project scope is denied.
- Focused tests, adjacent monitoring tests, full monitoring regression,
  `py_compile` and Hermes review-gate pass.
- Adjacent dashboard/inbox/AI/source-registration routes are recorded as
  policy gaps because no existing action is semantically exact; no generic
  monitoring action is reused for them.

## Risk Boundaries

- Do not write to production paths until Codex review gate passes and writable paths are explicit.
- The delegated agent is not final authority; Codex owns verification and acceptance.

## Timeout Policy

- Do not mark the delegated agent failed for slow response alone.
- For complex or artifact-heavy work, wait and poll generously; use conference mode when multiple independent model perspectives are needed.
- Failure requires terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.

## Loop Log

- 2026-08-04 05:03:20: Task initialized by `tools/hermes_workflow_guard.py init-task`.
- 2026-08-04: Offline route inventory found module-catalog and shared protocol
  facts are source-derived read projections with an exact existing action;
  dashboard/inbox/AI/source-registration remain separate policy gaps.
- 2026-08-04: Focused suite passed 35; full `tests/test_monitoring*.py`
  passed 1945 with 25 existing warnings in 503.30s (exit code 0). Hermes
  review-gate passed; slice closed.
