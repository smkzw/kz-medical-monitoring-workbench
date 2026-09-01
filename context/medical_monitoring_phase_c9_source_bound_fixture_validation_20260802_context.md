# Task Context: medical_monitoring_phase_c9_source_bound_fixture_validation_20260802

Created: 2026-08-02 01:40:27
Objective: Validate source-bound adapter fixture identity and field/evidence coverage against the C8 review-only matrix without reading real listings or activating mappings
Task type: `code_scoped_patch_plan`
Risk: `high`
Selected agent route: `codex` / `codex-main` / `high`

## Trigger Reason

This task was initialized through the Codex x Hermes complex-task entrypoint because it is expected to involve more than three execution steps, research/writing/report/code/report-visual work, or source-grounded verification.

## Source Of Truth

- `services/api/app/monitoring_adapter_consumer_coverage.py` and generated
  C8 matrix
  `runs/execution/medical_monitoring_phase_c8_adapter_consumer_coverage_20260802/ADAPTER_CONSUMER_COVERAGE_MATRIX.json`
- C4/C5/C6 contracts for event/observation/read-model/consumer identity and
  the three named skill contracts already read this turn
- Current filesystem is authoritative; no real listing/protocol, browser,
  service, runtime database, adapter invocation or product-AI output is in scope.

## Scope

- In scope: a pure source-bound fixture validator for schema-only/read-only
  records. It must match each fixture to a C8 coverage observation by mapping
  ID, project/trial, source sheet/field, evidence locator and source revision,
  preserve raw values and explicit missing/unknown status, and report coverage
  without activating mapping or creating a clinical event.
- Out of scope: real source reading/parsing, clinical normalization, baseline or
  CTCAE/risk inference, adapter invocation, mapping activation, persistence,
  API/React/UI changes, browser checks, runtime services and real-project data.

## Success Criteria

- A fixture cannot cross project/trial/adapter/source identity, use a different
  sheet/field/locator than C8, omit source revision or claim active mapping.
- Numeric zero and explicit unknown/missing values are preserved; no normalized
  clinical value or risk is inferred. Path-like locators and malformed date/
  identity fields fail closed.
- A coverage report deterministically records expected/observed/missing mapping
  IDs, `schema_only=true`, `activation_allowed=false`, and source evidence.
- A generated schema-only manifest covers all 46 C8 observations without reading
  real listings or starting any service.

## Risk Boundaries

- Generated artifacts are limited to this task's execution evidence path; no
  production/runtime/registry writes are allowed.
- Codex is the implementation, review and acceptance authority; no delegated
  agent, Hermes route or conference is used.

## Timeout Policy

- Do not mark the delegated agent failed for slow response alone.
- For complex or artifact-heavy work, wait and poll generously; use conference mode when multiple independent model perspectives are needed.
- Failure requires terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.

## Loop Log

- 2026-08-02 01:40:27: Task initialized by `tools/hermes_workflow_guard.py init-task`.
- 2026-08-02 01:41: direct task contract filled; fixture validation will consume
  only the C8 matrix and produce schema-only evidence, never real source data.
- 2026-08-02 01:54: added `services/api/app/monitoring_source_fixture_validation.py`
  and focused tests. `SourceFixtureRecord` requires C8 mapping/project/trial/
  source sheet/field/evidence locator/source revision identity, preserves raw
  values (including numeric zero), allows explicit missing/unknown states, and
  rejects local paths, malformed dates, normalized values, active mapping or
  non-schema-only records. `SourceFixtureValidationReport` records expected,
  observed and missing mapping IDs with deterministic hash.
- 2026-08-02 01:54: generated
  `runs/execution/medical_monitoring_phase_c9_source_bound_fixture_validation_20260802/SCHEMA_ONLY_SOURCE_FIXTURE_MANIFEST.json`
  from C3/C8 evidence: 3 reports and **46 schema-only records**, all complete,
  `schema_only=true`, `activation_allowed=false`; manifest hash is
  `1648fa85e6daba48e28acfa6409595b94baf3582af81d5aefb1e05b665476e60`.
  C9 focused **3 passed**; C1-C9 Python contract suite **68 passed**;
  pycompile/Ruff and manifest generation passed. No real listing/protocol,
  adapter, browser, service, runtime write or real-project run occurred.
