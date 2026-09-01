# Task Context: medical_monitoring_legacy_action_granularity_20260805

Created: 2026-08-05 23:39:02
Objective: 将旧版医学监查风险、收件箱和 AI 读取路由绑定到精确 READ_* 动作，补齐服务器身份/角色拒绝回归，同时不改变医学事实、批次或运行库
Task type: `code_scoped_patch_plan`
Risk: `high`
Selected agent route: `codex` / `codex-main` / `high`

## Trigger Reason

This task was initialized through the Codex x Hermes complex-task entrypoint because it is expected to involve more than three execution steps, research/writing/report/code/report-visual work, or source-grounded verification.

## Source Of Truth

- `services/api/app/main.py`: legacy monitoring route seam and host-principal adapter.
- `services/api/app/monitoring_identity_authorization.py`: canonical `MonitoringAction` vocabulary and role ACL.
- `tests/test_monitoring_risk_index_api.py`: current legacy risk/readiness/actor-spoof regression surface.
- `reviews/medical_monitoring_system_retro_roadmap_20260801.md`: P9 gap and the current blocked P10 boundary.
- `records/active_slices/medical_monitoring_real_loop_gate_audit_20260804/CURRENT_REAL_LOOP_GATE_AUDIT.json`: authoritative runtime gate.
- Current filesystem and deterministic test output are authoritative for this slice; no service, browser, provider or real-project output is in scope.

## Scope

- In scope: replace generic `READ_MONITORING` on legacy monitoring risk, workbench-inbox and AI read surfaces with the already-declared exact read actions; add focused tests that assert the action argument and role boundary before repository/service access.
- In scope: update source-bound task records, verification evidence, review-gate, LOOP ledger and roadmap with observed results.
- Out of scope: `/api/v1` route migration/alias mounting, authentication middleware implementation, medical facts/dispositions, source registration, batch promotion, SQLite/runtime writes, B6/C14, provider calls, browser/Playwright, real-project LOOP, frontend and medical-writing surfaces.

## Success Criteria

- Risk catalog/index/history/evidence reads use `READ_RISK_AUDIT` and reject a principal lacking that action before the backing repository/service is touched.
- Monitoring workbench-inbox reads use `READ_WORKBENCH_INBOX`; AI run catalog/detail uses `READ_AI_RUN`; AI artifacts use `READ_AI_ARTIFACT` on the registered-monitoring legacy path.
- Client actor/query values remain non-authoritative; no modified route passes them as server identity.
- Existing manager-path behavior and all current 409/403 fail-closed semantics remain intact.
- Focused and adjacent tests, `py_compile`, scoped Ruff and review-gate pass; runtime gate remains blocked and all protected listeners remain stopped.

## Risk Boundaries

- Do not write to production paths until Codex review gate passes and writable paths are explicit.
- The delegated agent is not final authority; Codex owns verification and acceptance.
- Do not alter action ACL membership, medical meaning, source/batch identity, request schemas, persistence or runtime state; only select an existing exact action at the legacy route boundary.
- Preserve the explicit policy-gap behavior (`403 monitoring_*_action_unconfigured`) until a future slice implements the write/read contract.

## Timeout Policy

- Do not mark the delegated agent failed for slow response alone.
- For complex or artifact-heavy work, wait and poll generously; use conference mode when multiple independent model perspectives are needed.
- Failure requires terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.

## Loop Log

- 2026-08-05 23:39:02: Task initialized by `tools/hermes_workflow_guard.py init-task`.
- 2026-08-06: Patched only the declared legacy route action bindings and
  fail-closed role regressions. Focused 42, adjacent 88, and full monitoring
  regression 2550 passed; compileall and scoped test Ruff passed. The full
  suite emitted 25 existing warnings; system Ruff still reports 118 historic
  main.py baseline findings and they were not mixed into this slice.
- 2026-08-06: Gate rechecked as read_only / blocked; medical approval,
  activation, provider, runtime and write authority remain false. 8911/5174/
  8910/4173 remain stopped. Next safe action is formal five-outcome B6 review,
  then source-token/CAS revalidation before any controlled runtime or real
  project LOOP.
