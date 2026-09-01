# Task Context: medical_monitoring_assurance_audit_read_route_20260803

Created: 2026-08-03 23:16:04
Objective: 为医学监查保障任务提供基于已验证身份和 READ_RISK_AUDIT ACL 的只读审计链路由，保持无上游身份时 503、无权限时 403，不改变写入事务和认证边界
Task type: `code_scoped_patch_plan`
Risk: `high`
Selected agent route: `codex` / `codex-main` / `high`

## Trigger Reason

This task was initialized through the Codex x Hermes complex-task entrypoint because it is expected to involve more than three execution steps, research/writing/report/code/report-visual work, or source-grounded verification.

## Source Of Truth

- `services/api/app/monitoring_assurance_router.py`: current server-principal
  write authorization seam and assurance route registration.
- `services/api/app/monitoring_assurance_repository.py`: persisted,
  hash-verified assurance audit chain and `list_audit_events` helper.
- `services/api/app/monitoring_identity_authorization.py`: explicit
  `READ_RISK_AUDIT` role/action mapping.
- `tests/test_monitoring_assurance_principal_route.py`: verified-principal
  route boundary and audit persistence tests.

## Scope

- In scope: refactor the assurance router's provider-neutral principal
  authorization helper so read and write actions share one fail-closed path;
  add `GET /api/projects/{project_id}/monitoring/assurance/tasks/{task_id}/audit`
  protected by `READ_RISK_AUDIT`; return only the existing safe public audit
  event representation; add positive/negative route tests.
- Out of scope: authentication/session middleware, default/demo identities,
  audit writes or schema changes, denied-attempt persistence, frontend changes,
  raw clinical data, service/browser/provider/real-project runs, B6/C14 and
  source/approved-input gates.

## Success Criteria

- A verified in-scope medical monitor/manager/director can read the task's
  persisted audit chain; the response preserves event order, hashes and
  principal/decision binding without raw session material.
- A verified system-admin or unrelated role receives 403; missing or malformed
  host principal receives 503; cross-project scope remains 403/404 according
  to the existing route boundary.
- Existing assurance write tests and the full monitoring regression remain
  green; no write behavior or task state changes.
- The route is provider-neutral and does not parse headers/cookies/tokens or
  create a fallback identity.

## Risk Boundaries

- Do not write to production paths until Codex review gate passes and writable paths are explicit.
- The delegated agent is not final authority; Codex owns verification and acceptance.

## Timeout Policy

- Do not mark the delegated agent failed for slow response alone.
- For complex or artifact-heavy work, wait and poll generously; use conference mode when multiple independent model perspectives are needed.
- Failure requires terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.

## Loop Log

- 2026-08-03 23:16:04: Task initialized by `tools/hermes_workflow_guard.py init-task`.
