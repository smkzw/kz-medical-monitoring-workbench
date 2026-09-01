# Codex Review: medical_monitoring_p9_source_token_hash_exact_20260805

Date: 2026-08-05
Mode: Codex direct source-only review
Delegated-agent output: none; the direct Codex route was selected.
Hermes: not used; direct Codex route was selected by the workflow guard.

## Verdict

Pass, bounded to source-token evidence expected-hash admission. Raw artifact,
source-inventory and archive-inventory expected SHA-256 bytes are now required
to be lowercase 64-hex values; padded values fail closed.

## Boundary Check

- Source and test edits are confined to source-token evidence revalidation and
  its focused regressions, plus task-scoped context/review/metrics/record and
  the P9 checkpoint/ledger.
- Source-token discovery, token synthesis, `not_proven` semantics, CAS/B6
  authority, provider/runtime, service, browser/API login and real-project
  paths were not activated.
- The formal gate remains `read_only / blocked`; 8911/5174/8910/4173 remain
  empty.

## Codex Verification

- Focused source-token evidence suite: **10 passed**.
- Selected source-token/readiness/acceptance/upstream/manifest adjacency:
  **67 passed**.
- `python3 -m py_compile` and targeted `compileall` passed.
- `hermes_workflow_guard.py review-gate --require-verification` returned
  `ok=true`.
- The source check confirms raw expected hashes are validated for all three
  file inputs and for the persisted inventory hash fields; canonical values
  continue through exact byte comparison.
- No browser, provider, live authority, clinical, visual or commercial check
  was attempted because the formal gate is blocked.

## Delegated-Agent Output Review

- No delegated output was used. The change is traceable to `_valid_sha` and the
  file-level expected-hash admission gap, with padded-input regressions added.
- Inventory replay, source-token `not_proven` conclusion, content summary and
  authority flags were preserved.

## Residual Risk

The live source observations, source-token/CAS replay, provider/runtime
identity, browser workflow, clinical/scientific correctness, visual acceptance
and commercial release remain unproven. Five formal reviewer outcomes and
source-token/CAS revalidation are still required before real LOOP activation.
