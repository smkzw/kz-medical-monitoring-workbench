# Task Context: medical_monitoring_subject_catalog_identity_20260806

Created: 2026-08-06 07:10:25; completed: 2026-08-06 (Asia/Shanghai)
Objective: 防止 Patient Profile / Subject Timeline 受试者目录在缺失或重复 `subject_id` 时发生 React key 与选中态碰撞，并对歧义目录项提供只读阻断
Task type: `code_scoped_patch_plan`
Risk: `high`
Selected route: direct Codex; no delegated agent/provider/browser/runtime

## Trigger Reason

Static review found that the Profile/TL catalog select, segmented switcher and center/subject tree keyed rows by `item.id` and allowed every row to call `setSelectedSubject`. A missing or duplicate subject identity could therefore collide in rendering or make a single string route to more than one source row.

## Source Of Truth

- `frontend/src/features/medical-monitoring/medicalMonitoringSubjectModels.mjs`
- `frontend/src/features/medical-monitoring/MedicalMonitoringSubjectViews.jsx`
- `frontend/src/features/medical-monitoring/medicalMonitoringSubjectModels.test.mjs`
- `tests/test_frontend_monitoring_contract.py`
- Gate: `records/active_slices/medical_monitoring_real_loop_gate_audit_20260804/CURRENT_REAL_LOOP_GATE_AUDIT.json`

## Scope

- In scope: display-only catalog identity normalization, unique source-index keys, explicit missing/duplicate copy, and fail-closed selection in Profile/TL catalog controls and center tree.
- Out of scope: source catalog repair/deduplication, subject profile fetch/API/route schema changes, backend/database/CAS, clinical interpretation, authorization, provider/runtime/browser/Playwright/API login, real-project execution, B6/C14/P8/Safety-PV and medical-writing surfaces.

## Success Criteria

- Every source catalog row remains visible and retains source order.
- A missing/duplicate identity is explicit, read-only and cannot become the selected subject.
- A unique `id` or `subject_id` remains selectable through the existing callback path.
- No profile values, route payloads, risk counts or medical conclusions change.
- Focused/full offline tests, Vite build, protected-shell hashes and stopped-port checks pass; review-gate accepts the evidence.

## Risk Boundaries

- Current real-loop gate remains `read_only / blocked`; `activation_allowed=false`, `provider_call_permitted=false`, `runtime_activation_permitted=false`, `write_permitted=false`.
- Do not start 8911, 5174, 8910 or 4173; do not run provider, browser, API login, real projects, SQLite/B6/C14 or Safety/PV flows.
- `displayIdentityState`, `displayKey` and `displaySubjectId` are UI reconciliation metadata only. They do not rewrite source IDs or prove the server/catalog identity.
- Codex is final authority for verification; no delegated-agent output was used.

## Timeout Policy

- This bounded offline slice uses deterministic Node/Python/build checks; no long-running route was launched.
- The blocked gate is a release boundary, not a test failure. Formal reviewer outcomes, source-token byte revalidation and aggregate/CAS version checks remain separate prerequisites.

## Loop Log

- 2026-08-06 07:10:25: Task initialized by `tools/hermes_workflow_guard.py init-task`.
- 2026-08-06: Added catalog identity metadata, namespaced display keys and valid-only selection guards in the three subject-navigation surfaces.
- 2026-08-06: Added duplicate/missing/subject_id-only fixtures and static checks; existing valid rows remain selectable.
- 2026-08-06: Verified Subject-model Node test, focused monitoring/timeline Python **88 passed**, full Node **44/44**, Vite **1,956 modules transformed**, protected hashes unchanged and mandated ports stopped.
- 2026-08-06: Review-gate accepted this offline slice; next safe work remains another feature-owned audit, not gate activation.
