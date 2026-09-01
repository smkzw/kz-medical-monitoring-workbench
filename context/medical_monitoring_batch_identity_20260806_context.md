# Task Context: medical_monitoring_batch_identity_20260806

Created: 2026-08-06 07:18:19; completed: 2026-08-06 (Asia/Shanghai)
Objective: 防止医学监查批次列表在重复 `batch_id` 时发生 React key 与批次选择碰撞，并对歧义批次提供只读阻断
Task type: `code_scoped_patch_plan`
Risk: `high`
Selected route: direct Codex; no delegated agent/provider/browser/runtime

## Trigger Reason

Static review found that the batch list normalized every row but rendered `key={batch.batch_id}` and passed the same ID to detail loading without checking whether it was uniquely represented. A malformed duplicate list could therefore visually collide or open an ambiguous batch detail.

## Source Of Truth

- `frontend/src/features/medical-monitoring/medicalMonitoringBatchView.mjs`
- `frontend/src/features/medical-monitoring/MedicalMonitoringBatchPanel.jsx`
- `frontend/src/features/medical-monitoring/medicalMonitoringBatchView.test.mjs`
- `tests/test_frontend_monitoring_contract.py`
- Gate: `records/active_slices/medical_monitoring_real_loop_gate_audit_20260804/CURRENT_REAL_LOOP_GATE_AUDIT.json`

## Scope

- In scope: batch-list duplicate identity metadata, UI-only source-index keys, list visibility and fail-closed duplicate selection/focus.
- Out of scope: batch ID repair/deduplication, missing-ID schema relaxation, batch state/count policy, detail/API/backend/database/CAS changes, authorization, provider/runtime/browser/Playwright/API login, real-project execution, B6/C14/P8/Safety-PV and medical-writing surfaces.

## Success Criteria

- A duplicate `batch_id` remains visible with an explicit identity warning and cannot be selected.
- Unique batches retain the existing detail-loading path and state transitions.
- Focused refresh does not silently load a duplicate ID; it leaves the list available for a valid selection.
- No batch payload, status, source proof, risk count or authority semantics change.
- Focused/full offline tests, Vite build, protected-shell hashes and stopped-port checks pass; review-gate accepts the evidence.

## Risk Boundaries

- Current real-loop gate remains `read_only / blocked`; `activation_allowed=false`, `provider_call_permitted=false`, `runtime_activation_permitted=false`, `write_permitted=false`.
- Do not start 8911, 5174, 8910 or 4173; do not run provider, browser, API login, real projects, SQLite/B6/C14 or Safety/PV flows.
- `displayIdentityState`, `displaySourceIndex` and `displayKey` are UI reconciliation metadata only. Existing missing `batch_id` shape validation remains fail-closed; this slice does not infer or repair it.
- Codex is final authority for verification; no delegated-agent output was used.

## Timeout Policy

- This bounded offline slice uses deterministic Node/Python/build checks; no long-running route was launched.
- The blocked gate is a release boundary, not a test failure. Formal reviewer outcomes, source-token byte revalidation and aggregate/CAS version checks remain separate prerequisites.

## Loop Log

- 2026-08-06 07:18:19: Task initialized by `tools/hermes_workflow_guard.py init-task`.
- 2026-08-06: Batch-list normalization retains duplicate rows with source index, duplicate identity state and display-only key; panel disables duplicate rows and rejects ambiguous focus/selection.
- 2026-08-06: Added duplicate batch fixture and static key/selection contract; unique batch selection and existing mutation path remain covered.
- 2026-08-06: Verified Batch-view Node test, focused monitoring/timeline Python **89 passed**, full Node **44/44**, Vite **1,956 modules transformed**, protected hashes unchanged and mandated ports stopped.
- 2026-08-06: Review-gate accepted this offline slice; next safe work remains another feature-owned audit, not gate activation.
