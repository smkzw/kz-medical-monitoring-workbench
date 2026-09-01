# Task Context: medical_monitoring_subject_trend_point_identity_20260806

Created: 2026-08-06 08:06:42
Objective: 离线审计 Patient Profile 趋势图点级 point_id 身份与选择键，保留重复/缺失点可见但避免显示/选择碰撞；不启动运行时
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

- In scope: Patient Profile `TrendSparkline` point display/reconciliation identity; retain source order and raw point facts while making missing/duplicate `point_id` states visible and collision-safe.
- Out of scope: server/schema/source repair, point deduplication, clinical interpretation, statistical logic, API payloads, backend/database/CAS/B6/C14/P8/source-token/Safety-PV, providers, services, browser/API login, real projects, shared shell/styles/main and medical-writing paths.

## Success Criteria

- Missing/duplicate point identities remain visible and are marked `missing`/`duplicate`; no inferred replacement identity is written back.
- Chart reference-range groups, interactive points, detail rows and selected-point state use source-indexed display keys; raw `point_id`, values, dates, risk flags and evidence are unchanged.
- Focused and full offline contracts plus Vite build pass; protected shell hashes remain unchanged and the four runtime ports remain stopped.

## Risk Boundaries

- Only the feature-owned model/view/test/static-contract files and this task's records/review/metrics may change; no production runtime or data-store write.
- Display metadata is UI-only. It must not substitute `point_id`, alter a raw point, change risk/clinical semantics, or authorize an action.
- Do not start 8911, 5174, 8910 or 4173; no provider, browser/Playwright, API login, real project, runtime/SQLite/CAS, B6/C14, P8/source-token, Safety/PV or medical-writing action.
- Codex is final authority; Hermes dispatch was not used.

## Timeout Policy

- Do not mark the delegated agent failed for slow response alone.
- For complex or artifact-heavy work, wait and poll generously; use conference mode when multiple independent model perspectives are needed.
- Failure requires terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.

## Loop Log

- 2026-08-06 08:06:42: Task initialized by `tools/hermes_workflow_guard.py init-task`.
- 2026-08-06 08:07–08:10: Confirmed the local trend point source used `point_id` directly for interactive/reference keys; duplicate or missing IDs could collide or be mistaken for a uniquely traceable point.
- 2026-08-06: Added `trendPointDisplayRows` with source-indexed display keys and explicit identity state. TrendSparkline now uses those keys for point entries/reference groups, shows a review-only warning, and labels ambiguous detail/inspector rows. No raw point or payload mutation.
- 2026-08-06: Subject-model Node passed; focused monitoring/timeline Python 96 passed; all 38 monitoring Node files passed; Vite build passed (1,956 modules; existing >500 kB advisory); runtime ports stopped; `review-gate --require-verification` returned `ok=true` with no warnings/errors.
