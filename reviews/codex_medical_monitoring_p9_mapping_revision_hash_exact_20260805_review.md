# Codex Review: medical_monitoring_p9_mapping_revision_hash_exact_20260805

Date: 2026-08-05 (Asia/Shanghai)
Delegated-agent output: none; Codex executed the bounded source-only slice directly.

## Verdict

**Pass** — the declared persisted mapping-revision hash boundary was repaired
without changing mapping semantics, and the required offline evidence passed.

## Boundary Check

- Codex must confirm the delegated agent stayed inside allowed paths.
- Codex must confirm only the requested output file was written.

Codex direct execution stayed inside the workbench. Only the declared
repository/test and task-evidence surfaces were changed; no service, provider,
browser, API login, real project, B6/C14, source-token/CAS or medical-writing
production surface was touched.

## Codex Verification

Source check: `_validation_evidence_mutation()` validates an existing
`mapping_sha256` with `_require_exact_sha256()` before content comparison.

Verification:

- focused tamper regression: **1 passed**, 57 deselected;
- full batch repository: **58 passed**;
- batch/field-profiler/daily-AI/analysis adjacency: **108 passed**;
- nine-module joint P9 regression: **286 passed** in 11.54s;
- compileall passed; Ruff returned `All checks passed!`;
- prompt preflight and this review-gate use `--require-verification`;
- Hermes review-gate is the recorded verification gate; it returned `ok=true`
  after the required evidence fields were populated;
- authoritative gate assertions passed (`read_only / blocked`), and ports
  8911, 5174, 8910 and 4173 were empty.

Browser, runtime, provider, real-project and clinical checks were not run
because the authoritative gate remains blocked.

## Delegated-Agent Output Review

No delegated output. The direct change is traceable to the persisted mapping
revision reuse branch and its isolated SQLite tamper test. The adjacent suite
covered the batch repository, field profiler, daily-run AI and analysis
consumers; no unrelated refactor was introduced.

## Residual Risk

This is an offline identity-contract repair. It does not establish that the
source bytes, source-token/CAS lineage, medical reviewer outcomes, runtime
authorization, clinical rule interpretation, browser UX, or commercial release
gates are valid. B6/C14 and the real three-project LOOP remain blocked.
