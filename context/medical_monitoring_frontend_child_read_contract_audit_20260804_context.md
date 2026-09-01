# Task Context: medical_monitoring_frontend_child_read_contract_audit_20260804

Created: 2026-08-04 14:35:40
Objective: 审计医学监查批次内部字段映射、方案准备、规则发布与Daily AI子面板的读取失败/旧状态/空态路径，修复连接到当前项目视图的silent-empty或stale-state并完成离线验证；不启动运行时
Task type: `code_open_audit`
Risk: `high`
Selected agent route: `codex` / `codex-main` / `high`

## Trigger Reason

This task was initialized through the Codex x Hermes complex-task entrypoint because it is expected to involve more than three execution steps, research/writing/report/code/report-visual work, or source-grounded verification.

## Source Of Truth

- `frontend/src/features/medical-monitoring/MedicalMonitoringFieldMappingPanel.jsx`
- `frontend/src/features/medical-monitoring/MedicalMonitoringProtocolPreparationPanel.jsx`
- `frontend/src/features/medical-monitoring/MedicalMonitoringRuleReleasePanel.jsx`
- `frontend/src/features/medical-monitoring/MedicalMonitoringDailyRunPanel.jsx`
- Their existing pure Node view/state tests and `medicalMonitoringProjectSwitchIsolation.test.mjs`.

## Scope

- In scope: read-failure catches, stale loaded state, auxiliary evidence/readiness/progress errors and explicit child-panel static contracts.
- Out of scope: backend/API route changes, B6/C14, source-token/CAS, runtime/provider/browser/Playwright, real projects, database, medical judgments and visual UAT.

## Success Criteria

- No in-scope read failure leaves prior mapping/protocol facts, rule-release evidence/readiness or Daily AI progress mounted without a visible boundary.
- A pure static child contract, focused child tests and production build pass; reserved ports remain stopped.

## Risk Boundaries

- Do not write to production paths until Codex review gate passes and writable paths are explicit.
- The delegated agent is not final authority; Codex owns verification and acceptance.

## Timeout Policy

- Do not mark the delegated agent failed for slow response alone.
- For complex or artifact-heavy work, wait and poll generously; use conference mode when multiple independent model perspectives are needed.
- Failure requires terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.

## Loop Log

- 2026-08-04 14:35:40: Task initialized by `tools/hermes_workflow_guard.py init-task`.
- 2026-08-04: Child audit found field-mapping initial/poll failures cleared only shape errors; protocol version/status and rule-template failures could retain old facts/payload; rule-release diff/lineage/readiness and DailyRun readiness/AI-progress failures were silently hidden.
- 2026-08-04: Repaired only connected paths: field-mapping read failures clear state; protocol reads clear stale status/versions/template payloads; rule-release auxiliary errors are visible and fail-closed; DailyRun exposes readiness/AI-progress read errors.
- 2026-08-04: Added `frontend/tests/monitoring_child_read_contract_qc.mjs`; focused child tests and build passed. No runtime was started.
