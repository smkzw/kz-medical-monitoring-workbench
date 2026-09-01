# Task Context: medical_monitoring_scope_summary_20260803

Created: 2026-08-03 20:39:39
Objective: 在医学监查主页面增加只读、fail-closed 的项目/中心/受试者风险摘要与一键聚焦，消费现有显式 risk rollup，不改变风险事实、处置、运行库或 B6/C14 权威门
Task type: `finite_code_task`
Risk: `medium`
Selected agent route: `opencode-go` / `deepseek-v4-flash` / `max`

## Trigger Reason

This task was initialized through the Codex x Hermes complex-task entrypoint because it is expected to involve more than three execution steps, research/writing/report/code/report-visual work, or source-grounded verification.

## Source Of Truth

- `services/api/app/medical_monitoring_summary.py` (`_risk_rollup` contract and explicit trial/site/subject fields).
- `frontend/src/App.jsx` (`MonitoringPage` risk index, scope routing and current checklist surface).
- `frontend/src/features/medical-monitoring/medicalMonitoringModels.mjs` (risk row normalization conventions).
- `docs/medical_monitoring_manual/医学监查子系统_PRD审阅与差距矩阵.md` sections 2.4, 2.5 and 8 (compact checklist, graphical subject/site/trial drilldown, no inferred facts).
- `records/active_slices/medical_monitoring_goal_p10_20260730/RELEASE_GATE_AUDIT_20260802.md` (current release gap: project/site/subject rollup is partial; runtime evidence remains unproven).
- `AGENTS.md` (workspace execution, evidence and editing constraints).

## Scope

- In scope: a new isolated frontend model/component/CSS surface for a compact read-only risk rollup summary; project/trial, explicit site rows and explicit subject rows; one-click scope focus callbacks; malformed/missing payload warning; focused Node tests and frontend build/lint/compile checks; task/review evidence.
- Out of scope: risk facts, dispositions, unread state, backend/API/database/runtime changes; B6/C14/aggregate/CAS gates; source classification or real project onboarding; service startup, browser/Playwright acceptance, provider calls, and medical conclusions; modifications to medical-writing surfaces.

## Success Criteria

- Only explicit integer counts and non-empty string scope IDs are displayed; malformed level payloads are visibly blocked rather than coerced or invented.
- Trial/site/subject summaries are visible on the main medical-monitoring page, with bounded row counts and clear “not evidence of no risk” language where coverage is incomplete.
- Clicking an explicit site/subject row invokes the existing route/scope callback and does not mutate risk state.
- New model/component tests pass; existing medical-monitoring Node tests and frontend build/lint/compile pass.
- No listener is started and no authoritative monitoring state or protected medical-writing file is modified.

## Risk Boundaries

- Edits are limited to the workbench frontend feature directory, `App.jsx` import/mount seam, and task evidence files.
- Do not use string/number coercion for counts, infer site/subject identity from risk text, or represent missing data as zero.
- The component is read-only and must remain safe when the risk snapshot is empty, loading, or malformed.
- The delegated agent is not final authority; Codex owns verification and acceptance.

## Timeout Policy

- Do not mark the delegated agent failed for slow response alone.
- For complex or artifact-heavy work, wait and poll generously; use conference mode when multiple independent model perspectives are needed.
- Failure requires terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.

## Loop Log

- 2026-08-03 20:39:39: Task initialized by `tools/hermes_workflow_guard.py init-task`.
- 2026-08-03 20:45:00: Added read-only scope summary model/component/CSS and mounted it at the existing monitoring page seam; no backend/runtime or protected medical-writing files changed.
- 2026-08-03 20:46:00: Focused model and all 24 medical-monitoring Node files passed; Vite build passed after correcting an explicit `.jsx` import; all four guarded ports remained empty.
