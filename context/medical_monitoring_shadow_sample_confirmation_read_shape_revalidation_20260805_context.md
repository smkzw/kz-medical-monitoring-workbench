# Task Context: medical_monitoring_shadow_sample_confirmation_read_shape_revalidation_20260805

Created: 2026-08-05 06:40:36
Objective: Harden persisted monitoring shadow sample confirmation read shape and canonical identity without runtime activation
Task type: `finite_code_task`
Risk: `high`
Selected agent route: `alibaba` / `qwen3.8-max` / `xhigh`

## Trigger Reason

This task was initialized through the Codex x Hermes complex-task entrypoint because it is expected to involve more than three execution steps, research/writing/report/code/report-visual work, or source-grounded verification.

## Source Of Truth

- `services/api/app/monitoring_protocol_rule_repository.py` (`_shadow_sample_confirmation_from_row`)
- `services/api/app/monitoring_protocol_rules.py` (`ShadowSampleMedicalConfirmation.create`)
- `tests/test_monitoring_shadow_sample_service.py` (confirmation lifecycle and tamper regression)
- Current filesystem and the active read-only gate; no runtime or real-project data is in scope.

## Scope

- In scope: strict confirmation-row text/hash/timestamp validation, canonical lowercase digest enforcement, confirmation identity recomputation, and one source-only regression.
- Out of scope: medical confirmation approval, trusted shadow-run semantics, clinical conclusions, schema changes, runtime activation, services/ports, browser/Playwright, providers, real projects, B6/C14 and commercial-release claims.

## Success Criteria

- Uppercase/non-hex confirmation hashes and malformed root metadata fail closed.
- Persisted confirmation IDs are recomputed from canonical content and cannot silently normalize tampered values.
- Existing shadow-sample lifecycle remains green in focused and filtered adjacent suites.
- Compileall/Ruff pass and required ports remain empty.

## Risk Boundaries

- Do not write to production paths until Codex review gate passes and writable paths are explicit.
- The delegated agent is not final authority; Codex owns verification and acceptance.
- Do not dispatch the guard-emitted route: authority remains read-only with provider/runtime activation forbidden. Codex performs this source-only slice directly.

## Timeout Policy

- Do not mark the delegated agent failed for slow response alone.
- For complex or artifact-heavy work, wait and poll generously; use conference mode when multiple independent model perspectives are needed.
- Failure requires terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.

## Loop Log

- 2026-08-05 06:40:36: Task initialized by `tools/hermes_workflow_guard.py init-task`.
- 2026-08-05: Added strict confirmation-row reconstruction and an uppercase confirmation-hash tamper regression. Focused shadow-sample suite: 39 passed in 3.84s. Filtered adjacent protocol/lifecycle/gold-shadow suite: 121 passed in 6.74s. Compileall and Ruff passed; ports 8911/5174/8910/4173 are empty.
