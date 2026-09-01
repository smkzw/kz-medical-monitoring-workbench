# Task Context: medical_monitoring_phase_c12_adapter_fallback_retirement_20260802

Created: 2026-08-02 02:07:50
Objective: Define a read-only source-specific adapter fallback and retirement contract over C8-C11 structural evidence; fail closed to limited/unavailable without clinical or mapping inference
Task type: `code_scoped_patch_plan`
Risk: `high`
Selected agent route: `codex` / `codex-main` / `high`

## Trigger Reason

This task was initialized through the Codex x Hermes complex-task entrypoint because it is expected to involve more than three execution steps, research/writing/report/code/report-visual work, or source-grounded verification.

## Source Of Truth

- C8 review-only adapter consumer coverage matrix
  `runs/execution/medical_monitoring_phase_c8_adapter_consumer_coverage_20260802/ADAPTER_CONSUMER_COVERAGE_MATRIX.json`
- C9 schema-only source fixture manifest, C10 field-presence report and C11
  cross-surface conservation report
- C2 adapter descriptor/translation contracts and current adapter/source-registry boundaries
- Current filesystem is authoritative; no real listing/protocol, browser, service, runtime
  database, adapter invocation or real-project data is in scope.

## Scope

- In scope: a typed read-only policy describing what the product may expose when a
  source-specific adapter is unavailable, stale, structurally incompatible or not yet
  medically approved, plus explicit retirement conditions for any fallback. The only safe
  fallback is a limited/unavailable structural status with source-bound evidence links; it
  must never fabricate a clinical event, normalized value, risk, treatment identity or active
  mapping.
- Out of scope: adapter invocation, source parsing, mapping activation, runtime persistence,
  API/React/UI changes, browser checks, real source data, real-project dry runs and authority
  migration.

## Success Criteria

- Every C8 coverage row gets a deterministic fallback policy and a non-empty retirement
  checklist; fallback state is limited/unavailable, never success or clinical-ready.
- Policies retain adapter/project/trial/source/evidence identity, C11 surface bindings and
  explicit risk-link policy; unknown failure reasons, active mappings, unsupported fallback
  modes and incomplete retirement conditions fail closed.
- A generated matrix covers all 46 review-only observations, preserves schema-only/inactive
  flags and passes focused/full contract tests without runtime invocation.

## Risk Boundaries

- Generated artifacts are limited to this task's execution evidence path; no production,
  registry, runtime or database writes are allowed.
- Fallback is a display/diagnostic boundary only. It cannot silently substitute data, inherit
  another project's thresholds/table names, create C4 events or permit risk decisions.
- Codex is the implementation, review and acceptance authority; no delegated agent, Hermes
  route or conference is used.

## Timeout Policy

- Do not mark the delegated agent failed for slow response alone.
- For complex or artifact-heavy work, wait and poll generously; use conference mode when multiple independent model perspectives are needed.
- Failure requires terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.

## Loop Log

- 2026-08-02 02:07:50: Task initialized by `tools/hermes_workflow_guard.py init-task`.
- 2026-08-02 02:08: direct task contract filled; C12 will encode fail-closed limited/unavailable
  fallback and explicit retirement gates over existing review-only structural evidence.
- 2026-08-02 02:12: added `services/api/app/monitoring_adapter_fallback_contract.py` and
  focused tests. Each mapping permits only `limited` or `unavailable`, defaults to
  `unavailable`, exposes metadata-only diagnostics, blocks risk actions and remains
  `schema_only=true`/`activation_allowed=false`. Six source/medical/consumer/runtime
  conditions are required before fallback retirement; no condition is asserted as met.
- 2026-08-02 02:12: generated
  `runs/execution/medical_monitoring_phase_c12_adapter_fallback_retirement_20260802/ADAPTER_FALLBACK_RETIREMENT_POLICY_MATRIX.json`:
  3 reports / 46 policies, 0 missing mappings, all `not_retired`; content hash
  `0cd6d75dc37f3a420928948aca6ec75b97c1c7ab546828dd499f08e97231bb42`.
  C12 focused **4 passed**; C1-C12 contract suite **79 passed**; pycompile/Ruff,
  deterministic matrix generation and review gate passed. No real source, adapter,
  service, runtime or project run occurred.
