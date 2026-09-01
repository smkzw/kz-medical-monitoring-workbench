# Conference Context: eligibility_unit_ledger_v14_gate_20260712

Date: 2026-07-12
Risk: high
Objective: post-fix read-only audit of the eligibility v14 source processing-unit ledger and controlled AI packet fail-closed boundary.

## Binding Route

- Codex is main-venue chair and final authority.
- The only Hermes sub-venue reviewer for this bounded pass is exact `aishuo/MiniMax-M3`.
- Generated Buddy DeepSeek and GLM routes are excluded because they conflict with the user's current routing instruction. No silent fallback is permitted.
- Reasonix is not part of this bounded follow-up; the preceding controlled AI packet already received Reasonix `deepseek-pro` main-venue review.

## Source Of Truth

- Current v14 source and tests listed in the delegated prompt.
- `records/active_slices/eligibility_next_slice_20260711/ELIGIBILITY_SOURCE_UNIT_LEDGER_V14.md`.
- `records/active_slices/eligibility_next_slice_20260711/six_subject_matrix_v2.json`.
- Verification evidence supplied by Codex: focused tests and Ruff passed; final full regression is running.

## Scope

Audit only the v14 processing contract, source-revision identity, unit ledger, artifact/evidence/QC/job binding, idempotency replay, migration failure behavior, strict AI packet gate and product mapping of six real-subject manifests. Do not inspect original clinical folders or clinical content.

## Success Criteria

- Find any reproducible P0/P1 allowing incomplete, stale, wrong-page, legacy, queued-job or un-QC evidence to enter an AI packet.
- Check whether old contract state can become current after source-unit contract changes.
- Check whether idempotent replay returns the original immutable record.
- Distinguish extraction-job success from medical-use evidence closure.
- Keep archive, DOC/DOCX, auth/RBAC/tenant/rate-limit and real clinical processing gates explicit.

## Boundaries

Read-only. No edits, tests, web, browser, images, original clinical folders or production writes. Write exactly the assigned review output. Codex independently verifies every material claim.
