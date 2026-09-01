# Task Context: medical_monitoring_scope_summary_identity_20260806

Created: 2026-08-06 06:10:41
Objective: 为项目/中心/个例范围汇总建立重复 scope_id 的只读身份防碰撞契约，禁止歧义行错误聚焦并完成离线验证
Task type: `code_scoped_patch_plan`
Risk: `high`
Selected agent route: `codex` / `codex-main` / `high`

## Trigger Reason

This task was initialized through the Codex x Hermes complex-task entrypoint because it is expected to involve more than three execution steps, research/writing/report/code/report-visual work, or source-grounded verification.

## Source Of Truth

- `frontend/src/features/medical-monitoring/medicalMonitoringScopeSummary.mjs`
- `frontend/src/features/medical-monitoring/MedicalMonitoringScopeSummary.jsx`
- `frontend/src/features/medical-monitoring/medicalMonitoringScopeSummary.test.mjs`
- `tests/test_frontend_monitoring_contract.py`
- Current real-loop gate: `records/active_slices/medical_monitoring_real_loop_gate_audit_20260804/CURRENT_REAL_LOOP_GATE_AUDIT.json` (read-only/blocked; no runtime activation)

## Scope

- In scope: detect duplicate center/subject `scope_id` values in the read-only summary model; expose a deterministic display-only React key; prevent ambiguous rows from offering a focus action; add offline regressions/static contract.
- Out of scope: backend/API schema changes, risk identity rewriting, source-data repair, medical conclusion changes, shared App shell, runtime/provider/browser/real-project execution, P8 authority selection, B6/C14 or commercial gate.

## Success Criteria

- Duplicate `scope_id` rows are marked partial/ambiguous and included in an explicit issue message.
- Ambiguous rows remain visible with their explicit counts but cannot focus Checklist; missing IDs retain the existing no-focus behavior.
- Display keys are unique and UI-only; no server or clinical identity is inferred.
- Focused Node, monitoring/timeline Python, full Node, and Vite checks pass; protected shared shell hashes remain unchanged; all runtime ports remain stopped.

## Risk Boundaries

- Only feature-owned source/tests and task evidence paths may change; do not write production data or start services.
- This is an offline display-safety repair, not evidence that the real loop or clinical/scientific acceptance is complete.
- Codex remains final authority; no delegated provider was used.

## Timeout Policy

- Do not mark the delegated agent failed for slow response alone.
- For complex or artifact-heavy work, wait and poll generously; use conference mode when multiple independent model perspectives are needed.
- Failure requires terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.

## Loop Log

- 2026-08-06 06:10:41: Task initialized by `tools/hermes_workflow_guard.py init-task`.
- 2026-08-06 06:11-06:14: Audited scope summary; confirmed duplicate `scope_id` could collide React keys and focus targets.
- 2026-08-06 06:14-06:16: Added duplicate-identity detection, display-only row key, and no-focus UI state; added Node/static regressions.
- 2026-08-06 06:16: Focused Node and Python contracts passed; Vite build passed; runtime ports remained stopped.
