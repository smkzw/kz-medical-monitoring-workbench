# Task Context: medical_monitoring_daily_run_strict_numeric_input_20260805

Created: 2026-08-05 00:37:36
Objective: 为日常医学监查 API 的 CAS/version 请求字段建立严格整数边界，拒绝 bool/字符串隐式转型并完成离线回归
Task type: `code_scoped_patch_plan`
Risk: `high`
Selected agent route: `codex` / `codex-main` / `high`

## Trigger Reason

This task was initialized through the Codex x Hermes complex-task entrypoint because it is expected to involve more than three execution steps, research/writing/report/code/report-visual work, or source-grounded verification.

## Source Of Truth

- `services/api/app/monitoring_daily_run_router.py`: public daily-run request
  models and route boundary.
- `tests/test_monitoring_daily_run_router.py`: existing production principal,
  CAS and route-shape tests.
- `services/api/app/monitoring_ai_router.py`: existing product pattern using
  `StrictInt` for comparable version/count inputs.
- Current P10/B6/C14 and release-gate records: source-only work only; no live
  runtime, provider, browser, Playwright, API login or real project.

## Scope

- In scope: change daily-run request CAS/version fields to `StrictInt` while
  preserving existing bounds and valid JSON integer behavior; add negative
  route regressions for bool/string coercion and run focused/adjacent checks.
- Out of scope: assurance request models, repository schemas, authentication,
  new ACL actions, frontend, B6/C14, approved-input/runtime activation,
  services, providers, browser/Playwright/API login, real projects and
  medical-writing files.

## Success Criteria

- `true`, `false`, and numeric strings are rejected at the request boundary
  with 422 before repository/service mutation.
- Canonical JSON integers and all existing route behavior remain compatible.
- Focused/adjacent tests, compile/lint and the review gate pass; reserved ports
  remain empty.

## Risk Boundaries

- Do not write to production paths until Codex review gate passes and writable paths are explicit.
- The delegated agent is not final authority; Codex owns verification and acceptance.
- This is an input-shape hardening slice and grants no medical, provider or
  runtime authority.

## Timeout Policy

- Do not mark the delegated agent failed for slow response alone.
- For complex or artifact-heavy work, wait and poll generously; use conference mode when multiple independent model perspectives are needed.
- Failure requires terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.

## Loop Log

- 2026-08-05 00:37:36: Task initialized by `tools/hermes_workflow_guard.py init-task`.
- 2026-08-05 00:38:xx: Narrow audit found ordinary Pydantic `int` fields in
  daily-run CAS/version requests; unlike the existing monitoring-AI router,
  they permit bool/string coercion. This slice is limited to those fields.
- 2026-08-05 00:4x: Strict integer fields and route regressions were added.
  Focused 50 and adjacent 132 tests passed under `.venv`; compile, Ruff, port
  checks and Hermes review-gate passed. Live/runtime/medical authority remains
  closed.
