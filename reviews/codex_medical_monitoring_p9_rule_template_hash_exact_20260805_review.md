# Codex Review: medical_monitoring_p9_rule_template_hash_exact_20260805

Date: 2026-08-05 19:33:00 +0800
Mode: Codex direct source-only review
Delegated-agent output: none; the external route was recorded but not dispatched because the formal gate is blocked.

## Verdict

Pass for the bounded rule-template recommendation digest boundary. Direct
service decisions now compare the caller's raw digest bytes to the persisted
job identity; padded and uppercase forms fail closed without changing the
canonical decision or idempotent replay path.

## Boundary Check

- The source edit is limited to the recommendation service's expected input
  revision digest comparison and its focused regression, plus task-scoped
  evidence files.
- No provider, runtime, browser/API login, real-project workflow, clinical
  content, or medical-writing path was activated. The gate remains
  `read_only / blocked`; reserved ports are empty.

## Codex Verification

- Focused `tests/test_monitoring_rule_template_recommendation.py`: **19
  passed**.
- Selected offline recommendation, rule, mapping, protocol, AI-service and
  real-loop readiness/revalidation adjacency: **567 passed, 2 warnings**.
- `python3 -m py_compile` and targeted `compileall` passed.
- The new regression proves padded and uppercase direct-service expected
  input-revision hashes return the existing stale-input error (409) before any
  decision mutation.
- `hermes_workflow_guard.py review-gate --require-verification` is the final
  task gate; live provider/runtime/browser/scientific/visual/commercial checks
  remain intentionally unrun under the formal gate.

## Delegated-Agent Output Review

- No delegated output was used; Codex performed the source inspection and
  verification directly.
- The router already enforces the canonical lowercase digest pattern; this
  slice closes the direct service boundary so internal callers cannot bypass
  that contract through normalization.
- Existing candidate selection, rejection, acceptance, replay and mapping
  drift semantics were preserved by the focused and adjacent suites.

## Residual Risk

The live source-token/CAS replay, server authorization, independent AI
provider/runtime identity, Playwright workflow, clinical/scientific accuracy,
visual usability and commercial release criteria remain unproven. The five
formal reviewer outcomes and gate revalidation are still required before P10
real-loop activation.
