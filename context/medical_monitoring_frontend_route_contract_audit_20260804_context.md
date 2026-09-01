# Task Context: medical_monitoring_frontend_route_contract_audit_20260804

Created: 2026-08-04 14:09:07
Objective: 逐面对照医学监查前端读取路径与后端 fail-closed 路由，修复仍将读取失败吞成空态的入口并完成离线契约验证
Task type: `code_open_audit`
Risk: `high`
Selected agent route: `codex` / `codex-main` / `high`

## Trigger Reason

This task was initialized through the Codex x Hermes complex-task entrypoint because it is expected to involve more than three execution steps, research/writing/report/code/report-visual work, or source-grounded verification.

## Source Of Truth

- `frontend/src/App.jsx`: all medical-monitoring fetch paths, page props, fallback/empty/error handling and route selection.
- `services/api/app/main.py`: canonical/reference monitoring GET route declarations and fail-closed responses.
- `services/api/app/monitoring_identity_authorization.py` and `monitoring_read_action_contract.py`: explicit read-action and route-context contracts.
- `frontend/tests/monitoring_*` and `tests/test_monitoring*`: existing static and backend contract expectations.

## Scope

- In scope: inventory every medical-monitoring frontend read surface, compare it with the backend fail-closed contract, repair connected silent-empty or stale-fallback paths, and add deterministic source/build checks.
- Out of scope: backend route activation, authentication, runtime/provider/browser startup, API login, Playwright, real projects, B6/C14, database or production-path writes.

## Success Criteria

- A bounded inventory maps each medical-monitoring read endpoint to its frontend state/error surface and backend fail-closed contract.
- Any in-scope silent-empty path is repaired or recorded as an explicit, justified residual risk.
- A pure static contract test and production build pass; reserved ports remain stopped; review-gate is green.

## Risk Boundaries

- Do not write to production paths until Codex review gate passes and writable paths are explicit.
- The delegated agent is not final authority; Codex owns verification and acceptance.

## Timeout Policy

- Do not mark the delegated agent failed for slow response alone.
- For complex or artifact-heavy work, wait and poll generously; use conference mode when multiple independent model perspectives are needed.
- Failure requires terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.

## Loop Log

- 2026-08-04 14:09:07: Task initialized by `tools/hermes_workflow_guard.py init-task`.
- 2026-08-04: Endpoint/state inventory found three connected gaps beyond 5.105: risk taxonomy and initial-risk focus catches silently cleared state; risk evidence preview's outer Promise catch cleared previews without an error; the MonitoringPage risk header/checklist/rollup could show `0` or an empty grid while the snapshot read had failed. Assurance and batch parent workspaces also retained stale task data after non-shape read failures.
- 2026-08-04: Repaired those paths. Risk counts now use `—` on read failure; checklist hides pagination and says “风险数量未读取”; scope summary hides its empty grid; taxonomy/focus/raw/evidence errors are visible; assurance/batch non-Abort failures clear stale state. Added `READ_SURFACE_INVENTORY.md` and extended the pure static contract.
- 2026-08-04: Final audit found two remaining connected stale/ambiguous paths: raw-intake failure left prior project facts mounted, and source-manifest failure or cross-project response silently collapsed the monitoring route into generic “module not configured”. Raw facts now clear on read start/failure and display `—`; source-manifest failures are held per project and render a dedicated unavailable page. Static assertions cover both.
- 2026-08-04: Final offline verification passed: static unavailable/read-route contract, 31/31 medical-monitoring pure Node files and production build. Reserved ports 8911/5174/8910/4173 are stopped. This slice is accepted; runtime, browser, real-project, B6/C14 and controlled-runtime gates remain open.

## Loop Contract

- **Hypothesis:** the previous dashboard/inbox/AI patch may not cover auxiliary monitoring reads or route aliases; a complete endpoint-to-state inventory will reveal remaining misleading fallbacks.
- **Action:** search endpoint strings and backend routes, inspect each catch/shape/identity branch, then apply only connected fixes and add deterministic assertions.
- **Observation:** endpoint inventory, state mutation, error-state propagation, identity checks, pure test/build results.
- **Evaluation:** no failure path may silently claim no clinical data; any fallback must be an intentional non-clinical UI fallback with a visible boundary.
- **Decision:** continue, repair, or record residual risk; do not infer runtime acceptance from source-only evidence.
