# Task Context: medical_monitoring_profile_metric_shape_guard_20260802

Created: 2026-08-02 11:27:39
Objective: 在 Patient Profile 趋势图中对非数值、缺失测量点或缺少有效实际评估日期的点 fail-closed：只绘制同时具备有限数值与严格有效 `YYYY-MM-DD` 实际日期的点，将不可绘制原始点保留在明细并明确标注，避免 NaN/假趋势、虚构时间轴且不推断临床值。
Task type: `code_scoped_patch_plan`
Risk: `high`
Selected agent route: `codex` / `codex-main` / `high`

## Trigger Reason

This task was initialized through the Codex x Hermes complex-task entrypoint because it is expected to involve more than three execution steps, research/writing/report/code/report-visual work, or source-grounded verification.

## Source Of Truth

- `frontend/src/features/medical-monitoring/MedicalMonitoringSubjectViews.jsx`
- `frontend/src/features/medical-monitoring/medicalMonitoringSubjectModels.mjs`
- `frontend/src/features/medical-monitoring/medicalMonitoringSubjectModels.test.mjs`
- `tests/test_frontend_timeline_contract.py`
- `frontend/AGENTS.md` Patient Profile visual/data contract
- Current B6/C14 gates and P10/LOOP evidence ledger

## Scope

- In scope: pure metric point coverage helper; chart-only numeric-and-actual-date filtering; explicit non-numeric/date warnings and raw detail retention; focused tests/build/evidence records.
- Out of scope: clinical reference-range rules, threshold changes, data coercion, API/backend/source registry/SQLite/runtime/provider, App.jsx/styles.css, real projects/browser, B6/C13, and medical-writing surfaces.

## Success Criteria

- Only finite numeric `point.value` values with a calendar-valid complete `assessment_date` in `YYYY-MM-DD` form can produce chart geometry.
- NaN, null, strings, and malformed point rows cannot create NaN geometry or a false trend.
- Invalid/non-numeric or partial/invalid-date points remain visible in the original measurement detail list and are explicitly labeled as not provided/not drawable.
- If no point is both numeric and date-bound, the chart is replaced by an explicit non-drawable state rather than an empty or misleading SVG.
- Existing medical-monitoring Node tests, focused frontend contracts, and Vite build pass.

## Risk Boundaries

- Do not write to production paths until Codex review gate passes and writable paths are explicit.
- Do not coerce numeric strings, infer values, replace missing values, or alter risk flags/reference ranges.
- Do not modify `App.jsx`, `styles.css`, backend/API/SQLite/runtime/provider, B6/C13, real projects, browser/server, or medical-writing surfaces.
- 8911/5174 remain stopped; v11 remains frozen; no external route or Hermes dispatch.

## Timeout Policy

- Do not mark the delegated agent failed for slow response alone.
- For complex or artifact-heavy work, wait and poll generously; use conference mode when multiple independent model perspectives are needed.
- Failure requires terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.

## Loop Log

- 2026-08-02 11:27:39: Task initialized by `tools/hermes_workflow_guard.py init-task`.
- 2026-08-02 11:28:00: Reviewed `TrendSparkline`; raw non-numeric values could flow into `Math.min`/SVG geometry and produce NaN or an apparently complete chart.
- 2026-08-02 11:29:00: Added `metricDataCoverage`, numeric-and-actual-date-bound `chartPoints`, explicit non-drawable state, and retained raw detail rows with “数值未提供”/“日期未提供” labels.
- 2026-08-02 11:30:00: Model tests passed; Python frontend contracts 42 passed; all 22 medical-monitoring Node files passed; Vite transformed 1925 modules successfully.
- 2026-08-02 11:36:00: Bounded source audit confirmed legacy MG-K10/RUX/MY009 trend builders emit day-level ISO dates when a point is retained; the separate C5 consumer contract permits month/year precision, so this chart intentionally keeps those records detail-only until an explicit precision-aware visualization contract exists.
