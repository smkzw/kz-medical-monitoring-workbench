# Task Context: medical_monitoring_protocol_rule_read_authorization_20260804

Created: 2026-08-04 01:15:03
Objective: 为医学监查协议版本、事实、适用性、规则包及规则复核读取面接入既有 READ_MONITORING 服务器 principal/ACL 边界，生产无 principal 继续 503
Task type: `code_scoped_patch_plan`
Risk: `high`
Selected agent route: `codex` / `codex-main` / `high`

## Trigger Reason

This task was initialized through the Codex x Hermes complex-task entrypoint because it is expected to involve more than three execution steps, research/writing/report/code/report-visual work, or source-grounded verification.

## Source Of Truth

- `services/api/app/medical_monitoring_router.py` — protocol/rule GET routes and
  existing provider-neutral `authorize_read` seam.
- `services/api/app/main.py` — production router wiring and existing host
  principal adapter.
- `services/api/app/monitoring_identity_authorization.py` and
  `services/api/app/monitoring_runtime_route_context.py` — existing
  `READ_MONITORING` role/project authorization contract.
- `tests/test_medical_monitoring_module_contract.py`,
  `tests/test_monitoring_protocol_rule_api.py`,
  `tests/test_monitoring_rule_release_chain_p0_20260730.py`,
  `tests/test_monitoring_shadow_sample_service.py` — route and lifecycle
  contracts.
- Current filesystem gate truth: B6 review is `pending_review`, C14 is
  `blocked_pending_b6_review`; approved-input/source-preflight/real-loop gates
  remain closed. Reserved ports 8911/5174/8910/4173 must remain empty.

## Scope

- In scope: add server-principal authorization before repository/service lookup
  for the 13 protocol/rule GET routes: protocol versions, protocol facts,
  applicability list/resolve, rule-pack list/current/detail/source/diff,
  shadow sample sets/lineage/shadow runs, and rule re-review list; add narrow
  no-principal tests; retain explicit offline harness opt-out.
- Out of scope: protocol/rule authoring and shadow/publish writes, auth
  middleware/provider, denied-attempt persistence, source-token/CAS,
  approved-input/B6/C14 changes, services, browser/API login, real projects,
  external model dispatch, frontend redesign and unrelated refactors.

## Success Criteria

- In production wiring, every scoped GET returns 503 with
  `monitoring_principal_unavailable` before a protocol/rule service or
  repository lookup when no server principal exists.
- A malformed/expired/unauthenticated principal remains 401/503 according to
  the existing seam; role or project-scope failure remains 403; a valid scoped
  principal preserves existing downstream 200/404/409 semantics.
- Client actor/payload values do not become authority; no write route changes.
- Focused, adjacent and full monitoring regressions pass; Ruff,
  `py_compile`, and review-gate pass; reserved ports remain empty.

## Risk Boundaries

- Do not write to production paths until Codex review gate passes and writable paths are explicit.
- The delegated agent is not final authority; Codex owns verification and acceptance.

## Timeout Policy

- Do not mark the delegated agent failed for slow response alone.
- For complex or artifact-heavy work, wait and poll generously; use conference mode when multiple independent model perspectives are needed.
- Failure requires terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.

## Loop Log

- 2026-08-04 01:15:03: Task initialized by `tools/hermes_workflow_guard.py init-task`.
- 2026-08-04 01:15:20: Protocol/rule GET inventory reviewed; 13 reads lack the
  existing principal boundary, while authoring/write routes are intentionally
  deferred.
- 2026-08-04 01:15:45: Implemented authorization before lookup and added
  no-principal coverage; focused 117 and adjacent 174 tests passed.
- 2026-08-04 01:23: Full monitoring regression passed 1936 tests with 25
  warnings in 483.21s; exit code 0. No live runtime action was taken.
