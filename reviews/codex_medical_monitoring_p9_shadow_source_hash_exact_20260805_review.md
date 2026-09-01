# Codex Review: medical_monitoring_p9_shadow_source_hash_exact_20260805

Date: 2026-08-05 11:33 +0800
Delegated-agent output: `runs/pi_medical_monitoring_p9_shadow_source_hash_exact_20260805.md`

## Verdict

Pass for the bounded source-only integrity slice; the external route was intentionally not dispatched. This does not clear the independent real-loop gate.

## Boundary Check

- Work remained in the configured workbench and task-scoped evidence paths.
- No provider, runtime, service, browser, API login, real project, or medical-writing path was activated.

## Codex Verification

- `MonitoringRuleAuthoringService._usable_source()` and `_usable_monitoring_source()` now require both validation and registry hashes to be exact lowercase 64-hex strings with byte-for-byte equality; non-string input no longer reaches `.lower()`.
- `MonitoringShadowSampleService._batch_source()` now rejects non-canonical or mismatched source hashes in the frozen batch, usable source and source registrations, and projects the exact bound value without lowercasing.
- Shadow-sample service suite: **41 passed, 1 existing deprecation warning**.
- Authoring service suite: **9 passed**; gold-shadow suite: **16 passed**.
- Protocol-rule/repository suite: **63 passed**.
- Batch/authoring adjacency: **73 passed, 27 subtests**.
- Protocol API/lifecycle/review/cross-project adjacency: **57 passed, 1 existing deprecation warning**.
- Daily-run/record-resolver/repository adjacency: **96 passed, 41 subtests**.
- `python3 -m py_compile` passed for changed source and tests.
- Prompt preflight and review-gate are required before slice closure; runtime/provider/browser/real-project acceptance remains unperformed.

## Delegated-Agent Output Review

- No delegated-agent output was used; the runner path remains reserved and was not dispatched.
- Changes are limited to source-hash boundary checks and regressions. Evaluation-state and diagnostic-code normalization were intentionally left unchanged.
- Codex retains final authority for runtime, browser, scientific, visual and commercial acceptance.

## Residual Risk

- Real source-token/CAS replay, authorization, provider/runtime, browser, scientific, visual and commercial acceptance remain unverified.
- The gate still requires five hash-bound formal reviewer outcomes and revalidation before any activation or real LOOP.

## Hermes Boundary

- Hermes route was recorded by the workflow guard but not dispatched; no external output or provider call is part of this slice.
