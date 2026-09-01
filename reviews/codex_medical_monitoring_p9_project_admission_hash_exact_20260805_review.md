# Codex Review: medical_monitoring_p9_project_admission_hash_exact_20260805

Date: 2026-08-05
Mode: Codex direct source-only review
Delegated-agent output: none; the direct Codex route was selected.
Hermes: not used; direct Codex route was selected by the workflow guard.

## Verdict

Pass, bounded to the project-admission hash seam. The contract now preserves
canonical lowercase hash bytes and rejects non-canonical representations before
they can enter diagnostic admission evidence.

## Boundary Check

- Source and test edits are confined to the project-admission contract and its
  focused regression file, plus task-scoped context/review/metrics/record and
  the P9 checkpoint/ledger.
- No provider, runtime, service, browser/API login, real-project or
  medical-writing path was activated.
- The formal gate remains `read_only / blocked`; 8911/5174/8910/4173 remain
  empty.

## Codex Verification

- Focused project-admission suite: **7 passed**.
- Selected real-loop readiness/upstream adjacency: **41 passed**.
- `python3 -m py_compile` and targeted `compileall` passed.
- `hermes_workflow_guard.py review-gate --require-verification` returned
  `ok=true` after the review included the direct-route boundary.
- The source check confirms `_sha256()` no longer calls `str()`, `strip()` or
  `lower()` on the supplied digest; it accepts only an actual raw lowercase
  64-hex string.
- No browser, provider, live authority, clinical, visual or commercial check
  was attempted because the formal gate is blocked.

## Delegated-Agent Output Review

- No delegated output was used. The change is directly traceable to the
  discovered normalization defect and the added uppercase/padded/non-string
  regressions.
- Existing canonical values and diagnostic-only authority flags were preserved;
  audit-chain hash behavior was intentionally left for a separate bounded
  slice.

## Residual Risk

The live source registry, authorization, source-token/CAS replay, provider and
runtime identity, browser workflow, clinical/scientific correctness, visual
acceptance and commercial release remain unproven. Five formal reviewer
outcomes and source-token/CAS revalidation are still required before any real
LOOP activation.
