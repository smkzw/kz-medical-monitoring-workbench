# Task Context: medical_monitoring_checklist_empty_state_integrity_20260802

Created: 2026-08-02 11:42:12
Objective: 为医学监查风险清单补齐接口报告数量与当前页可安全展示记录不一致时的明确空态，避免把形状异常、分页漂移或数据不可读误报为无风险
Task type: `code_scoped_patch_plan`
Risk: `high`
Selected agent route: `codex` / `codex-main` / `high`

## Trigger Reason

This task was initialized through the Codex x Hermes complex-task entrypoint because it is expected to involve more than three execution steps, research/writing/report/code/report-visual work, or source-grounded verification.

## Source Of Truth

- `frontend/src/features/medical-monitoring/MedicalMonitoringRiskChecklist.jsx`
- `tests/test_frontend_unified_risk_workbench_contract.py`
- `frontend/AGENTS.md` risk checklist and fail-closed display contract
- Existing B6/C14 gate records and P10 LOOP ledger; no runtime authority is changed.

## Scope

- In scope: explicit checklist empty state when the API reports records but the current page has no safely renderable rows; focused static contract and existing frontend test/build evidence.
- Out of scope: risk facts, API pagination, backend/SQLite/runtime/provider, App.jsx/styles.css, source evidence, B6/C13, real projects, browser, and medical-writing surfaces.

## Success Criteria

- A nonzero reported total with zero safe rows is never rendered as the ordinary “no risk items” state.
- The warning states that the absence of renderable rows cannot establish absence of risk and directs refresh/shape review.
- Ordinary zero-total empty state and existing error/loading/stale snapshot behavior remain unchanged.
- Focused frontend contracts, all medical-monitoring Node tests, and Vite build pass.

## Risk Boundaries

- Do not write to production paths until Codex review gate passes and writable paths are explicit.
- Do not infer missing risk facts, repair malformed rows, coerce pagination counts, or change API/backend semantics.
- Do not modify `App.jsx`, `styles.css`, backend/API/SQLite/runtime/provider, B6/C13, real projects, browser/server, or medical-writing surfaces.
- 8911/5174 remain stopped; v11 remains frozen; no external route or Hermes dispatch.

## Timeout Policy

- Do not mark the delegated agent failed for slow response alone.
- For complex or artifact-heavy work, wait and poll generously; use conference mode when multiple independent model perspectives are needed.
- Failure requires terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.

## Loop Log

- 2026-08-02 11:42:12: Task initialized by `tools/hermes_workflow_guard.py init-task`.
- 2026-08-02 11:43:00: Reviewed checklist loading/error/empty paths; a nonzero API total with no safely renderable rows fell through to the ordinary no-risk copy.
- 2026-08-02 11:44:00: Added a fail-closed shape/pagination warning branch without changing risk data or API behavior.
