# Task Context: medical_monitoring_shadow_sample_set_read_shape_revalidation_20260805

Created: 2026-08-05 06:37:05
Objective: Harden persisted monitoring shadow sample-set read shape and canonical identity without runtime activation
Task type: `finite_code_task`
Risk: `high`
Selected agent route: `alibaba` / `qwen3.8-max` / `xhigh`

## Trigger Reason

This task was initialized through the Codex x Hermes complex-task entrypoint because it is expected to involve more than three execution steps, research/writing/report/code/report-visual work, or source-grounded verification.

## Source Of Truth

- `services/api/app/monitoring_protocol_rule_repository.py` (`_shadow_sample_set_from_row`)
- `services/api/app/monitoring_protocol_rules.py` (canonical shadow sample/sample-set factories)
- `tests/test_monitoring_shadow_sample_service.py` (provisional sample lifecycle and tamper regressions)
- Current filesystem and the active read-only gate; no runtime or real-project data is authoritative for this slice.

## Scope

- In scope: strict persisted shadow sample-set reconstruction; canonical lowercase SHA-256 checks; typed batch version/timestamp/JSON checks; sample identity/content recomputation; source-only regression tests.
- Out of scope: clinical rule judgement, medical confirmation, schema redesign, runtime activation, services/ports, browser or Playwright tests, external providers, real study fixtures, B6/C14 activation, and commercial-release claims.

## Success Criteria

- Malformed sample-set rows fail closed before a provisional sample set is returned.
- Uppercase/non-hex hashes and non-integer batch versions are rejected rather than coerced.
- Existing provisional shadow-sample lifecycle behavior remains green in focused and filtered adjacent suites.
- Source/test files compile and pass Ruff; required runtime ports remain empty.
- Durable records distinguish accepted filtered evidence from any excluded `real_` tests.

## Risk Boundaries

- Do not write to production paths until Codex review gate passes and writable paths are explicit.
- The delegated agent is not final authority; Codex owns verification and acceptance.
- Do not dispatch the guard-emitted route: current authority is read-only with provider/runtime activation forbidden. Codex performs this bounded slice directly.

## Timeout Policy

- Do not mark the delegated agent failed for slow response alone.
- For complex or artifact-heavy work, wait and poll generously; use conference mode when multiple independent model perspectives are needed.
- Failure requires terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.

## Loop Log

- 2026-08-05 06:37:05: Task initialized by `tools/hermes_workflow_guard.py init-task`.
- 2026-08-05: Added strict sample-set row reconstruction and two tamper tests. Focused shadow-sample suite: 38 passed in 3.98s. Filtered adjacent protocol/lifecycle/gold-shadow suites: 120 passed in 6.51s. Compileall and Ruff passed; ports 8911/5174/8910/4173 are empty.
- No provider, service, browser, API login, real project, or runtime activation was used.
