# Codex Review: medical_monitoring_p9_migration_hash_exact_20260805

Date: 2026-08-05
Mode: Codex direct source-only review
Delegated-agent output: none; the direct Codex route was selected.
Hermes: not used; direct Codex route was selected by the workflow guard.

## Verdict

Pass, bounded to the read-only migration hash contract. Migration, rollback,
backup and authority evidence hashes now require exact lowercase 64-hex bytes;
padded/uppercase values fail closed.

## Boundary Check

- Source and test edits are confined to the migration contract and focused
  regressions, plus task-scoped context/review/metrics/record and the P9
  checkpoint/ledger.
- No migration execution, SQLite write/backup/rollback, authority grant,
  provider/runtime, service, browser/API login or real-project path was
  activated.
- The formal gate remains `read_only / blocked`; 8911/5174/8910/4173 remain
  empty.

## Codex Verification

- Focused migration-contract suite: **20 passed**.
- Selected migration/startup-recovery/readiness/acceptance/manifest adjacency:
  **70 passed, 17 warnings**; warnings are deprecation notices only.
- `python3 -m py_compile` and targeted `compileall` passed.
- `hermes_workflow_guard.py review-gate --require-verification` returned
  `ok=true`.
- The source check confirms `_hash` preserves supplied hash bytes and the
  backup observation no longer lowercases or strips before validation.
- No browser, provider, live authority, clinical, visual or commercial check
  was attempted because the formal gate is blocked.

## Delegated-Agent Output Review

- No delegated output was used. The change is traceable to migration hash
  normalization at `_hash` and backup observation admission.
- Ledger ordering, reconciliation decisions and all write-permitted false
  invariants were preserved.

## Residual Risk

The live migration stores, source-token/CAS replay, provider/runtime identity,
browser workflow, clinical/scientific correctness, visual acceptance and
commercial release remain unproven. Five formal reviewer outcomes and
source-token/CAS revalidation are still required before real LOOP activation.
