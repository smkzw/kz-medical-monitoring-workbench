# Task Context: medical_monitoring_batch_digest_shape_revalidation_20260805

Created: 2026-08-05 08:37:51
Objective: Harden derived-snapshot source digest validation at the medical monitoring batch repository boundary without runtime activation
Task type: `code_scoped_patch_plan`
Risk: `high`
Selected agent route: `codex` / `codex-main` / `high`

## Trigger Reason

This task was initialized through the Codex x Hermes complex-task entrypoint because it is a tracked, high-risk source integrity patch with focused regression and review-gate evidence.

## Source Of Truth

- `services/api/app/monitoring_batch_repository.py`
- `tests/test_monitoring_batch_repository.py`
- `context/medical_monitoring_p9_source_only_checkpoint_20260805.md`
- Current authoritative real-loop gate and mode-coverage artifacts.

## Scope

- In scope: exact lowercase 64-hex validation for the
  `verify_derived_snapshot()` source-content identity; preserve canonical
  derived-snapshot verification and existing mismatch/state semantics.
- Out of scope: provider/runtime/browser/API login/real-project activity,
  medical-writing data, B6/C14 review, release activation and unrelated batch,
  parser, mapping or source-registration semantics.

## Success Criteria

- Present derived-snapshot source-content digests are never accepted after
  lower/strip rewriting or type coercion.
- Existing canonical derived-snapshot success, mismatch, idempotency, source
  promotion and batch-state tests remain green.
- Focused/adjacent tests, compileall, guard preflight and review gate pass;
  reserved ports remain empty.

## Risk Boundaries

- The authoritative gate is `read_only`/`blocked`; do not start services or
  ports 8911/5174/8910/4173, call providers, use browser/Playwright or API
  login, touch real projects/medical-writing data, or perform B6/C14/release
  activation.
- Product edits are limited to the two source/test files named above. Codex
  owns verification and acceptance.

## Timeout Policy

- No delegated agent or provider is being launched; Codex owns this bounded
  source-only slice directly under the blocked runtime gate.

## Loop Log

- 2026-08-05 08:37:51: Task initialized by `tools/hermes_workflow_guard.py init-task`.
- 2026-08-05: Source audit found `verify_derived_snapshot()` lowercased the
  supplied source content digest before comparing it with the registered
  parent source, allowing noncanonical identities to be rewritten.

## Verification Result

- Focused repository suite: 53 passed in 1.17s.
- Adjacent batch/API/rule-runner/service/source-preflight suites: 52 passed,
  5 deselected, 17 warnings in 1.81s.
- Combined AI/daily-run/mapping/batch/source regression suites: 1221 passed,
  10 deselected, 17 warnings in 25.14s.
- Changed modules compile; prompt preflight and review-gate passed with no
  warnings or errors.
- Ruff is unavailable; lint is unverified.
- Reserved ports 8911, 5174, 8910 and 4173 were empty.
- The authoritative real-loop gate remains read-only/blocked; no provider,
  runtime, browser, API login, real project or formal medical review occurred.

## Next Safe Action

Recheck the authoritative gate before P10 activation. Keep source-only work
bounded to a concrete integrity gap and preserve the formal sequence: B6
outcomes, source-token/CAS replay, host/runtime identity, real-project modes,
browser role rounds, then release dossier.
