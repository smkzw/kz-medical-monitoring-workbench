# Task Context: medical_monitoring_protocol_version_identity_20260806

Created: 2026-08-06 07:22:56; completed: 2026-08-06 (Asia/Shanghai)
Objective: 防止方案准备面板在缺失或重复 `protocol_version_id` 时发生 React key 与版本选择碰撞，并对歧义方案版本提供只读阻断
Task type: `code_scoped_patch_plan`
Risk: `high`
Selected route: direct Codex; no delegated agent/provider/browser/runtime

## Trigger Reason

Static review found that confirmed protocol versions were filtered/sorted but not identity-checked. The panel keyed options by `protocol_version_id` and could expose the same ID more than once or render a missing ID as if it were selectable.

## Source Of Truth

- `frontend/src/features/medical-monitoring/medicalMonitoringProtocolPreparation.mjs`
- `frontend/src/features/medical-monitoring/MedicalMonitoringProtocolPreparationPanel.jsx`
- `frontend/src/features/medical-monitoring/medicalMonitoringProtocolPreparation.test.mjs`
- `tests/test_frontend_monitoring_contract.py`
- Gate: `records/active_slices/medical_monitoring_real_loop_gate_audit_20260804/CURRENT_REAL_LOOP_GATE_AUDIT.json`

## Scope

- In scope: confirmed-version display identity metadata, unique option keys, and fail-closed selection for missing/duplicate protocol version IDs.
- Out of scope: protocol source repair, version deduplication, protocol-content interpretation, API/backend/database/CAS changes, authorization, provider/runtime/browser/Playwright/API login, real-project execution, B6/C14/P8/Safety-PV and medical-writing surfaces.

## Success Criteria

- Missing/duplicate confirmed-version rows remain visible with explicit identity warning and cannot become `selectedVersionId`.
- A unique confirmed version retains existing selection, status polling and downstream preparation behavior.
- Display keys do not enter API payloads or replace the persisted version identity.
- Focused/full offline tests, Vite build, protected-shell hashes and stopped-port checks pass; review-gate accepts the evidence.

## Risk Boundaries

- Current real-loop gate remains `read_only / blocked`; `activation_allowed=false`, `provider_call_permitted=false`, `runtime_activation_permitted=false`, `write_permitted=false`.
- Do not start 8911, 5174, 8910 or 4173; do not run provider, browser, API login, real projects, SQLite/B6/C14 or Safety/PV flows.
- `displayIdentityState`, `displaySourceIndex` and `displayKey` are UI reconciliation metadata only. They do not prove protocol-source identity or factual correctness.
- Codex is final authority for verification; no delegated-agent output was used.

## Timeout Policy

- This bounded offline slice uses deterministic Node/Python/build checks; no long-running route was launched.
- The blocked gate is a release boundary, not a test failure. Formal reviewer outcomes, source-token byte revalidation and aggregate/CAS version checks remain separate prerequisites.

## Loop Log

- 2026-08-06 07:22:56: Task initialized by `tools/hermes_workflow_guard.py init-task`.
- 2026-08-06: Confirmed-version normalization retains source index, marks `ready`/`missing`/`duplicate`, and exports a UI-only version key.
- 2026-08-06: Version selector renders ambiguous rows read-only; only one ready version may be selected automatically or manually.
- 2026-08-06: Added duplicate/missing version fixtures and static checks; verified protocol Node **32 passed**, focused monitoring/timeline Python **90 passed**, full Node **44/44**, Vite **1,956 modules transformed**, protected hashes unchanged and ports stopped.
- 2026-08-06: Review-gate accepted this offline slice; next safe work remains another feature-owned audit, not gate activation.
