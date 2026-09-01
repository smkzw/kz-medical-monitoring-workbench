# Task Context: medical_monitoring_primary_run_write_authorization_20260804

Created: 2026-08-04 01:17:47
Objective: 为医学监查显式 runs 生成风险快照写入接入既有 RUN_DETERMINISTIC_RULES 服务器 principal/ACL 边界，生产无 principal 在任何快照计算或写入前 503
Task type: `code_scoped_patch_plan`
Risk: `high`
Selected agent route: `codex` / `codex-main` / `high`

## Trigger Reason

This task was initialized through the Codex x Hermes complex-task entrypoint because it is expected to involve more than three execution steps, research/writing/report/code/report-visual work, or source-grounded verification.

## Source Of Truth

- `services/api/app/medical_monitoring_router.py` — primary `/runs` command
  route and existing provider-neutral principal/ACL seam.
- `services/api/app/medical_monitoring_summary.py` — snapshot computation and
  repository write boundary called by the route.
- `services/api/app/main.py` — fail-closed production router wiring.
- `services/api/app/monitoring_identity_authorization.py` and
  `services/api/app/monitoring_runtime_route_context.py` — existing
  `RUN_DETERMINISTIC_RULES` permission contract.
- Module/risk-export/protocol/rule/identity/runtime/frontend tests and current
  filesystem gate truth. B6 remains `pending_review`; C14 remains
  `blocked_pending_b6_review`; reserved ports 8911/5174/8910/4173 stay empty.

## Scope

- In scope: authorize `POST /api/projects/{project_id}/modules/medical-monitoring/runs`
  with the existing server principal and `RUN_DETERMINISTIC_RULES` action
  before registry lookup, risk evaluation or snapshot persistence; add focused
  no-principal/role/no-write tests and evidence.
- Out of scope: protocol/rule authoring writes, auth middleware/provider,
  denied-attempt persistence, source-token/CAS, approved-input/B6/C14 changes,
  services, browser/API login, external model dispatch, real projects and
  frontend redesign.

## Success Criteria

- Production with no principal returns 503 `monitoring_principal_unavailable`
  and leaves the risk database byte-identical.
- A principal without `RUN_DETERMINISTIC_RULES` returns 403 before registry or
  snapshot work; an explicit offline harness opt-out preserves existing tests.
- Existing 201/200/404 run semantics are unchanged for authorized/offline
  calls; focused, adjacent and full monitoring regressions plus Ruff,
  `py_compile` and review-gate pass.

## Risk Boundaries

- Do not write to production paths until Codex review gate passes and writable paths are explicit.
- The delegated agent is not final authority; Codex owns verification and acceptance.

## Timeout Policy

- Do not mark the delegated agent failed for slow response alone.
- For complex or artifact-heavy work, wait and poll generously; use conference mode when multiple independent model perspectives are needed.
- Failure requires terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.

## Loop Log

- 2026-08-04 01:17:47: Task initialized by `tools/hermes_workflow_guard.py init-task`.
- 2026-08-04 01:18:15: Confirmed `/runs` is the remaining primary snapshot
  write without a server identity boundary; action mapping is the existing
  `RUN_DETERMINISTIC_RULES`, so no new policy action is needed.
- 2026-08-04 01:18:50: Added fail-closed write authorization and no-principal/
  role tests; focused 119 and adjacent 176 passed.
- 2026-08-04 01:27: Full monitoring regression passed 1936 tests with 25
  warnings in 485.58s; exit code 0. No live runtime action was taken.
