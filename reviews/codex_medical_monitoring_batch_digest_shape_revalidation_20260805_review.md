# Codex Review: medical_monitoring_batch_digest_shape_revalidation_20260805

Date: 2026-08-05
Delegated-agent output: none; Codex direct source-only work.

## Verdict

Pass for the bounded source-only derived-snapshot digest slice. This does not
establish provider, runtime, browser, clinical, B6/C14 or commercial-release
readiness.

## Boundary Check

- Product changes must remain limited to `monitoring_batch_repository.py` and
  `test_monitoring_batch_repository.py`; task records are durable evidence.
- No provider, service, port, browser/Playwright, API login, real project,
  medical-writing or release activation action is allowed.

## Hermes Role

Hermes/provider dispatch was intentionally skipped because the authoritative
real-loop gate is `read_only`/`blocked`; no external-agent output was used.

## Codex Verification

- Focused `tests/test_monitoring_batch_repository.py`: **53 passed** in 1.17s.
- Adjacent batch/API/rule-runner/service/source-preflight suites:
  **52 passed, 5 deselected, 17 warnings** in 1.81s.
- Combined AI, daily-run, mapping and batch/source regression suites:
  **1221 passed, 10 deselected, 17 warnings** in 25.14s.
- Changed modules compile with `compileall`.
- Guard prompt preflight passed; review-gate is recorded separately.
- Ruff is unavailable in the current venv/PATH, so lint remains unverified.
- Reserved ports 8911, 5174, 8910 and 4173 must remain empty.
- The authoritative gate remains `read_only`/`blocked`; live runtime/provider,
  browser and clinical acceptance was intentionally not attempted.

## Direct Work Review

`verify_derived_snapshot()` now uses exact lowercase 64-hex SHA-256 validation
for the source-content identity. The regression covers padded, uppercase,
non-hex, short and non-string values while preserving the existing success and
mismatch/state paths. No delegated-agent output was used.

## Residual Risk

Runtime/provider, source-token/CAS replay, clinical correctness, visual
usability, browser role rounds, formal medical review and final release dossier
remain blocked by the authoritative gate.
