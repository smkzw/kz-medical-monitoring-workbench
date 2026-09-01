# Task Context: medical_monitoring_subject_prompt_identity_20260806

Created: 2026-08-06 07:51:47
Objective: 离线审计受试者 Patient Profile 的风险提示身份与证据可见性，保留重复/缺失提示可见并禁止歧义身份进入聚焦或业务动作；不启动运行时
Task type: `code_scoped_patch_plan`
Risk: `high`
Selected agent route: `codex` / `codex-main` / `high`

## Trigger Reason

This task was initialized through the Codex x Hermes complex-task entrypoint because it is expected to involve more than three execution steps, research/writing/report/code/report-visual work, or source-grounded verification.

## Source Of Truth

- `/Users/smkzw/Documents/康哲项目资料/AI/医学经理工作台/implementation/workbench/frontend/src/features/medical-monitoring/medicalMonitoringSubjectModels.mjs`
- `/Users/smkzw/Documents/康哲项目资料/AI/医学经理工作台/implementation/workbench/frontend/src/features/medical-monitoring/MedicalMonitoringSubjectViews.jsx`
- `/Users/smkzw/Documents/康哲项目资料/AI/医学经理工作台/implementation/workbench/frontend/src/features/medical-monitoring/medicalMonitoringSubjectModels.test.mjs`
- `/Users/smkzw/Documents/康哲项目资料/AI/医学经理工作台/implementation/workbench/tests/test_frontend_monitoring_contract.py`
- Existing Patient Profile `TimepointRiskPrompt.prompt_id` contract in `packages/contracts/workbench_contracts/models.py`.
- Current real-loop gate: `records/active_slices/medical_monitoring_real_loop_gate_audit_20260804/CURRENT_REAL_LOOP_GATE_AUDIT.json` (read-only/blocked; no runtime activation).

## Scope

- In scope: audit and repair the Patient Profile risk-prompt display identity boundary; preserve missing/duplicate prompt rows with source-order display keys and explicit read-only warnings; keep source prompt IDs and clinical values unchanged.
- Out of scope: API/schema changes, risk scoring, source parsing, focus/navigation actions, confirmation/disposition writes, real projects, browser login, providers, services, ports, SQLite/CAS, Safety/PV, and medical-writing paths.

## Success Criteria

- Every visible risk-prompt row has a collision-safe display key using prompt identity plus source index.
- Missing/duplicate `prompt_id` rows remain visible, expose an identity warning, and do not become an implicit confirmed/focusable identity.
- Focused Node and Python contracts pass; all monitoring Node tests pass; Vite production build passes; runtime ports remain stopped.

## Risk Boundaries

- Presentation-only source edits are limited to the workbench feature and its static/Node contracts; no production runtime or data-store writes.
- Do not start 8911, 5174, 8910, or 4173; do not invoke external providers, browser/API login, real-project data, or the blocked real LOOP.
- Identity metadata is display-only and must not replace `prompt_id`, create a risk instance, alter severity/status, or authorize a medical action.

## Timeout Policy

- Do not mark the delegated agent failed for slow response alone.
- For complex or artifact-heavy work, wait and poll generously; use conference mode when multiple independent model perspectives are needed.
- Failure requires terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.

## Loop Log

- 2026-08-06 07:51:47: Task initialized by `tools/hermes_workflow_guard.py init-task`.
- 2026-08-06 07:52:xx: Confirmed direct `key={prompt.prompt_id || prompt.title}` collision risk in both PD/Query and risk-prompt lists; source contract requires explicit `prompt_id`, but malformed/duplicate payloads must remain visible and fail closed for identity.
- 2026-08-06 07:53:xx: Added `riskPromptDisplayRows`/`riskPromptDisplayKey`; UI now uses source-order display keys and visible identity warnings. No API or business-action path changed.
- 2026-08-06 07:54:35: Focused Node pass, 94 Python frontend/timeline contracts, all 38 monitoring Node files, and Vite build passed; build retained existing >500 kB advisory. Ports 8911/5174/8910/4173 had no listeners.
