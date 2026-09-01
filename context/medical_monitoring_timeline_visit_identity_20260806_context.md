# Task Context: medical_monitoring_timeline_visit_identity_20260806

Created: 2026-08-06 08:21:09
Objective: 离线审计 Patient Profile 时间线访视轴的 anchor/source identity，保留重复/缺失访视可见并避免 SVG reconciliation 键碰撞
Task type: `code_scoped_patch_plan`
Risk: `high`
Selected agent route: `codex` / `codex-main` / `high`

## Trigger Reason

This task was initialized through the Codex x Hermes complex-task entrypoint because it is expected to involve more than three execution steps, research/writing/report/code/report-visual work, or source-grounded verification.

## Source Of Truth

- `frontend/src/features/medical-monitoring/medicalMonitoringSubjectModels.mjs`
- `frontend/src/features/medical-monitoring/MedicalMonitoringSubjectViews.jsx`
- `frontend/src/features/medical-monitoring/medicalMonitoringSubjectModels.test.mjs`
- `tests/test_frontend_monitoring_contract.py`
- `records/active_slices/medical_monitoring_real_loop_gate_audit_20260804/CURRENT_REAL_LOOP_GATE_AUDIT.json`
- Current read-only/blocked gate and the source files above; no runtime data source was opened.

## Scope

- In scope: Patient Profile/Subject Timeline visit-axis display identity; preserve duplicate or missing `anchor_id`/source identity while preventing SVG reconciliation collisions and making the ambiguity visible.
- Out of scope: visit deduplication, source/schema repair, date derivation, visit ordering/window logic, event facts, API/backend/database/CAS/B6/C14/P8/source-token/Safety-PV, providers, services, browser/API login, real projects, shared shell/styles/main and medical-writing paths.

## Success Criteria

- Timeline visits retain source order and receive `ready`/`missing`/`duplicate` display state with source-indexed keys.
- SVG visit groups use the display key; the page explicitly warns when a visit source identity is missing/duplicated.
- Focused/full offline contracts and Vite build pass; protected shell hashes remain unchanged and four runtime ports remain stopped.

## Risk Boundaries

- Only the feature-owned subject model/view/test/static-contract files and this task's records/context/review/metrics may change; no runtime or data-store write.
- Display identity is UI-only. It must not replace source identity, infer dates, deduplicate visits, change order/window semantics, or alter event facts.
- Do not start 8911, 5174, 8910 or 4173; no provider, browser/Playwright, API login, real project, runtime/SQLite/CAS, B6/C14, P8/source-token, Safety/PV or medical-writing action.
- Codex is final authority; Hermes dispatch was not used.

## Timeout Policy

- Do not mark the delegated agent failed for slow response alone.
- For complex or artifact-heavy work, wait and poll generously; use conference mode when multiple independent model perspectives are needed.
- Failure requires terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.

## Loop Log

- 2026-08-06 08:21:09: Task initialized by `tools/hermes_workflow_guard.py init-task`.
- 2026-08-06: Confirmed the visit-axis SVG keyed visits by direct `anchorId` or a date/code fallback; missing or duplicate source identity could cause React/SVG reconciliation collisions without a visible warning.
- 2026-08-06: Added explicit source identity propagation for event-derived visit rows, `timelineVisitDisplayRows`, source-indexed display keys, and page/SVG warning copy. Date axis, order, window calculations and event facts remain unchanged.
- 2026-08-06: Subject-model Node passed; focused monitoring/timeline Python **98 passed**; all 38 monitoring Node files passed; Vite build passed (1,956 modules; existing >500 kB advisory); runtime ports stopped; `review-gate --require-verification` returned `ok=true` with no warnings/errors.
