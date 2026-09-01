# Task Context: medical_monitoring_p9_row_fingerprint_input_hash_exact_20260805

Created: 2026-08-05 20:53:41
Objective: Reject non-canonical supplied batch row fingerprints before comparison without changing deterministic row identity
Task type: `code_open_audit`
Risk: `high`
Selected agent route: `codex` / `codex-main` / `high`

## Trigger Reason

This task was initialized through the Codex x Hermes complex-task entrypoint because it is expected to involve more than three execution steps, research/writing/report/code/report-visual work, or source-grounded verification.

## Source Of Truth

- `services/api/app/monitoring_batch_repository.py`, especially
  `_normalize_rows()` and its optional caller-supplied `row_fingerprint` check.
- `tests/test_monitoring_batch_repository.py` plus adjacent batch, field-profile,
  daily-run AI and analysis suites.
- The P9 checkpoint/LOOP ledger and
  `records/active_slices/medical_monitoring_real_loop_gate_audit_20260804/CURRENT_REAL_LOOP_GATE_AUDIT.json`;
  the authoritative gate remains `read_only / blocked`.

## Scope

- In scope: require a present caller-supplied `row_fingerprint` to be an exact
  lowercase 64-hex SHA-256 string before comparing it with the deterministic
  domain/data fingerprint; add isolated malformed input regressions and retain
  valid supplied/omitted behavior.
- Out of scope: changing row canonicalization or fingerprint algorithm, source
  locators, persistence schema, runtime activation, provider/model calls,
  services, browser/Playwright/API login, real projects, B6/C14 or unrelated
  modules.

## Success Criteria

- Present non-canonical `row_fingerprint` values fail at the explicit identity
  boundary, while a valid supplied fingerprint and omitted fingerprint continue
  to produce the same deterministic `NormalizedRow`.
- Focused/adjacent tests, changed-module compileall, Ruff (if available),
  review-gate with `--require-verification`, gate assertions and reserved-port
  checks pass.

## Risk Boundaries

- Do not write to production paths until Codex review gate passes and writable paths are explicit.
- The delegated agent is not final authority; Codex owns verification and acceptance.

## Timeout Policy

- Do not mark the delegated agent failed for slow response alone.
- For complex or artifact-heavy work, wait and poll generously; use conference mode when multiple independent model perspectives are needed.
- Failure requires terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.

## Loop Log

- 2026-08-05 20:53:41: Task initialized by `tools/hermes_workflow_guard.py init-task`.
- 2026-08-05: Candidate selected from the remaining monitoring row-fingerprint
  `str(...)` comparison scan; this is a bounded source-only input-contract
  hardening slice under the blocked gate.
- 2026-08-05: `_normalize_rows()` now validates a present supplied row
  fingerprint with `_require_exact_sha256()` before deterministic comparison.
  Valid supplied/omitted behavior and five malformed-input subcases were
  covered; focused 1 passed, batch repository 59 passed, adjacency 109 passed,
  and the nine-module joint regression 287 passed.
- 2026-08-05: Changed-module compileall and Ruff passed. Gate assertions still
  report `read_only / blocked`; 8911/5174/8910/4173 remain empty. No provider,
  runtime, browser, API login or real project action occurred.
