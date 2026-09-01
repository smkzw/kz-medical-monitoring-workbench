# Task Context: medical_monitoring_assurance_task_identity_20260806

Created: 2026-08-06 07:03:44; completed: 2026-08-06 (Asia/Shanghai)
Objective: 防止保障任务列表在重复 `task_id` 时发生 React key/选中态碰撞，并对歧义任务提供只读阻断
Task type: `code_scoped_patch_plan`
Risk: `high`
Selected route: direct Codex; no delegated agent/provider/browser/runtime

## Trigger Reason

Static review found that the assurance task list used `key={task.id}` and allowed a duplicate task identity to remain selectable. A duplicate could visually collide, change the active selection unexpectedly, or route a review action to an ambiguous task. The smallest safe fix is a display-only identity guard, not task deduplication or source repair.

## Source Of Truth

- `frontend/src/features/medical-monitoring/medicalMonitoringAssurance.mjs`
- `frontend/src/features/medical-monitoring/MedicalMonitoringAssurancePanel.jsx`
- `frontend/src/features/medical-monitoring/medicalMonitoringAssurance.test.mjs`
- `tests/test_frontend_monitoring_contract.py`
- Gate: `records/active_slices/medical_monitoring_real_loop_gate_audit_20260804/CURRENT_REAL_LOOP_GATE_AUDIT.json`

## Scope

- In scope: task-list normalization, duplicate identity state, display-only source-index keys, and fail-closed selection for ambiguous rows.
- Out of scope: task deduplication, task status/count policy, backend/API/schema/database/CAS changes, audit-source repair, authorization, provider or runtime activation, browser/Playwright login, real-project execution, B6/C14/P8/Safety-PV and medical-writing surfaces.

## Success Criteria

- Every task row remains visible and retains its source order.
- Missing/duplicate task identities are explicit, read-only, and cannot become the active task.
- A unique task keeps its existing selection/details behavior.
- No candidate/approval/status semantics change.
- Focused and full offline tests, Vite build, protected-shell hashes and stopped-port checks pass; review-gate accepts the evidence.

## Risk Boundaries

- Current real-loop gate remains `read_only / blocked`; `activation_allowed=false`, `provider_call_permitted=false`, `runtime_activation_permitted=false`, `write_permitted=false`.
- Do not start 8911, 5174, 8910 or 4173; do not run provider, browser, API login, real projects, SQLite/B6/C14 or Safety/PV flows.
- `identityState` and `assuranceTaskDisplayKey` are UI reconciliation metadata only. They do not assert source truth, repair identifiers, deduplicate tasks, or establish clinical/medical correctness.
- Codex is final authority for verification; no delegated-agent output was used.

## Timeout Policy

- This bounded offline slice uses direct deterministic checks; no long-running route was launched.
- Do not interpret unchanged external state or the blocked gate as a failure. Release requires the separate formal reviewer/source-token/CAS outcomes described by the gate.

## Loop Log

- 2026-08-06 07:03:44: Task initialized by `tools/hermes_workflow_guard.py init-task`.
- 2026-08-06: Added duplicate task identity metadata and UI-only display keys; duplicate rows are visible but disabled with explicit read-only copy.
- 2026-08-06: Added adversarial duplicate fixture and static contract; valid task selection remains covered.
- 2026-08-06: Verified assurance Node contract **46 passed**, focused monitoring/timeline Python **87 passed**, full Node **44/44**, Vite **1,956 modules transformed**, protected hashes unchanged and mandated ports stopped.
- 2026-08-06: Review-gate accepted this offline slice; next safe work is another feature-owned identity/source-locator audit, not gate activation.
