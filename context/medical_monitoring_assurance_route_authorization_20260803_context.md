# Task Context: medical_monitoring_assurance_route_authorization_20260803

Created: 2026-08-03 22:40:38
Objective: 将现有医疗监查身份 ACL 接入保障路由，按显式 assurance action 做角色授权，并保持完成任务的再认证/电子签名门禁
Task type: `code_scoped_patch_plan`
Risk: `high`
Selected agent route: `codex` / `codex-main` / `high`

## Trigger Reason

This task was initialized through the Codex x Hermes complex-task entrypoint because it is expected to involve more than three execution steps, research/writing/report/code/report-visual work, or source-grounded verification.

## Source Of Truth

- `services/api/app/monitoring_identity_authorization.py`
- `services/api/app/monitoring_assurance_router.py`
- `services/api/app/monitoring_runtime_principal.py`
- `services/api/app/monitoring_runtime_route_context.py`
- focused assurance/principal/authorization tests under `tests/`

## Scope

- In scope: add explicit assurance actions to the existing ACL; authorize
  assurance create/evidence/review routes from the server principal; preserve
  high-risk complete-task reauthentication and e-signature gates; add negative
  role and positive medical-manager route tests.
- Out of scope: authentication-provider implementation, cookie/token parsing,
  audit persistence/e-signature storage, SQLite migration, aggregate/CAS,
  browser/provider/service start, real project ingestion, and medical-writing.

## Success Criteria

- Medical manager/director are explicitly allowed only for the assurance
  actions needed by these routes; system admin and unrelated roles are denied.
- Create/evidence/review routes fail before service mutation when ACL denies;
  complete route fails before mutation without reauthentication/signature.
- Existing assurance/principal/authorization/audit contract tests remain green.

## Risk Boundaries

- Do not write to production paths until Codex review gate passes and writable paths are explicit.
- The delegated agent is not final authority; Codex owns verification and acceptance.
- The host resolver remains absent in `main.py`; no production assurance write
  can become enabled from this slice alone.

## Timeout Policy

- Do not mark the delegated agent failed for slow response alone.
- For complex or artifact-heavy work, wait and poll generously; use conference mode when multiple independent model perspectives are needed.
- Failure requires terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.

## Loop Log

- 2026-08-03 22:40:38: Task initialized by `tools/hermes_workflow_guard.py init-task`.
- 2026-08-03 22:41-22:44: Added explicit assurance ACL actions and wired the
  route helper to evaluate authorization before service mutation.
- 2026-08-03 22:44: Focused assurance/principal/authorization/audit tests
  passed; complete frontend suite was already green in the preceding slice.
