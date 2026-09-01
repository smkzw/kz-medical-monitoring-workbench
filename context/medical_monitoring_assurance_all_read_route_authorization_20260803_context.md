# Task Context: medical_monitoring_assurance_all_read_route_authorization_20260803

Created: 2026-08-03 23:44:07
Objective: 将医学监查保障任务的列表、详情、就绪、全量证明和三级汇总读取统一接入 READ_RISK_AUDIT 身份边界，生产无 principal 继续 503，保留明确隔离的旧测试 harness
Task type: `code_scoped_patch_plan`
Risk: `high`
Selected agent route: `codex` / `codex-main` / `high`

## Trigger Reason

This task was initialized through the Codex x Hermes complex-task entrypoint because it is expected to involve more than three execution steps, research/writing/report/code/report-visual work, or source-grounded verification.

## Source Of Truth

- `services/api/app/monitoring_assurance_router.py`: assurance route table;
  only the audit read route currently uses `READ_RISK_AUDIT`.
- `services/api/app/monitoring_identity_authorization.py`: canonical read ACL.
- `services/api/app/monitoring_principal_host_adapter.py` and
  `services/api/app/main.py`: production host principal seam and fail-closed
  wiring.
- `tests/test_monitoring_assurance_principal_route.py`: production boundary
  tests with/without a verified principal.
- `tests/test_monitoring_assurance.py`: isolated legacy route harness used by
  the existing offline service tests.

## Scope

- In scope: protect assurance task list/detail, readiness evaluation, full
  recompute proof read and rollup read with the same provider-neutral
  `READ_RISK_AUDIT` decision path; add request identity tests and keep the
  production default fail-closed at 503.
- The existing explicit `require_server_principal=False` route factory option
  remains only for the offline legacy test harness, so its deterministic
  service tests do not need a real host session. Production `main.py` remains
  `require_server_principal=True`; no new production caller may use the bypass.
- Out of scope: auth/session middleware or IdP integration, headers/cookies/
  token parsing, denied-attempt persistence, new ACL actions, writes/schema,
  frontend, service/browser/provider/API login, runtime DB, real projects,
  B6/C14 and approved-input gates.

## Success Criteria

- Every assurance read route takes a `Request`, requests `READ_RISK_AUDIT`,
  and rejects absent/malformed/unscoped/system-admin-only principals in the
  production router before task lookup (503/403 as already defined).
- The isolated legacy test factory remains explicit and is not used by
  `main.py`; existing assurance tests remain green.
- Cross-project behavior, 404 task/proof/rollup semantics and write route
  authorization are preserved.
- No read route mutates task/audit state or accepts a client actor as identity.

## Risk Boundaries

- Do not write to production paths until Codex review gate passes and writable paths are explicit.
- The delegated agent is not final authority; Codex owns verification and acceptance.
- Do not weaken the production default to make tests pass. If a legacy test
  needs the explicit factory bypass, keep it visible in test setup and record
  that it is not production evidence.

## Timeout Policy

- Do not mark the delegated agent failed for slow response alone.
- For complex or artifact-heavy work, wait and poll generously; use conference mode when multiple independent model perspectives are needed.
- Failure requires terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.

## Loop Log

- 2026-08-03 23:44:07: Task initialized by `tools/hermes_workflow_guard.py init-task`.
- 2026-08-03 23:45:xx: Inspected the full assurance route table and found list,
  detail, readiness, proof-read and rollup-read routes lacked the production
  principal/ACL seam; the host still has no authentication middleware.
- 2026-08-03 23:46:xx: Added `READ_RISK_AUDIT` authorization to those five
  read surfaces and kept the explicit `require_server_principal=False` branch
  only for existing offline test harnesses. A first syntax check caught a
  Python default/non-default parameter ordering error; the request parameter
  was reordered before tests were rerun.
