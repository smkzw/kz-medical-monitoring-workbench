# Codex Review: medical_monitoring_p9_upstream_evidence_hash_exact_20260805

Date: 2026-08-05
Mode: Codex direct source-only review
Delegated-agent output: none; the direct Codex route was selected.
Hermes: not used; direct Codex route was selected by the workflow guard.

## Verdict

Pass, bounded to upstream evidence-hash admission. Raw evidence hash bytes are
now preserved; padded/non-string values fail closed under existing diagnostics.

## Boundary Check

- Source and test edits are confined to upstream assembly and its focused
  regressions, plus task-scoped context/review/metrics/record and the P9
  checkpoint/ledger.
- Upstream status meaning, gate authority, provider/runtime, service,
  browser/API login and real-project paths were not activated.
- The formal gate remains `read_only / blocked`; 8911/5174/8910/4173 remain
  empty.

## Codex Verification

- Focused upstream-assembly suite: **13 passed**.
- Selected upstream/manifest/replay/readiness/acceptance adjacency: **85
  passed**.
- `python3 -m py_compile` and targeted `compileall` passed.
- `hermes_workflow_guard.py review-gate --require-verification` returned
  `ok=true`.
- The source check confirms `evidence_sha256` is no longer stripped before the
  lowercase 64-hex check; non-string fields retain their existing field-invalid
  path and cannot prove a gate.
- No browser, provider, live authority, clinical, visual or commercial check
  was attempted because the formal gate is blocked.

## Delegated-Agent Output Review

- No delegated output was used. The change is traceable to the `_text()` hash
  normalization defect and the added padded/non-string regressions.
- Evidence reference pairing, duplicate detection, gate derivation and
  authority flags were preserved.

## Residual Risk

The live source observations, source-token/CAS replay, provider/runtime
identity, browser workflow, clinical/scientific correctness, visual acceptance
and commercial release remain unproven. Five formal reviewer outcomes and
source-token/CAS revalidation are still required before real LOOP activation.
