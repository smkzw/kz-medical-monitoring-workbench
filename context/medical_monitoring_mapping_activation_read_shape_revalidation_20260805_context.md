# Task Context: medical_monitoring_mapping_activation_read_shape_revalidation_20260805

Created: 2026-08-05 06:21:37; completed as a direct Codex source-only slice.
Objective: Harden persisted mapping activation state and batch binding read
shapes without runtime activation.
Task type: `finite_code_task`; risk: `high`.

## Source Of Truth

- `services/api/app/monitoring_mapping_activation.py`
- `tests/test_monitoring_mapping_activation.py`
- Authoritative real-loop state is read-only/blocked; no service, browser,
  provider, API login or real-project evidence is permitted as a substitute.

## Scope And Non-Negotiables

- In scope: active state row/history/replay rehydration and batch-binding row/
  history readers; strict IDs/revisions/hashes, JSON list shapes, capability
  snapshots, versions/status/timestamps and fail-closed errors; focused
  persisted tamper regressions.
- Out of scope: activation itself, schema migration, UI/runtime, provider or
  subagent dispatch, ports 8911/5174/8910/4173, Playwright, API login, real
  projects, B6/C14, clinical conclusions and release claims.

## Acceptance

- State and binding reads now validate exact text, formal mapping revision,
  lowercase hashes, versions/status/timestamps, capability list/snapshot shape
  and duplicate capability IDs; history/replay dict paths reuse the same
  strict readers.
- Added state-row hash/capability tamper tests, activation-operation replay
  state-shape tamper, and batch-binding hash tamper.
- Evidence: activation **21 passed**; mapping adjacent suite **188 passed**;
  compileall/Ruff passed; reserved ports empty.

## Residual Boundary

This proves only offline activation/binding persistence integrity. It is not an
activation approval and does not prove source-token/CAS replay, formal B6
outcomes, host/runtime identity, real-project modes, Playwright rounds,
clinical accuracy, visual acceptance or commercial release.

## Loop Log

- 2026-08-05 06:21:37: Task initialized by workflow guard.
- 2026-08-05: Direct Codex implementation and read-only verification completed;
  no external route was dispatched.
