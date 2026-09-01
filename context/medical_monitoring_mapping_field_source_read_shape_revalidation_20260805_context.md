# Task Context: medical_monitoring_mapping_field_source_read_shape_revalidation_20260805

Created: 2026-08-05 06:05:22; completed as a direct Codex source-only slice.
Objective: Harden persisted medical-monitoring mapping field-source read shape and
parent bindings without runtime activation.
Task type: `finite_code_task`
Risk: `high`

## Source Of Truth

- `services/api/app/monitoring_mapping_draft_repository.py`
- `tests/test_monitoring_mapping_draft_repository.py`
- Current real-loop gate remains read-only and blocked; no service, browser,
  provider, API login, or real project data is an allowed verification source.

## Scope And Non-Negotiables

- In scope: the `_field_sources` persistence read boundary; strict scalar,
  lowercase SHA-256, evidence-ID list, and project/draft parent validation;
  focused regression tests and source-only evidence.
- Out of scope: schema migration, UI/runtime work, provider or subagent
  dispatch, 8911/5174/8910/4173, Playwright, API login, real projects, B6/C14,
  clinical conclusions, and release claims.
- Preserve the existing immutable SQLite triggers and mapping semantics.

## Implementation And Acceptance

- `_field_sources` now routes each row through `_field_source_from_row` and
  converts any malformed persisted lineage into
  `MonitoringMappingStateConflictError`.
- Rehydration requires exact project/draft binding, non-empty unpadded text
  fields, lowercase SHA-256 values, and a non-empty unique JSON list of string
  evidence IDs.
- Added parameterized tamper regressions for uppercase hash, empty prompt
  version, and object-shaped evidence IDs.
- Done evidence: focused mapping repository test 50 passed; adjacent mapping
  suite 180 passed; compileall and Ruff passed; reserved ports empty.

## Residual Boundary

This proves only offline persistence-contract behavior. Signed source-token/CAS
replay, formal B6 medical outcomes, host/runtime identity, real-project mode
coverage, Playwright role rounds, clinical accuracy, visual acceptance, and
commercial release gates remain unproven and blocked by the authoritative gate.

## Loop Log

- 2026-08-05 06:05:22: Task initialized by workflow guard.
- 2026-08-05: Direct Codex patch and read-only verification completed; no
  external route was dispatched.
