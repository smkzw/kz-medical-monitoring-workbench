# Task Context: medical_monitoring_timeline_data_coverage_20260802

Created: 2026-08-02 11:14:09
Objective: 在医学监查 Subject Timeline 与内嵌风险时间线中建立严格的实际日期证据覆盖契约，避免计划日或缺失日期被误绘为真实时间轴，并为资深医学监查员保留可追溯的来源事件明细。
Task type: `code_scoped_patch_plan`
Risk: `high`
Selected agent route: `codex` / `codex-main` / `high`

## Trigger Reason

This task was initialized through the Codex x Hermes complex-task entrypoint because it is expected to involve more than three execution steps, research/writing/report/code/report-visual work, or source-grounded verification.

## Source Of Truth

- `frontend/src/features/medical-monitoring/medicalMonitoringSubjectModels.mjs`
- `frontend/src/features/medical-monitoring/MedicalMonitoringSubjectViews.jsx`
- `frontend/src/features/medical-monitoring/medicalMonitoringSubjectModels.test.mjs`
- `tests/test_frontend_timeline_contract.py`
- `frontend/AGENTS.md` Subject Timeline visual contract
- `context/medical_monitoring_system_retro_pause_20260801.md` and `reviews/medical_monitoring_system_retro_roadmap_20260801.md`
- B6/C14 gates remain read-only authority evidence:
  `runs/execution/medical_monitoring_phase_b6_review_gate_20260801/B6_REVIEW_OUTCOME_GATE.json` and
  `runs/execution/medical_monitoring_phase_c14_b6_activation_gate_20260802/B6_TO_C13_ACTIVATION_GATE_REPORT.json`

## Scope

- In scope: a pure actual-date evidence helper; Timeline and embedded risk-timeline fail-closed rendering for missing/partial dates; preserving undated source events in detail rows; focused regression contracts and evidence records.
- Out of scope: App.jsx/styles.css, backend/API/source registry/SQLite/runtime/provider, B6/C13 outcomes or migration, protocol/risk thresholds, real-project execution, browser/server startup, and medical-writing surfaces.

## Success Criteria

- A complete, calendar-valid `YYYY-MM-DD` is the only value eligible to position a visit/event on the graph.
- Planned study days, visit codes, partial dates, and invalid dates never become axis coordinates; affected records remain discoverable in source detail rows.
- No valid actual dates yields an explicit non-axis state rather than a fallback axis based on `Date.now()`.
- Mixed coverage explicitly reports omitted date evidence and never presents it as a time-window or ordering conclusion.
- Existing monitor feature tests, frontend timeline contracts, and production Vite build pass.
- B6/C14, stopped ports, protected shared files, and medical-writing boundaries remain unchanged.

## Risk Boundaries

- Do not write to production paths until Codex review gate passes and writable paths are explicit.
- No source field is repaired, normalized into a date, or clinically interpreted by this slice.
- `App.jsx` and `styles.css` are protected shared surfaces; no runtime/service/provider/browser/SQLite or real-project execution is allowed.
- The v11 terminal failure remains frozen; 8911 and 5174 remain stopped; B6 `write_permitted=false` and C14 `activation_allowed=false` remain authoritative.
- The delegated-agent section is not applicable: Codex performed this route directly and remains final authority.

## Timeout Policy

- Do not mark the delegated agent failed for slow response alone.
- For complex or artifact-heavy work, wait and poll generously; use conference mode when multiple independent model perspectives are needed.
- Failure requires terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.

## Loop Log

- 2026-08-02 11:14:09: Task initialized by `tools/hermes_workflow_guard.py init-task`.
- 2026-08-02 11:15:00: Added strict `hasActualTimelineDate` and descriptive `timelineDataCoverage`; no derivation from planned day, visit code, partial date, or invalid date.
- 2026-08-02 11:15:30: Subject Timeline and embedded risk timeline now omit undated/invalid events from graph placement, show explicit no-axis/partial-data warnings, and retain source detail rows.
- 2026-08-02 11:16:00: Added model and static frontend regression assertions; 22/22 medical-monitoring Node test files passed, 41 Python frontend contracts passed, Vite transformed 1925 modules and built successfully.
- 2026-08-02 11:17:17: Source/protected hashes and B6/C14 gate hashes captured; no service, provider, API, SQLite, browser, or real project was run.
