# Task Context: medical_monitoring_risk_history_trend_20260803

Created: 2026-08-03 20:49:15
Objective: 在医学监查风险证据历史页增加只读、fail-closed 的跨批次风险级别/变化趋势条，消费既有 history.instances，不改变风险事实、处置或运行库
Task type: `finite_code_task`
Risk: `medium`
Selected agent route: `opencode-go` / `deepseek-v4-flash` / `max`

## Trigger Reason

This task was initialized through the Codex x Hermes complex-task entrypoint because it is expected to involve more than three execution steps, research/writing/report/code/report-visual work, or source-grounded verification.

## Source Of Truth

- `frontend/src/App.jsx` (`RiskHistoryView` and existing `history.instances` consumer).
- `services/api/app/main.py` (`/monitoring/risks/{risk_key}/history` response and explicit `change_reason`/snapshot lineage).
- `frontend/src/features/medical-monitoring/medicalMonitoringModels.mjs` (risk severity/status display conventions).
- `docs/medical_monitoring_manual/医学监查子系统_PRD审阅与差距矩阵.md` sections 2.4, 2.5 and 8 (trend visibility, source-first evidence and release boundary).
- `AGENTS.md` (workspace execution, evidence and editing constraints).

## Scope

- In scope: a new isolated frontend history-trend normalizer/component/CSS surface; strict explicit severity/batch/status/date consumption; compact trend strip mounted above the existing complete history table; focused and full Node/build checks; task/review evidence.
- Out of scope: backend/API/history response changes; risk facts, dispositions, unread state, source fragments, B6/C14/aggregate/CAS gates; clinical causal inference; service/browser/provider/real-project execution; medical-writing surfaces.

## Success Criteria

- History points are ordered by explicit parseable snapshot time; invalid or absent time never fabricates order and remains visible as a partial warning.
- Severity direction is derived only from explicit known severity ranks, labelled as a display trend and explicitly not a clinical conclusion.
- Malformed boolean/collection/field shapes do not enter the trend calculation; the original table remains available for audit.
- New model/component compiles; focused model test, all medical-monitoring Node tests and Vite build pass.
- No runtime listener or authoritative monitoring state is changed.

## Risk Boundaries

- Edits are limited to the workbench frontend feature directory, the existing `App.jsx` import/mount seam and task evidence files.
- Do not describe an upward/downward severity rank as efficacy, safety causality or a medically resolved risk.
- Do not hide malformed historical instances without a visible warning; do not substitute current source content for historical evidence.
- The delegated agent is not final authority; Codex owns verification and acceptance.

## Timeout Policy

- Do not mark the delegated agent failed for slow response alone.
- For complex or artifact-heavy work, wait and poll generously; use conference mode when multiple independent model perspectives are needed.
- Failure requires terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.

## Loop Log

- 2026-08-03 20:49:15: Task initialized by `tools/hermes_workflow_guard.py init-task`.
- 2026-08-03 20:49:30: Implemented strict history-trend normalizer/component/CSS and mounted it above the existing risk history table; no backend or runtime files changed.
- 2026-08-03 20:50:30: Focused trend test passed after correcting its malformed-entry expectation; full medical-monitoring Node suite passed and Vite build passed with the existing chunk warning.
