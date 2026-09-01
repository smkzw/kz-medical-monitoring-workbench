# Task Context: medical_monitoring_risk_checklist_accessibility_20260802

Created: 2026-08-02 11:23:32
Objective: 强化医学监查风险清单的键盘可达性、行选中语义与屏幕阅读标签，让资深医学监查员在少点击条件下稳定聚焦风险且不改变风险数据、排序、筛选或权限合同。
Task type: `code_scoped_patch_plan`
Risk: `high`
Selected agent route: `codex` / `codex-main` / `high`

## Trigger Reason

This task was initialized through the Codex x Hermes complex-task entrypoint because it is expected to involve more than three execution steps, research/writing/report/code/report-visual work, or source-grounded verification.

## Source Of Truth

- `frontend/src/features/medical-monitoring/MedicalMonitoringRiskChecklist.jsx`
- `frontend/src/features/medical-monitoring/medicalMonitoringModels.mjs`
- `tests/test_frontend_unified_risk_workbench_contract.py`
- `frontend/AGENTS.md` desktop-first and medical-monitoring display contracts
- B6/C14 read-only gate evidence and the current P10/LOOP ledger

## Scope

- In scope: row-level keyboard activation semantics, selected-state and accessible labels for the existing risk checklist; focused static/Node/build verification and evidence records.
- Out of scope: risk data shape, API query/filter/sort contracts, disposition mutation, CSS/layout redesign, App.jsx/styles.css, backend/runtime/provider/SQLite, B6/C13 authority, real projects, browser/server startup, and medical-writing surfaces.

## Success Criteria

- Enter and Space activate the same existing `onSelect` action; Space does not scroll the page.
- Each row exposes `aria-selected` and a deterministic label made only from displayed risk fields and existing label functions.
- No risk value, severity, category, disposition, sort, filter, paging, export, or permission behavior changes.
- Existing frontend contracts, medical-monitoring Node tests, and Vite build pass.
- Shared protected surfaces, stopped ports, B6/C14 state, and medical-writing lane remain unchanged.

## Risk Boundaries

- Do not write to production paths until Codex review gate passes and writable paths are explicit.
- Do not infer risk meaning, severity, category, site, or disposition; labels reuse existing model functions and explicit fields.
- Do not modify `frontend/src/App.jsx`, `frontend/src/styles.css`, backend/API/runtime/SQLite/provider, B6/C13 gates, or medical-writing surfaces.
- 8911 and 5174 remain stopped; v11 remains frozen; no real project, service, browser, or provider is allowed in this slice.
- Codex performs this route directly; no Hermes dispatch or delegated-agent output is accepted as production evidence.

## Timeout Policy

- Do not mark the delegated agent failed for slow response alone.
- For complex or artifact-heavy work, wait and poll generously; use conference mode when multiple independent model perspectives are needed.
- Failure requires terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.

## Loop Log

- 2026-08-02 11:23:32: Task initialized by `tools/hermes_workflow_guard.py init-task`.
- 2026-08-02 11:24:00: Inspected checklist row semantics; rows already use click/keyboard selection but lacked selected-state, accessible label, and Space default suppression.
- 2026-08-02 11:24:30: Added `riskRowAccessibleLabel`, `aria-selected`, `aria-label`, and Enter/Space `preventDefault` while preserving the existing callback and data fields.
- 2026-08-02 11:25:00: Focused Python contracts 44 passed, all 22 medical-monitoring Node test files passed, and Vite 1925-module build passed with the existing chunk warning.
