# Task Context: medical_monitoring_source_registration_read_shape_revalidation_20260805

Created: 2026-08-05 06:31:13
Objective: Harden persisted monitoring source registration read shape and canonical metadata without runtime activation
Task type: `finite_code_task`
Risk: `high`
Selected agent route: `alibaba` / `qwen3.8-max` / `xhigh`

## Trigger Reason

This task was initialized through the Codex x Hermes complex-task entrypoint because it is expected to involve more than three execution steps, research/writing/report/code/report-visual work, or source-grounded verification.

## Source Of Truth

- `services/api/app/monitoring_batch_repository.py` (`MonitoringBatchRepository._source_from_row`)
- `tests/test_monitoring_batch_repository.py` (read-shape and immutability regression coverage)
- Existing source-registration schema/migration code in the same repository; no runtime or real-project data is in scope.
- Current filesystem and the active read-only gate are authoritative. The gate remains blocked: no provider, service, browser, API-login, or real-project execution is permitted.

## Scope

- In scope: strict reconstruction of persisted `SourceRegistration` rows; canonical SHA-256 checks; typed numeric/timestamp/JSON fields; binding-metadata hash recomputation; one focused regression test; source-only deterministic verification.
- Out of scope: schema redesign, migration rewrites, production data, runtime activation, ports/services, browser or Playwright testing, external providers, real study fixtures, B6/C14 activation, and clinical conclusions.

## Success Criteria

- Malformed persisted source rows fail closed with stable `RepositoryIntegrityError` paths.
- Canonical lowercase content/binding hashes and binding metadata are enforced on every read path.
- Existing source-registration behavior remains green under the focused and filtered adjacent suites.
- Source and test files compile and pass Ruff; required runtime ports remain empty.
- Durable records explicitly distinguish accepted evidence from the discarded broad command that selected five `real_` tests.

## Risk Boundaries

- Do not write to production paths until Codex review gate passes and writable paths are explicit.
- The delegated agent is not final authority; Codex owns verification and acceptance.
- Do not dispatch the route emitted by the guard: current read-only authority forbids external provider calls and runtime activation. This is a Codex-direct source-only slice.

## Timeout Policy

- Do not mark the delegated agent failed for slow response alone.
- For complex or artifact-heavy work, wait and poll generously; use conference mode when multiple independent model perspectives are needed.
- Failure requires terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.

## Loop Log

- 2026-08-05 06:31:13: Task initialized by `tools/hermes_workflow_guard.py init-task`.
- 2026-08-05: Implemented strict `_source_from_row` reconstruction and added a lowercase `binding_sha256` tamper regression. Focused repository suite: 49 passed in 0.94s. Filtered adjacent source/mapping/batch suites: 105 passed, 5 deselected (`real_` tests excluded) in 2.13s. Compileall and Ruff passed; ports 8911/5174/8910/4173 are empty.
- An exploratory broad command reported 110 passed plus one warning but selected five existing `real_` tests; that result is discarded and is not acceptance evidence. No product or real-project files were written.
