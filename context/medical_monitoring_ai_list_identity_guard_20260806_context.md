# Task Context: medical_monitoring_ai_list_identity_guard_20260806

Created: 2026-08-06 04:53:46
Objective: 补齐日常医学监查运行列表响应的 project_id 身份守卫，防止跨项目列表进入当前面板；仅做离线前端合同、测试与记录，不启动运行时
Task type: `finite_code_task`
Risk: `high`
Selected agent route: `alibaba` / `qwen3.8-max` / `xhigh`

## Trigger Reason

This task was initialized through the Codex x Hermes complex-task entrypoint because it is expected to involve more than three execution steps, research/writing/report/code/report-visual work, or source-grounded verification.

## Source Of Truth

- `services/api/app/monitoring_daily_run_router.py` (`GET /api/projects/{project_id}/monitoring/daily-runs`)
- `services/api/app/monitoring_daily_run_repository.py` (`MonitoringDailyRun.to_dict()`)
- `frontend/src/features/medical-monitoring/medicalMonitoringDailyRunView.mjs`
- `frontend/src/features/medical-monitoring/MedicalMonitoringDailyRunPanel.jsx`
- `frontend/src/features/medical-monitoring/medicalMonitoringDailyRunView.test.mjs`
- `frontend/src/features/medical-monitoring/medicalMonitoringProjectSwitchIsolation.test.mjs`
- `tests/test_frontend_monitoring_contract.py`
- Current real-loop gate: `records/active_slices/medical_monitoring_real_loop_gate_audit_20260804/CURRENT_REAL_LOOP_GATE_AUDIT.json` (read-only, blocked)

## Scope

- In scope: strict client-side normalization of the existing list response identity, item/active/baseline project binding, panel call-site binding, focused/static tests, and durable evidence records.
- Out of scope: backend schema or persistence changes, provider/model calls, service startup, browser/Playwright login, real-project data, SQLite/CAS/B6/C14 activation, and visual/runtime acceptance.

## Success Criteria

- A list response is accepted only when the expected project identity is present and the top-level project, every returned run item, active run, and current baseline (when present) are project-matched.
- Missing or mismatched identity fails closed with an explicit user-facing error and cannot enter panel state.
- Focused Node tests, static Python contract tests, full frontend tests, and a production build pass; all required ports remain stopped.
- Review gate is `ok: true`; residual runtime and medical acceptance remain explicitly blocked by the current gate.

## Risk Boundaries

- Do not write to production paths until Codex review gate passes and writable paths are explicit.
- The delegated agent is not final authority; Codex owns verification and acceptance.
- This is a direct Codex implementation slice; no external agent/provider is dispatched because the current real-loop gate prohibits provider/runtime activation and the system instruction disables proactive subagent dispatch.

## Timeout Policy

- Do not mark the delegated agent failed for slow response alone.
- For complex or artifact-heavy work, wait and poll generously; use conference mode when multiple independent model perspectives are needed.
- Failure requires terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.

## Loop Log

- 2026-08-06 04:53:46: Task initialized by `tools/hermes_workflow_guard.py init-task`.
