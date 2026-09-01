# Task Context: medical_monitoring_protocol_rule_write_action_inventory_20260804

Created: 2026-08-04 01:29:08
Objective: 盘点医学监查协议/规则 authoring 与 shadow/publish 写入路由的既有 MonitoringAction、角色、高风险重新认证/签名要求，形成不新增权限动作的下一安全实现边界
Task type: `high_risk_contradiction_review`
Risk: `high`
Selected agent route: `codex` / `gpt-5.6-luna` / `max`

## Trigger Reason

This task was initialized through the Codex x Hermes complex-task entrypoint because it is expected to involve more than three execution steps, research/writing/report/code/report-visual work, or source-grounded verification.

## Source Of Truth

- `services/api/app/medical_monitoring_router.py` — all 14 protocol/rule POST
  routes and request models.
- `services/api/app/monitoring_identity_authorization.py` — existing action,
  role, write, high-risk reauthentication and e-signature matrices.
- `services/api/app/monitoring_runtime_route_context.py` and
  `services/api/app/monitoring_daily_run_router.py` — existing fail-closed
  route authorization pattern and signature-token contract.
- `context/monitoring_p10_protocol_candidate_decision_closure_20260730.md` and
  `records/active_slices/medical_monitoring_goal_p7_20260729/P7_LOOP3_PROTOCOL_RULE_AUTHORING.md`
  — established protocol/rule lifecycle semantics.
- Current gate truth: B6 `pending_review`, C14 `blocked_pending_b6_review`;
  source/approved-input/real-loop gates closed; no services or live projects.

## Scope

- In scope: inventory route-to-action candidates against the existing enum and
  role matrix; identify which routes can be implemented without adding a new
  permission and which require a material policy decision; define high-risk
  reauthentication/evidence-token requirements; recommend bounded follow-up
  slices.
- Out of scope: changing the action enum/role policy, authoring writes,
  authentication provider or middleware, signature verification provider,
  source admission/CAS/B6/C14, services, browser/API login, external model
  dispatch and real projects.

## Success Criteria

- Every protocol/rule POST route is classified with an existing action or
  explicitly marked as lacking an exact action; no route is silently assigned
  an unrelated permission.
- Existing `APPROVE_RULE_CHANGE` director-only/e-signature semantics are
  preserved; evidence SHA-256 is treated as a token, not a signature.
- A follow-up implementation order is recorded with no live-gate dependency.

## Risk Boundaries

- Do not write to production paths until Codex review gate passes and writable paths are explicit.
- The delegated agent is not final authority; Codex owns verification and acceptance.

## Timeout Policy

- Do not mark the delegated agent failed for slow response alone.
- For complex or artifact-heavy work, wait and poll generously; use conference mode when multiple independent model perspectives are needed.
- Failure requires terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.

## Loop Log

- 2026-08-04 01:29:08: Task initialized by `tools/hermes_workflow_guard.py init-task`.
- 2026-08-04 01:30:10: Reviewed all 14 protocol/rule POST routes, the action
  enum/role matrix, and the existing daily-run authorization/signature pattern.
- 2026-08-04 01:31:20: Classified exact-action routes and identified an
  intentional policy gap for protocol registration/applicability candidate
  creation; no new action will be invented in this inventory.
