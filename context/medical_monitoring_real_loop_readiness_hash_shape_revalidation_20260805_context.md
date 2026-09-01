# Task Context: medical_monitoring_real_loop_readiness_hash_shape_revalidation_20260805

Created: 2026-08-05 08:53:11
Objective: Harden real-loop readiness source and upstream evidence digest validation against silent normalization without runtime activation
Task type: `code_scoped_patch_plan`
Risk: `high`
Selected agent route: `codex` / `codex-main` / `high`

## Trigger Reason

This task was initialized through the Codex x Hermes complex-task entrypoint
because it is a tracked, high-risk source integrity patch on a real-loop
readiness evidence contract, with focused regression and review-gate evidence
required.

## Source Of Truth

- `services/api/app/monitoring_real_loop_readiness.py`
- `tests/test_monitoring_real_loop_readiness.py`
- Current authoritative real-loop gate and mode-coverage artifacts.

## Scope

- In scope: exact lowercase 64-hex validation for readiness source, prompt,
  semantics, generalization and upstream evidence digests; preserve authority-
  free readiness diagnostics.
- Out of scope: provider/runtime/browser/API login/real-project activity,
  medical-writing data, B6/C14 review, release activation and unrelated
  scenario, route or authority semantics.

## Success Criteria

- Present readiness digests are never accepted after lower/strip rewriting or
  type coercion, and invalid values are not copied into report digest fields.
- Existing canonical readiness and blocked/ready diagnostics remain green.
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

- 2026-08-05 08:53:11: Task initialized by `tools/hermes_workflow_guard.py init-task`.
- 2026-08-05: Source audit found readiness source, prompt, semantics,
  generalization and upstream digest paths using `_text`/`lower` normalization.

## Verification Result

- Focused readiness suite: 22 passed in 0.07s.
- All real-loop contract suites: 138 passed in 0.40s.
- Changed modules compile; prompt preflight and review-gate passed with no
  warnings or errors.
- Ruff is unavailable; lint is unverified.
- Reserved ports 8911, 5174, 8910 and 4173 were empty.
- The authoritative real-loop gate remains read-only/blocked; no provider,
  runtime, browser, API login, real project or formal medical review occurred.

## Next Safe Action

Recheck the authoritative gate before any P10 activation. Continue only with a
concrete source-only integrity gap; formal B6/source-token/CAS/host/runtime,
browser and real-project testing remain blocked.
