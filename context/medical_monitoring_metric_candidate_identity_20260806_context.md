# Task Context: medical_monitoring_metric_candidate_identity_20260806

Created: 2026-08-06 06:52:41
Objective: 防止 Patient Profile 指标配置候选缺失或重复 candidate_id/metric_key 时发生 React key 碰撞，并让待核对身份在只读候选区明确可见
Task type: `code_scoped_patch_plan`
Risk: `high`
Selected agent route: `codex` / `codex-main` / `high`

## Trigger Reason

Static audit of the Patient Profile metric-candidate review found a real evidence-preservation gap: the read-only card keyed rows by `candidate_id || metric_key` without distinguishing missing or duplicate identities.

## Source Of Truth

- `frontend/src/features/medical-monitoring/medicalMonitoringMetricConfiguration.mjs`
- `frontend/src/features/medical-monitoring/MedicalMonitoringSubjectViews.jsx`
- `frontend/src/features/medical-monitoring/medicalMonitoringMetricConfiguration.test.mjs`
- `tests/test_frontend_monitoring_contract.py`
- Current read-only gate: `records/active_slices/medical_monitoring_real_loop_gate_audit_20260804/CURRENT_REAL_LOOP_GATE_AUDIT.json`

## Scope

- In scope: read-only metric-candidate identity normalization, display-only keys, and explicit missing/duplicate identity copy.
- Out of scope: metric confirmation, rule release, source repair, backend/API changes, clinical interpretation, runtime/provider/browser/real-project execution, B6/C14/P8/Safety-PV and medical-writing surfaces.

## Success Criteria

- Missing/duplicate candidate identities remain visible and never collide in React.
- The card labels the identity as pending/duplicate without implying confirmation or release.
- Candidate-only and medical-confirmation semantics remain unchanged.
- Focused/full offline tests, Vite build, protected-shell hashes and stopped-port checks pass.

## Risk Boundaries

- Do not write to production paths until Codex review gate passes and writable paths are explicit.
- The delegated agent is not final authority; Codex owns verification and acceptance.

## Timeout Policy

- Do not mark the delegated agent failed for slow response alone.
- For complex or artifact-heavy work, wait and poll generously; use conference mode when multiple independent model perspectives are needed.
- Failure requires terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.

## Loop Log

- 2026-08-06 06:52:41: Task initialized by `tools/hermes_workflow_guard.py init-task`.
- 2026-08-06: Candidate normalization now retains source index, marks effective `candidate_id || metric_key` identity as ready/missing/duplicate, and exposes a display-only key; the Patient Profile card uses it and shows explicit blocker copy.
- 2026-08-06: Focused metric Node **18**, focused monitoring/timeline Python **84**, full Node **44/44**, Vite **1,956 modules**, protected hashes and stopped ports verified. An initial build call from the workbench root was corrected by rerunning from `frontend/`.
