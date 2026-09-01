# Task Context: medical_monitoring_protocol_rule_policy_gap_fail_closed_20260804

Created: 2026-08-04 02:05:53
Objective: 为缺乏精确既有 MonitoringAction 的协议登记、适用性候选/确认/退休和规则包草稿写入面增加显式未配置 fail-closed 边界，服务器身份不再可绕过策略缺口
Task type: `code_scoped_patch_plan`
Risk: `high`
Selected agent route: `codex` / `codex-main` / `high`

## Trigger Reason

This task was initialized through the Codex x Hermes complex-task entrypoint because it is expected to involve more than three execution steps, research/writing/report/code/report-visual work, or source-grounded verification.

## Source Of Truth

- `services/api/app/medical_monitoring_router.py` — policy-gap POST routes and
  shared server-principal read/write seams.
- `services/api/app/monitoring_identity_authorization.py` — current action and
  role matrix; no exact named action exists for this subset.
- Protocol/rule authoring and lifecycle tests plus the prior action inventory in
  `records/active_slices/medical_monitoring_protocol_rule_write_action_inventory_20260804`.
- Gate truth: B6 `pending_review`, C14 `blocked_pending_b6_review`; source,
  approved-input and real-loop gates closed; ports 8911/5174/8910/4173 empty.

## Scope

- In scope: add a visible fail-closed guard before service lookup for five
  policy-gap write routes: protocol-version registration, applicability
  candidate creation/confirmation/retirement and rule-pack draft creation.
  Valid server identity receives explicit `monitoring_write_action_unconfigured`
  403; missing identity remains the existing 503; offline harnesses retain the
  explicit opt-out.
- Out of scope: defining a new action/role matrix, exact-action writes,
  high-risk approvals/signatures, authentication provider/middleware,
  source-token/CAS/B6/C14, services/browser/API login, external models and
  real projects.

## Success Criteria

- No policy-gap route reaches authoring service/repository in production until
  a named action is added and reviewed.
- Missing principal, valid medical-manager principal and explicit offline
  harness behavior are all covered; existing offline lifecycle semantics remain
  unchanged.
- Focused, adjacent and full monitoring regression, Ruff, `py_compile` and
  review-gate pass; no live runtime action occurs.

## Risk Boundaries

- Do not write to production paths until Codex review gate passes and writable paths are explicit.
- The delegated agent is not final authority; Codex owns verification and acceptance.

## Timeout Policy

- Do not mark the delegated agent failed for slow response alone.
- For complex or artifact-heavy work, wait and poll generously; use conference mode when multiple independent model perspectives are needed.
- Failure requires terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.

## Loop Log

- 2026-08-04 02:05:53: Task initialized by `tools/hermes_workflow_guard.py init-task`.
- 2026-08-04 02:06:30: Added `reject_unconfigured_write` guard and five-route
  no-principal/identity-policy tests; focused 150 and adjacent 207 passed.
- 2026-08-04 02:15: Full monitoring regression passed 1936 tests with 25
  warnings in 487.17s; exit code 0. No live runtime action was taken.
