# Task Context: medical_monitoring_source_preflight_revalidation_20260803

Created: 2026-08-03 04:13:45
Objective: Add a pure read-only revalidation boundary for the persisted medical-monitoring source-batch preflight artifact; re-open its declared rows through the existing hash-bound source preflight contract, preserve fail-closed authority, and record the current blocked result without starting runtime or real LOOP.
Task type: `code_open_audit`
Risk: `medium`
Selected agent route: `codex` / `codex-main` / `high`

## Trigger Reason

This task was initialized through the Codex x Hermes complex-task entrypoint because it is expected to involve more than three execution steps, research/writing/report/code/report-visual work, or source-grounded verification.

## Source Of Truth

- `records/active_slices/medical_monitoring_real_source_batch_preflight_20260803/REAL_SOURCE_BATCH_PREFLIGHT.json`
- `services/api/app/monitoring_source_batch_preflight.py`
- `records/active_slices/medical_monitoring_approved_input_source_binding_20260803/APPROVED_INPUT_SOURCE_BINDING.json`
- Current B6/C14 evidence under `runs/execution/medical_monitoring_phase_b6_review_gate_20260801/` and `runs/execution/medical_monitoring_phase_c14_b6_activation_gate_20260802/`.
- The five supplied project roots remain source evidence only; this slice does not start a project runtime.

## Scope

- In scope: a pure persistence revalidation module/test and a diagnostic artifact for the current source-preflight envelope.
- Out of scope: source promotion, adapter registration, batch creation, B6/CAS/source-token changes, runtime/provider/browser execution, frontend, SQLite, and medical decisions.

## Success Criteria

- Reopen the persisted JSON and all declared listing files through the existing source-batch contract.
- Detect envelope drift, unsafe artifact paths, source-file byte/SHA drift, and derived-summary mismatch.
- Keep freshness separate from source admission: a fresh report may still be source-preflight blocked.
- Keep all authority flags false and preserve 8911/5174 stopped.

## Risk Boundaries

- Do not write to production paths until Codex review gate passes and writable paths are explicit.
- The delegated agent is not final authority; Codex owns verification and acceptance.

## Timeout Policy

- Do not mark the delegated agent failed for slow response alone.
- For complex or artifact-heavy work, wait and poll generously; use conference mode when multiple independent model perspectives are needed.
- Failure requires terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.

## Loop Log

- 2026-08-03 04:13:45: Task initialized by `tools/hermes_workflow_guard.py init-task`.
- 2026-08-03: Added the read-only revalidation contract and focused tests. Initial self-check exposed that excluded historical/comparison rows have no `batch_ref`; the contract was corrected to check their files without synthesizing identity.
- 2026-08-03: Added explicit `source_file_drift` propagation for missing/non-file/symlink/byte/SHA failures while leaving ordinary source-admission deficiencies as the underlying `blocked` status.
- 2026-08-03: Focused and adjacent tests passed 51/51. Current persisted artifact replay is exact and fresh; source admission remains blocked with 14 issues and no eligible promoted batch.
