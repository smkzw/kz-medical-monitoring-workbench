# Task Context: medical_monitoring_real_source_batch_preflight_20260803

Created: 2026-08-03 00:36:10
Objective: Read-only preflight of canonical medical-monitoring source batches and provenance evidence for RUX, MG-K10-SAR, and MY009; do not run runtime or change product source.
Task type: `code_open_audit`
Risk: `medium`
Selected agent route: `codex` / `codex-main` / `high`

## Trigger Reason

This task was initialized through the Codex x Hermes complex-task entrypoint because it is expected to involve more than three execution steps, research/writing/report/code/report-visual work, or source-grounded verification.

## Source Of Truth

- Current workbench source contracts and evidence:
  - `records/active_slices/medical_monitoring_project_source_adapter_reconciliation_20260802/PROJECT_SOURCE_ADAPTER_RECONCILIATION.json`
  - `records/active_slices/medical_monitoring_candidate_matrix_20260802/CANDIDATE_MATRIX.json`
  - `context/monitoring_p10_real_project_source_matrix_20260729.md`
  - `context/monitoring_p10_rux_incremental_source_validation_20260730.md`
  - `records/active_slices/medical_monitoring_mgk10_source_revalidation_20260802/CANDIDATE_INVENTORY.json`
  - `records/active_slices/medical_monitoring_my009_source_inventory_recheck_20260802/SOURCE_INVENTORY.json`
  - `records/active_slices/medical_monitoring_my009_source_token_content_revalidation_20260802/SOURCE_TOKEN_CONTENT_REVALIDATION.json`
  - `runs/execution/medical_monitoring_phase_b6_review_gate_20260801/B6_REVIEW_OUTCOME_GATE.json`
  - `runs/execution/medical_monitoring_phase_c14_b6_activation_gate_20260802/B6_TO_C13_ACTIVATION_GATE_REPORT.json`
- The three canonical monitoring roots are the only candidates for this preflight:
  `proj_rux_03_002`, `proj_mgk10_sar_real`, and `proj_my009_uc`.
- External project files were read only to re-hash the already declared protocol/listing paths; no source file was written.

## Scope

- In scope: read-only verification of the exact protocol/listing paths, SHA-256 values, source classes, existing batch references, distinct full-snapshot evidence, and current B6/C14/readiness gates; produce an evidence artifact and a reusable read-only integrity contract for the later approved-input step.
- Out of scope: source registration, batch creation or mutation, SQLite/API runtime writes, provider/browser execution, medical decisions, frontend changes, 8911/5174 startup, real-project LOOP execution, and onboarding MY008 candidate roots. The new contract is not wired to activation or runtime.

## Success Criteria

- Every canonical project has an explicit source row with path, byte count, SHA-256, source class, and eligibility decision.
- Duplicate/processed/restored/comparison files are not counted as a second provenance-complete full batch.
- The report records the current B6/C14 block and keeps all runtime/provider/write/medical authority false.
- The report is independently hashable and review-gate verifiable; it does not claim real LOOP readiness.

## Risk Boundaries

- Do not write to production paths until Codex review gate passes and writable paths are explicit.
- No runtime database, provider route, browser session, source registry, batch state, or clinical state may be changed in this slice. The only product-code change permitted here is the isolated read-only preflight contract and its focused test.
- A filesystem path existing is not evidence that a batch is eligible; historical context may not be promoted by inference.
- B6 reviewer approval is not inferred from engineering defer records; no risk disposition, aggregate, CAS, or source token may be synthesized.
- The final artifact is diagnostic evidence only; Codex remains final authority.

## Timeout Policy

- Do not mark the delegated agent failed for slow response alone.
- For complex or artifact-heavy work, wait and poll generously; use conference mode when multiple independent model perspectives are needed.
- Failure requires terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.

## Loop Log

- 2026-08-03 00:36:10: Task initialized by `tools/hermes_workflow_guard.py init-task`.
- 2026-08-03: Re-hashed the declared RUX, MG-K10-SAR, and MY009 protocol/listing files; checked 8911/5174 listeners (none) and protected frontend hashes (unchanged).
- 2026-08-03: Consolidated the canonical source rows and existing historical candidate decisions into `records/active_slices/medical_monitoring_real_source_batch_preflight_20260803/REAL_SOURCE_BATCH_PREFLIGHT.json`.
- 2026-08-03: JSON syntax passed; all 11 protocol/listing path hash-and-size checks passed; project-admission/readiness/execution focused regression passed **25 tests**; Hermes review-gate returned `ok=true`.
- 2026-08-03: No listener was observed on 8911/5174; protected `frontend/src/App.jsx` and `frontend/src/styles.css` hashes remained unchanged. The slice is complete, but the product goal remains active and the real LOOP step is still gated by B6/approved-input/source-token/CAS/runtime.
- 2026-08-03: Added the reusable read-only `services/api/app/monitoring_source_batch_preflight.py` contract and focused test. It re-hashes actual files, rejects symlinks/missing paths/size or SHA drift, exact-class mismatches, unconfirmed/provenance-incomplete rows, duplicate content, and fewer than two distinct eligible batches per project. Module SHA `3aaa62ba0e64ba733f423d86553ac5fe889b5f3b185e9734a4422ac5665f374e`; test SHA `4c8504de6a8824cc75b5ffecadc01494d3e8e8be828eafd2732e3f488fa05523`.
- 2026-08-03: Applied the contract to the current explicit batch rows: status `blocked`, 0 eligible promoted batches for each canonical project, 14 issues, and all authority flags false. The stricter result corrects the earlier planning shorthand that counted MG-K10's unpromoted `raw_locked_snapshot_candidate` as one eligible batch.
- 2026-08-03: Added the bounded approved-input/source-batch binding entrypoint
  `dry_run_approved_input_with_source_preflight`. It requires a package-hash-covered
  `source_batch_bindings` list, reconstructs typed records and reopens actual files through
  source preflight. The current formal package has no such binding, so the controlled result
  is blocked with 15 issues; focused regression 15 passed. No runtime or source state changed.
