# Codex Review: medical_monitoring_p9_row_fingerprint_input_hash_exact_20260805

Date: 2026-08-05 (Asia/Shanghai)
Delegated-agent output: none; Codex executed the bounded source-only slice directly.

## Verdict

**Pass** — present caller-supplied row fingerprints now satisfy an explicit
canonical identity boundary before comparison, with valid and malformed
regression evidence.

## Boundary Check

- Codex must confirm the delegated agent stayed inside allowed paths.
- Codex must confirm only the requested output file was written.

Codex direct execution stayed inside the workbench. Only the declared
repository/test and task-evidence surfaces were changed; no service, provider,
browser, API login, real project, B6/C14, source-token/CAS or medical-writing
production surface was touched.

## Codex Verification

Source check: `_normalize_rows()` now validates a present
`row_fingerprint` with `_require_exact_sha256()` before comparing the
deterministic domain/data digest.

Verification:

- focused valid/malformed regression: **1 passed**, 58 deselected;
- full batch repository: **59 passed**;
- batch/field-profiler/daily-AI/analysis adjacency: **109 passed**;
- nine-module joint P9 regression: **287 passed** in 10.56s;
- compileall passed; Ruff returned `All checks passed!`;
- prompt preflight and Hermes review-gate with `--require-verification`
  returned `ok=true`;
- authoritative gate assertions passed (`read_only / blocked`), and ports
  8911, 5174, 8910 and 4173 were empty.

Browser, runtime, provider, real-project and clinical checks were not run
because the authoritative gate remains blocked.

## Delegated-Agent Output Review

No delegated output. The direct change is traceable to the optional supplied
row-fingerprint branch and its valid/invalid regression. The adjacent suite
covered batch, field-profiler, daily-run AI and analysis consumers; no
unrelated refactor was introduced.

## Residual Risk

This is an offline input-identity repair. It does not establish source-byte or
source-token/CAS authenticity, reviewer outcomes, runtime authorization,
clinical interpretation, browser UX or commercial release readiness. B6/C14
and the real three-project LOOP remain blocked.
