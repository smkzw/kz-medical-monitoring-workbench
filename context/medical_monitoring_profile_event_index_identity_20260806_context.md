# Task Context: medical_monitoring_profile_event_index_identity_20260806

Created: 2026-08-06 06:23:21
Objective: 为 Patient Profile 的 PD/Query 与事件索引建立 display-only 事件键，阻止缺失或重复 event_id 的列表碰撞
Task type: `code_scoped_patch_plan`
Risk: `high`
Selected agent route: `codex` / `codex-main` / `high`

## Trigger Reason

This task was initialized through the Codex x Hermes complex-task entrypoint because it is expected to involve more than three execution steps, research/writing/report/code/report-visual work, or source-grounded verification.

## Source Of Truth

- `frontend/src/features/medical-monitoring/MedicalMonitoringSubjectViews.jsx`
- `frontend/src/features/medical-monitoring/medicalMonitoringSubjectModels.mjs` (`timelineEventSelectionKey`)
- `tests/test_frontend_monitoring_contract.py`
- Current real-loop gate: `records/active_slices/medical_monitoring_real_loop_gate_audit_20260804/CURRENT_REAL_LOOP_GATE_AUDIT.json` (read-only/blocked; no runtime activation)

## Scope

- In scope: use the existing display-only timeline event key in Patient Profile PD/Query and source-event index lists, add list-index suffixes for duplicate explicit IDs, and add a static regression.
- Out of scope: timeline model/source identity changes, event content or risk identity changes, backend/API schema, shared App shell, runtime/provider/browser/real-project execution, P8 authority, B6/C14 or commercial gate.

## Success Criteria

- Patient Profile event index rows remain visible and uniquely keyed when `event_id` is absent or duplicated.
- The key is namespaced/display-only and never replaces event/source/risk identity.
- Focused Python, subject-model Node, full Node and Vite checks pass; protected shared shell hashes remain unchanged; ports stay stopped.

## Risk Boundaries

- Only feature-owned view/test and task evidence paths may change; no backend/source data/runtime may be changed or started.
- This is a rendering-key repair, not proof of event identity, source completeness or clinical correctness.
- Codex remains final authority; no delegated provider was used.

## Timeout Policy

- Do not mark the delegated agent failed for slow response alone.
- For complex or artifact-heavy work, wait and poll generously; use conference mode when multiple independent model perspectives are needed.
- Failure requires terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.

## Loop Log

- 2026-08-06 06:23: Audited Patient Profile event indexes and found direct `key={event.event_id}` use outside Timeline lane de-duplication.
- 2026-08-06 06:24: Reused `timelineEventSelectionKey` with per-list index suffixes; added static contract.
- 2026-08-06 06:24-06:27: Focused/full tests, Vite build and stopped-port checks passed.
