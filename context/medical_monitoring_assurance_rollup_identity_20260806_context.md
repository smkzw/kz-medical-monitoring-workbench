# Task Context: medical_monitoring_assurance_rollup_identity_20260806

Created: 2026-08-06 06:59:43
Objective: 防止保障面板中心/个例汇总在缺失或重复 site_id/subject_id 时发生 React key 碰撞或歧义下钻，并保持只读对账阻断语义
Task type: `code_scoped_patch_plan`
Risk: `high`
Selected agent route: `codex` / `codex-main` / `high`

## Trigger Reason

Static audit of the pre-inspection assurance rollup found a real navigation boundary: center/subject rows were keyed by direct IDs and still offered scope/profile drill-through when IDs were missing or duplicated.

## Source Of Truth

- `frontend/src/features/medical-monitoring/medicalMonitoringAssuranceRollup.mjs`
- `frontend/src/features/medical-monitoring/MedicalMonitoringAssurancePanel.jsx`
- `frontend/src/features/medical-monitoring/medicalMonitoringAssuranceRollup.test.mjs`
- `tests/test_frontend_monitoring_contract.py`
- Current read-only gate: `records/active_slices/medical_monitoring_real_loop_gate_audit_20260804/CURRENT_REAL_LOOP_GATE_AUDIT.json`

## Scope

- In scope: assurance rollup display-only identity metadata, unique row keys, and fail-closed site/subject drill-through.
- Out of scope: backend/API rollup repair, source mutation, risk reconciliation policy, authorization, runtime/provider/browser/real-project execution, B6/C14/P8/Safety-PV and medical-writing surfaces.

## Success Criteria

- Missing/duplicate site/subject rows remain visible and are explicitly read-only.
- Only rows with a unique explicit identity can open scope/profile/timeline drill-through.
- Counts, risk-instance sets and existing conservation blocking remain unchanged.
- Focused/full offline tests, Vite build, protected-shell hashes and stopped-port checks pass.

## Risk Boundaries

- Do not write to production paths until Codex review gate passes and writable paths are explicit.
- The delegated agent is not final authority; Codex owns verification and acceptance.

## Timeout Policy

- Do not mark the delegated agent failed for slow response alone.
- For complex or artifact-heavy work, wait and poll generously; use conference mode when multiple independent model perspectives are needed.
- Failure requires terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.

## Loop Log

- 2026-08-06 06:59:43: Task initialized by `tools/hermes_workflow_guard.py init-task`.
- 2026-08-06: Rollup rows now retain display source indices, mark site/subject identity `ready`/`missing`/`duplicate`, use `assuranceRollupRowDisplayKey`, and block ambiguous drill-through with explicit read-only copy.
- 2026-08-06: Verified rollup Node **16**, focused monitoring/timeline Python **86**, full Node **44/44**, Vite **1,956 modules**, protected hashes and stopped ports.
