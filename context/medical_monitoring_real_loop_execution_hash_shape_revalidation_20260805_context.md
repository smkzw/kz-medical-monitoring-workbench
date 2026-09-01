# Task Context: medical_monitoring_real_loop_execution_hash_shape_revalidation_20260805

Created: 2026-08-05 08:45:13
Objective: Harden real-loop execution evidence digest validation against silent normalization without runtime activation
Task type: `code_scoped_patch_plan`
Risk: `high`
Selected agent route: `codex` / `codex-main` / `high`

## Trigger Reason

This task was initialized through the Codex x Hermes complex-task entrypoint
because it is a tracked, high-risk source integrity patch on a real-loop
evidence contract, with focused regression and review-gate evidence required.

## Source Of Truth

- `services/api/app/monitoring_real_loop_execution.py`
- `tests/test_monitoring_real_loop_execution.py`
- `context/medical_monitoring_p9_source_only_checkpoint_20260805.md`
- Current authoritative real-loop gate and mode-coverage artifacts.

## Scope

- In scope: exact lowercase 64-hex validation for execution evidence prompt
  and optional output digests; preserve structural execution assessment and
  authority-free report behavior.
- Out of scope: provider/runtime/browser/API login/real-project activity,
  medical-writing data, B6/C14 review, release activation, readiness or
  acceptance-module redesign and unrelated evidence semantics.

## Success Criteria

- Present execution evidence hashes are never accepted after lower/strip
  rewriting or type coercion.
- Existing canonical execution, route-window, missing-output, identity and
  report-chain tests remain green.
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

- 2026-08-05 08:45:13: Task initialized by `tools/hermes_workflow_guard.py init-task`.
- 2026-08-05: Source audit found `_sha256()` in the execution evidence
  contract converted present hashes with `_text(...).lower()` before shape
  validation, allowing noncanonical identities to be rewritten.

## Next Safe Action

Patch only the execution hash helper and focused negative regressions, then
recheck the authoritative gate. Formal source-token/CAS/host/runtime, browser,
real-project and medical-review actions remain blocked.

## Verification Result

- Focused execution suite: 15 passed in 0.07s.
- Adjacent real-loop contract suites: 135 passed in 0.42s.
- Changed modules compile; prompt preflight and review-gate passed with no
  warnings or errors.
- Ruff is unavailable; lint is unverified.
- Reserved ports 8911, 5174, 8910 and 4173 were empty.
- The authoritative real-loop gate remains read-only/blocked; no provider,
  runtime, browser, API login, real project or formal medical review occurred.
