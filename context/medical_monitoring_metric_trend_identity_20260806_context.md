# Task Context: medical_monitoring_metric_trend_identity_20260806

Created: 2026-08-06 06:56:20
Objective: 防止 Patient Profile 疗效/安全性趋势指标缺失或重复 metric_key/metric_label 时发生图表 React key 碰撞，并把指标身份异常以只读方式明确呈现
Task type: `code_scoped_patch_plan`
Risk: `high`
Selected agent route: `codex` / `codex-main` / `high`

## Trigger Reason

Static audit of Patient Profile efficacy/safety trend rendering found a real identity boundary: chart-grid keys used `metric_key || metric_label` directly, so missing or duplicate metric identities could collapse separate trend charts.

## Source Of Truth

- `frontend/src/features/medical-monitoring/medicalMonitoringSubjectModels.mjs`
- `frontend/src/features/medical-monitoring/MedicalMonitoringSubjectViews.jsx`
- `frontend/src/features/medical-monitoring/medicalMonitoringSubjectModels.test.mjs`
- `tests/test_frontend_monitoring_contract.py`
- Current read-only gate: `records/active_slices/medical_monitoring_real_loop_gate_audit_20260804/CURRENT_REAL_LOOP_GATE_AUDIT.json`

## Scope

- In scope: display-only trend-metric identity metadata, unique chart-grid keys, and explicit missing/duplicate identity copy.
- Out of scope: source/profile mutation, metric interpretation, statistical or clinical conclusions, backend/API changes, runtime/provider/browser/real-project execution, B6/C14/P8/Safety-PV and medical-writing surfaces.

## Success Criteria

- Missing/duplicate trend metric rows remain visible and never collide in the chart grid.
- The chart identifies identity anomalies as review-only and does not infer or confirm a metric.
- Numeric/date plotting and raw point inspection behavior remain unchanged.
- Focused/full offline tests, Vite build, protected-shell hashes and stopped-port checks pass.

## Risk Boundaries

- Do not write to production paths until Codex review gate passes and writable paths are explicit.
- The delegated agent is not final authority; Codex owns verification and acceptance.

## Timeout Policy

- Do not mark the delegated agent failed for slow response alone.
- For complex or artifact-heavy work, wait and poll generously; use conference mode when multiple independent model perspectives are needed.
- Failure requires terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.

## Loop Log

- 2026-08-06 06:56:20: Task initialized by `tools/hermes_workflow_guard.py init-task`.
- 2026-08-06: Added `metricDisplayRows` display-only metadata and switched efficacy/safety chart keys to namespaced source-index keys; TrendSparkline now exposes missing/duplicate metric identity copy.
- 2026-08-06: Verified Subject-model Node, focused monitoring/timeline Python **85**, full Node **44/44**, Vite **1,956 modules**, protected hashes and stopped ports.
