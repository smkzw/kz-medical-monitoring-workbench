# Task Context: medical_monitoring_protocol_rule_exact_write_authorization_20260804

Created: 2026-08-04 01:41:30
Objective: 为协议事实 AI 候选采纳与规则包 shadow 启动/自动运行/运行接入既有 REVIEW_AI_CANDIDATE 或 RUN_DETERMINISTIC_RULES 服务器 principal/ACL，生产 payload actor 不再作为权限来源
Task type: `code_scoped_patch_plan`
Risk: `high`
Selected agent route: `codex` / `codex-main` / `high`

## Trigger Reason

This task was initialized through the Codex x Hermes complex-task entrypoint because it is expected to involve more than three execution steps, research/writing/report/code/report-visual work, or source-grounded verification.

## Source Of Truth

- `services/api/app/medical_monitoring_router.py` — existing nested
  `authorize_write` seam and exact-action protocol/rule POST routes.
- `services/api/app/monitoring_identity_authorization.py` — existing
  `REVIEW_AI_CANDIDATE` and `RUN_DETERMINISTIC_RULES` role/action contracts.
- `services/api/app/monitoring_rule_authoring_service.py` and
  `services/api/app/monitoring_shadow_sample_service.py` — downstream actor
  and lifecycle methods.
- Protocol/rule API, release-chain, shadow-sample and identity/runtime tests;
  current gates B6 `pending_review`, C14 `blocked_pending_b6_review`, with
  reserved ports 8911/5174/8910/4173 empty.

## Scope

- In scope: authorize four exact-action POST routes before service lookup:
  protocol-fact AI-candidate adoption (`REVIEW_AI_CANDIDATE`), rule-pack
  start-shadow, automatic-shadow-runs and shadow-runs
  (`RUN_DETERMINISTIC_RULES`); pass the server actor to existing actor-aware
  downstream methods; add no-principal/role tests.
- Out of scope: protocol registration/applicability/draft policy-gap routes,
  high-risk confirm/confirm-shadow/publish signatures, action enum/role
  changes, auth middleware/provider, source-token/CAS/B6/C14, services,
  browser/API login, external model dispatch and real projects.

## Success Criteria

- Production missing identity returns 503 before authoring/shadow service
  lookup; a medical-writer principal returns 403 for all four routes.
- Payload actor values are ignored in production; existing offline behavior and
  downstream 200/201/409 semantics remain intact.
- Focused, adjacent and full monitoring regressions, Ruff, `py_compile` and
  review-gate pass; no live runtime action occurs.

## Risk Boundaries

- Do not write to production paths until Codex review gate passes and writable paths are explicit.
- The delegated agent is not final authority; Codex owns verification and acceptance.

## Timeout Policy

- Do not mark the delegated agent failed for slow response alone.
- For complex or artifact-heavy work, wait and poll generously; use conference mode when multiple independent model perspectives are needed.
- Failure requires terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.

## Loop Log

- 2026-08-04 01:41:30: Task initialized by `tools/hermes_workflow_guard.py init-task`.
- 2026-08-04 01:42:10: Implemented exact-action authorization and server-actor
  handoff for four routes; focused 127 and adjacent 184 passed.
- 2026-08-04 01:51: Full monitoring regression passed 1936 tests with 25
  warnings in 492.31s; exit code 0. No live runtime action was taken.
- 2026-08-04 02:00: Added explicit reauthentication/evidence-token fields and
  director-only `APPROVE_RULE_CHANGE` authorization to fact confirmation, rule
  confirmation, shadow confirmation and publish; focused 140 and adjacent 197
  passed.
- 2026-08-04 02:09: Full monitoring regression passed 1936 tests with 25
  warnings in 490.01s; exit code 0. No live runtime action was taken.
