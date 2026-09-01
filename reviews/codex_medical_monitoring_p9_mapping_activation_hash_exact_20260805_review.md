# Codex Review: medical_monitoring_p9_mapping_activation_hash_exact_20260805

Date: 2026-08-05
Mode: Codex direct source-only review
Delegated-agent output: none; the direct Codex route was selected.
Hermes: not used; direct Codex route was selected by the workflow guard.

## Verdict

Pass, bounded to mapping profile and capability-manifest hash admission. Raw
profile and capability-manifest SHA-256 bytes are now required to be exact
lowercase 64-hex strings; padded/uppercase values fail closed.

## Boundary Check

- Source and test edits are confined to mapping activation and its focused
  regressions, plus task-scoped context/review/metrics/record and the P9
  checkpoint/ledger.
- Mapping semantics, clinical capability decisions, authority flags,
  provider/runtime, service, browser/API login and real-project paths were not
  activated.
- The formal gate remains `read_only / blocked`; 8911/5174/8910/4173 remain
  empty.

## Codex Verification

- Focused mapping-activation suite: **24 passed**.
- Selected mapping/batch/draft/semantic-quality/readiness/acceptance/
  manifest-replay adjacency: **212 passed**.
- `python3 -m py_compile` and targeted `compileall` passed.
- `hermes_workflow_guard.py review-gate --require-verification` returned
  `ok=true`.
- The source check confirms `_require_hash` no longer coerces, trims or
  lowercases supplied identity bytes; profile and capability-manifest
  boundaries use the strict path.
- No browser, provider, live authority, clinical, visual or commercial check
  was attempted because the formal gate is blocked.

## Delegated-Agent Output Review

- No delegated output was used. The change is traceable to the mapping
  activation hash-normalization defect and the added focused regressions.
- Existing source-chain validation, semantic quality evaluation, capability
  disposition and persisted-state replay semantics were preserved.

## Residual Risk

The live source observations, source-token/CAS replay, provider/runtime
identity, browser workflow, clinical/scientific correctness, visual acceptance
and commercial release remain unproven. Five formal reviewer outcomes and
source-token/CAS revalidation are still required before real LOOP activation.
