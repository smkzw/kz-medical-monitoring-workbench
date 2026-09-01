# Task Context: medical_monitoring_approved_input_source_binding_20260803

Created: 2026-08-03 CST
Objective: bind the diagnostic approved-input gate to hash-bound source-batch declarations and a live read-only source preflight, without enabling runtime or changing real project state.
Task type: `code_open_audit`
Risk: `medium`

## Source of truth

- `records/active_slices/medical_monitoring_formal_reviewer_provenance_package_20260802/B6_FORMAL_REVIEWER_PROVENANCE_PACKAGE.json`
- `services/api/app/monitoring_approved_input_dry_run.py`
- `services/api/app/monitoring_source_batch_preflight.py`
- `records/active_slices/medical_monitoring_real_source_batch_preflight_20260803/REAL_SOURCE_BATCH_PREFLIGHT.json`
- existing B6/C14 gate evidence and protected frontend hashes

## Completed

- Added `ControlledApprovedInputDryRunReport`, stable source-batch binding digest,
  and `dry_run_approved_input_with_source_preflight`.
- The controlled entrypoint requires `source_batch_bindings` and
  `source_batch_binding_sha256` inside the package hash, reconstructs typed
  records, and reopens actual files through source preflight.
- Current formal package returns `blocked`, 15 issues, including
  `source_batch_binding_missing`; no authority is granted.
- Focused tests: 15 passed; Ruff/format/compile passed.

## Boundaries

- Pure diagnostic contract only. No runtime/API/provider/browser/SQLite/source
  registry writes; no frontend or medical-writing changes.
- 8911 and 5174 remain stopped.
- The current source preflight still reports zero promoted eligible full batches;
  this contract does not promote MG-K10 candidates or infer reviewer approval.

## Upstream recheck (2026-08-03)

- B6 evidence SHA `1f3df053b094c3b6f974e1deec78f17446b03c00e54557b667fcd159ac05557e`:
  `pending_review`, 5 candidates/5 outcomes, 0 accepted review IDs, two unresolved
  blockers, write/migration false.
- C14 gate SHA `44ea7a602c9aa017f14992ac4af45efd18203ab4a8e1f1396dda9555a5dca4be`:
  `blocked_pending_b6_review`, 46/46 rows blocked, activation/event/projection/write
  false.
- The formal package SHA remains `a9e2664307dc5a7224e35fc7b57b0bd231c91959de5e925469411e311efffd68`;
  it still has zero `source_batch_bindings`. No upstream evidence drift was observed.

## Next safe action

After authorized B6 outcomes plus source-token/CAS closure, create a new
hash-bound formal package with explicit source-batch bindings and rerun the
controlled entrypoint. Do not start controlled runtime or real-project LOOP
before that gate and the upstream C14/identity gates are green.
