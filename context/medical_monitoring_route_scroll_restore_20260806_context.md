# Task Context: medical_monitoring_route_scroll_restore_20260806

Created: 2026-08-06 00:11:40
Objective: 补齐医学监查 Checklist 跨风险详情/Timeline/Profile 返回时的桌面滚动位置恢复，保持项目/筛选/风险身份边界，不改变医学事实、运行库、医学写作或真实 LOOP 门禁
Task type: `code_scoped_patch_plan`
Risk: `high`
Selected agent route: `codex` / `codex-main` / `high`

## Trigger Reason

This task was initialized through the Codex x Hermes complex-task entrypoint because it is expected to involve more than three execution steps, research/writing/report/code/report-visual work, or source-grounded verification.

## Source Of Truth

- docs/medical_monitoring_manual/医学监查子系统_PRD审阅与差距矩阵.md,
  P1-04 route-context requirement.
- frontend/src/features/medical-monitoring/medicalMonitoringRouteState.mjs
  and its tests.
- frontend/src/features/medical-monitoring/MedicalMonitoringRiskChecklist.jsx.
- frontend/src/App.jsx MonitoringPage and monitoring route state handoff.
- Current filesystem and deterministic frontend tests; runtime gate remains
  read-only and blocked.

## Scope

- In scope: persist a bounded desktop window scroll offset in the existing
  medical-monitoring route state and restore it when returning to Checklist
  after Timeline/Profile/evidence navigation or a stable query/project context;
  add pure hook/route-state tests and update the App/Checklist wiring.
- Out of scope: medical facts, risk status, batch/source identity, API schema,
  runtime database, service/browser/provider/real-project LOOP, B6/C14,
  medical-writing sources, or lifecycle navigation.

## Success Criteria

- Invalid or excessive offsets are discarded fail-closed.
- Project, subject, risk and filter identity remain unchanged.
- Scroll updates are throttled and do not submit data or change risk state.
- Route-state, hook and adjacent monitoring tests/build pass.

## Risk Boundaries

- Do not write to production paths until Codex review gate passes and writable paths are explicit.
- The delegated agent is not final authority; Codex owns verification and acceptance.

## Timeout Policy

- Do not mark the delegated agent failed for slow response alone.
- For complex or artifact-heavy work, wait and poll generously; use conference mode when multiple independent model perspectives are needed.
- Failure requires terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.

## Loop Log

- 2026-08-06 00:11:40: Task initialized by `tools/hermes_workflow_guard.py init-task`.
- 2026-08-06 00:18:52: Implemented bounded route scroll state, browser-only
  restoration hook, App wiring, and pure tests. Node monitoring suite: 35 test
  files passed; Vite build passed. The adjacent Python static contract command
  returned 160 passed / 4 pre-existing source-group/Timeline/source-body
  failures; no failure names this slice. Review-gate passed with no warnings.
- 2026-08-06 00:18:52: Rechecked the authoritative real-loop gate: still
  `read_only / blocked`; 8911/5174/8910/4173 remain stopped. No service,
  browser, provider, API login, real project, B6/C14 or medical-writing action
  occurred. Next safe action remains formal B6 outcome submission followed by
  source-token/CAS revalidation before any runtime activation.
