# Task Context: medical_monitoring_assurance_strict_numeric_input_20260805

Created: 2026-08-05 00:40:08
Objective: 为医学监查保障 API 的 CAS/计数请求字段建立严格整数边界，拒绝 bool/字符串隐式转型并完成离线回归
Task type: `code_scoped_patch_plan`
Risk: `high`
Selected agent route: `codex` / `codex-main` / `high`

## Trigger Reason

This task was initialized through the Codex x Hermes complex-task entrypoint because it is expected to involve more than three execution steps, research/writing/report/code/report-visual work, or source-grounded verification.

## Source Of Truth

- `services/api/app/monitoring_assurance_router.py`: public P8 assurance
  request models and route boundary.
- `tests/test_monitoring_assurance_principal_route.py` and
  `tests/test_monitoring_assurance.py`: existing production-principal,
  CAS, full-recompute, rollup and completion tests.
- `services/api/app/monitoring_ai_router.py` and the completed daily-run
  strict-input slice: existing `StrictInt` boundary pattern.
- Current P10/B6/C14 and release-gate records: source-only work only; no live
  runtime, provider, browser, Playwright, API login or real project.

## Scope

- In scope: change assurance CAS/version and non-negative count request fields
  to `StrictInt`, preserving bounds and valid JSON integer behavior; add
  production-boundary bool/string regressions and run focused/adjacent checks.
- Out of scope: owner assignment semantics, repository schema, authentication,
  ACL actions, frontend, B6/C14, approved-input/runtime activation, services,
  providers, browser/Playwright/API login, real projects and medical-writing
  files.

## Success Criteria

- `true`, `false`, and numeric strings are rejected at the assurance request
  boundary with 422 before task/proof/rollup mutation.
- Canonical JSON integers and existing assurance route behavior remain
  compatible.
- Focused/adjacent tests, compile/lint and review-gate pass; reserved ports
  remain empty.

## Risk Boundaries

- Do not write to production paths until Codex review gate passes and writable paths are explicit.
- The delegated agent is not final authority; Codex owns verification and acceptance.
- This is input-shape hardening only; it grants no medical, provider or runtime
  authority.

## Timeout Policy

- Do not mark the delegated agent failed for slow response alone.
- For complex or artifact-heavy work, wait and poll generously; use conference mode when multiple independent model perspectives are needed.
- Failure requires terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.

## Loop Log

- 2026-08-05 00:40:08: Task initialized by `tools/hermes_workflow_guard.py init-task`.
- 2026-08-05 00:40:xx: Narrow audit found ordinary Pydantic `int` fields in
  assurance CAS/count requests. This slice preserves the separate user-facing
  owner assignment field and targets only numeric shape.
- 2026-08-05 00:4x: Strict integer fields and route regressions were added.
  Focused 41 and adjacent 155 tests passed under `.venv`; compile, Ruff, port
  checks and Hermes review-gate passed. Live/runtime/medical authority remains
  closed.
