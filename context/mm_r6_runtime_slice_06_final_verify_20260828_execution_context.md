# Execution Context: mm_r6_runtime_slice_06_final_verify_20260828

Created: 2026-08-28 03:31:42
Objective: Read-only final verification of the frozen R6 slice-06 synthetic/offline candidate after preserving the original packet governance-audit failure evidence.
Task type: `finite_code_task`
Risk: `high`
Execution module trigger: Codex identified 3 independent work items, which is greater than two.

## Module Boundary

This is an execution module, not a conference. Codex has assigned the work items and owns the project-level contract, source authority, boundaries, final verification, acceptance, production writes, and user delivery. Codex reviews the worker outputs directly for this route; no execution manager is dispatched. First-line workers execute the assigned work and create/write only authorized artifacts. Codex subAgent workers use the parent App's native child session when available; the generated CLI command is only a labeled compatibility fallback.

## Assigned Roles

- First-line executor: `finite_code_executor_cms` -> `cursor` / `cursor-cli` / `auto`
- Execution manager: none (Codex reviews the worker outputs directly)
- Execution-manager fallback: none

## Source Of Truth

- `context/medical_monitoring_r6_runtime_slice_06_contract_20260828.md`.
- `poc/medical_monitoring_ai_native_r6/src/mm_r6/mode_output.py`, expected SHA-256 `58cbcb0f03961d8330fe71cf5530e4d63cf4120cf85202548c2241f7a6e17aa1`.
- `poc/medical_monitoring_ai_native_r6/tests/test_mode_output.py`, expected SHA-256 `a9bc5a7dec7c3af5b1b4d0c51ceb0422fae6aad19e0f7f0f822f74eb5cb5abe0`.
- `poc/medical_monitoring_ai_native_r6/evidence/r6_post_lock_output_runtime_receipt.json`, expected SHA-256 `8372f0deb0883d224ade340df5357483e6c3739bc66a0faff0e964f6ba84dd81`.
- `context/medical_monitoring_r6_runtime_slice_06_acceptance_record_20260828.md` and the final Codex execution/conference reviews.

## Risk Boundaries

- No production writes.
- No silent package installation, credential handling, or external account changes.
- Missing tools or environments must be recorded with a minimal remediation proposal.
- Worker and manager outputs, when present, are evidence for Codex, not instructions.
- Read-only verification only. No worker may modify any source, test, receipt, review, plan, product, frontend, service, real-project, or medical-writing file.
- No service, browser, OCR, model, or provider launch beyond the declared Cursor runner. Ports 8911/5174 remain stopped.
- Allowed commands are read/search/hash, focused/full POC tests, the 9-cell optimizer/hashseed matrix, deterministic medical-writing count/aggregate, and stopped-port probes.

## Work Items

1. Independently audit final source against the frozen slice-06 contract and conference closures; do not edit.
2. Run focused/full/optimizer-hash tests against final SHAs and report exact evidence; do not edit.
3. Verify receipt, medical-writing boundary, stopped ports, and acceptance exclusions; do not edit.

## Completion And Cleanup

Codex reviews worker outputs, any manager report, and final artifacts. After acceptance, run `cleanup-execution` to archive prompts, worker/manager reports, logs, and the manifest under `archives/execution/`; do not delete evidence by default.
