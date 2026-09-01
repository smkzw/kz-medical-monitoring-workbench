# Task Context: medical_monitoring_phase_c11_onboarding_consumer_conservation_20260802

Created: 2026-08-02 01:59:10
Objective: Build a schema-only read-only onboarding/consumer cross-surface conservation contract over C8 coverage, C9 fixture validation and C10 field-presence diff; preserve review-only and inactive boundaries
Task type: `code_scoped_patch_plan`
Risk: `high`
Selected agent route: `codex` / `codex-main` / `high`

## Trigger Reason

This task was initialized through the Codex x Hermes complex-task entrypoint because it is expected to involve more than three execution steps, research/writing/report/code/report-visual work, or source-grounded verification.

## Source Of Truth

- C8 review-only coverage matrix
  `runs/execution/medical_monitoring_phase_c8_adapter_consumer_coverage_20260802/ADAPTER_CONSUMER_COVERAGE_MATRIX.json`
- C9 schema-only source fixture manifest
  `runs/execution/medical_monitoring_phase_c9_source_bound_fixture_validation_20260802/SCHEMA_ONLY_SOURCE_FIXTURE_MANIFEST.json`
- C10 schema-only field-presence report
  `runs/execution/medical_monitoring_phase_c10_source_fixture_diff_report_20260802/SOURCE_FIXTURE_FIELD_PRESENCE_REPORT.json`
- C4-C7 event/projection/consumer contracts and the three named skill contracts already read
  this turn
- Current filesystem is authoritative; no real listing/protocol, browser, service, runtime
  database, adapter invocation or real-project data is in scope.

## Scope

- In scope: a pure read-only conservation contract that joins each C8 observed mapping to
  its C9 schema-only fixture, C10 field-presence row and the C7 frontend consumer surface
  vocabulary (`timeline`, `profile`, `safety_metric`, `risk_link`). It must report structural
  coverage and missing mapping IDs without claiming clinical readiness.
- Out of scope: real source reads, source parsing, clinical normalization, event creation,
  baseline/CTCAE/risk inference, adapter invocation, mapping activation, persistence,
  API/React/UI changes, browser checks, runtime services and real-project runs.

## Success Criteria

- Each C8 mapping ID is represented at most once and is conserved across C8/C9/C10; any
  unknown mapping, identity drift, hash drift or surface overclaim fails closed.
- Each existing row retains source/evidence/revision identity, explicit consumer surfaces,
  C7 surface bindings, `schema_only=true`, `activation_allowed=false` and a structural-only
  readiness state. Missing/incomplete fixture rows remain missing, not silently ready.
- A deterministic report and focused/full contract tests pass without real-source or runtime
  invocation.

## Risk Boundaries

- Generated artifacts are limited to this task's execution evidence path; no production,
  registry, runtime or database writes are allowed.
- The conservation report must not turn C3/C8 observations or schema-only placeholders into
  approved mappings, clinical events, severity, status, normality, baseline, CTCAE, treatment
  identity or risk conclusions.
- Codex is the implementation, review and acceptance authority; no delegated agent, Hermes
  route or conference is used.

## Timeout Policy

- Do not mark the delegated agent failed for slow response alone.
- For complex or artifact-heavy work, wait and poll generously; use conference mode when multiple independent model perspectives are needed.
- Failure requires terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.

## Loop Log

- 2026-08-02 01:59:10: Task initialized by `tools/hermes_workflow_guard.py init-task`.
- 2026-08-02 02:00: direct task contract filled; C11 will join only the existing C8/C9/C10
  structural artifacts and will remain schema-only/inactive.
