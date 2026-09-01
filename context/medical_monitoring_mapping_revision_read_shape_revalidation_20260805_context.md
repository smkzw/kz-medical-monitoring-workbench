# Task Context: medical_monitoring_mapping_revision_read_shape_revalidation_20260805

Created: 2026-08-05 06:10:49; completed as a direct Codex source-only slice.
Objective: Harden persisted medical-monitoring mapping revision read shape and
lineage identity without runtime activation.
Task type: `finite_code_task`; risk: `high`.

## Source Of Truth

- `services/api/app/monitoring_mapping_draft_repository.py`
- `tests/test_monitoring_mapping_draft_repository.py`
- Authoritative real-loop state is read-only/blocked; it cannot be replaced by
  service, browser, provider, API-login or real-project evidence.

## Scope And Non-Negotiables

- In scope: `_revision_from_row`; strict revision root identifiers/hashes,
  field/source payload shape and pair alignment, source revision lineage,
  semantic-quality report shape/hash, and confirmation metadata; focused
  tamper regressions.
- Out of scope: schema migration, UI/runtime, provider/subagent dispatch,
  8911/5174/8910/4173, Playwright, API login, real projects, B6/C14, clinical
  conclusions and release claims.

## Acceptance

- Revision reads now validate exact non-empty safe identifiers, lowercase
  hashes, positive version, non-empty field/source lists, exact source payload
  keys, field/source pair equality, source input-revision equality, report
  object/hash identity, and confirmation metadata; malformed rows map to a
  stable state-conflict error.
- Added three persisted revision read-shape tamper cases (unexpected source
  key, list-shaped report, empty confirmation actor).
- Evidence: focused mapping repository **53 passed** in 1.97s; adjacent mapping
  group **183 passed** in 3.17s; compileall/Ruff passed; reserved ports empty.

## Residual Boundary

This proves only offline revision persistence integrity. Source-token/CAS,
formal B6 medical outcomes, host/runtime identity, real-project modes,
Playwright role rounds, clinical accuracy, visual acceptance and commercial
release remain unproven/blocked.

## Loop Log

- 2026-08-05 06:10:49: Task initialized by workflow guard.
- 2026-08-05: Direct Codex implementation and read-only verification completed;
  no external route was dispatched.
