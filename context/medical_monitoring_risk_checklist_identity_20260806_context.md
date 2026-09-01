# Task Context: medical_monitoring_risk_checklist_identity_20260806

Created: 2026-08-06 06:46:48
Objective: 防止医学风险 Checklist 中重复 risk_instance_id 导致证据行覆盖或歧义定位，并以只读、fail-closed 方式保留全部风险证据
Task type: `code_scoped_patch_plan`
Risk: `high`
Selected agent route: `codex` / `codex-main` / `high`

## Trigger Reason

Static audit of feature-owned risk Checklist rendering found a real evidence-preservation gap: duplicate `risk_instance_id` values could collide at the React row key and still appear selectable, making a data-sensitive reviewer unable to distinguish two source rows safely.

## Source Of Truth

- `frontend/src/features/medical-monitoring/medicalMonitoringModels.mjs`
- `frontend/src/features/medical-monitoring/MedicalMonitoringRiskChecklist.jsx`
- `frontend/src/features/medical-monitoring/medicalMonitoringModels.test.mjs`
- `tests/test_frontend_monitoring_contract.py`
- Current read-only gate: `records/active_slices/medical_monitoring_real_loop_gate_audit_20260804/CURRENT_REAL_LOOP_GATE_AUDIT.json`

## Scope

- In scope: client-side risk-row identity detection, display-only keys, evidence-preserving rendering, and fail-closed selection semantics.
- Out of scope: backend/API identity repair, source data mutation, risk deduplication, clinical judgement, authorization, runtime/provider/browser/real-project execution, B6/C14/P8/Safety-PV, and medical-writing surfaces.

## Success Criteria

- Duplicate risk rows remain visible with source order retained.
- Ambiguous rows are explicitly marked and cannot open a risk evidence/medical-action target.
- Valid rows retain existing selection behavior; display keys never become risk identity.
- Focused and full offline tests, Vite build, protected-shell hash check, and stopped-port check pass.

## Risk Boundaries

- Do not write to production paths until Codex review gate passes and writable paths are explicit.
- The delegated agent is not final authority; Codex owns verification and acceptance.

## Timeout Policy

- Do not mark the delegated agent failed for slow response alone.
- For complex or artifact-heavy work, wait and poll generously; use conference mode when multiple independent model perspectives are needed.
- Failure requires terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.

## Loop Log

- 2026-08-06 06:46:48: Task initialized by `tools/hermes_workflow_guard.py init-task`.
- 2026-08-06: Added source-index display identity and duplicate-risk anomaly fields in the risk API projection; Checklist uses display-only keys and blocks ambiguous row selection while retaining evidence.
- 2026-08-06: Verified focused Node 84 assertions, focused monitoring/timeline Python 83, full Node 44/44, Vite 1,956 modules, protected hashes unchanged, and ports 8911/5174/8910/4173 stopped.
