# Task Context: medical_monitoring_profile_metric_availability_state_20260802

Created: 2026-08-02 11:46:08
Objective: 区分 Patient Profile 疗效/安全性指标的来源缺失、字段能力受限与尚未提供空态，避免把空趋势误读为无风险或等待状态
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
- `frontend/AGENTS.md` Patient Profile data/empty-state contract

## Scope

- In scope: explicit empty-state wording for efficacy/safety metric sections based only on existing subject capability and domain-availability metadata; focused tests/build/evidence.
- Out of scope: clinical interpretation, thresholds, API/backend/SQLite/runtime/provider, App.jsx/styles.css, source evidence, B6/C13, real projects, browser, and medical-writing surfaces.

## Success Criteria

- Empty metric sections distinguish not-loaded, restricted capability, source-unavailable, and generic not-provided states.
- Every empty state explicitly says it cannot establish stability or absence of risk.
- No inference is made from titles, free text, counts, dates, or missing metrics; existing populated chart behavior remains unchanged.
- Subject model tests, focused frontend contracts, all medical-monitoring Node tests, and Vite build pass.

## Risk Boundaries

- Do not write to production paths until Codex review gate passes and writable paths are explicit.
- Do not infer clinical stability, safety absence, efficacy response, or source availability beyond explicit metadata.
- Do not modify `App.jsx`, `styles.css`, backend/API/SQLite/runtime/provider, B6/C13, real projects, browser/server, or medical-writing surfaces.
- 8911/5174 remain stopped; v11 remains frozen; no external route or Hermes dispatch.

## Timeout Policy

- Do not mark the delegated agent failed for slow response alone.
- For complex or artifact-heavy work, wait and poll generously; use conference mode when multiple independent model perspectives are needed.
- Failure requires terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.

## Loop Log

- 2026-08-02 11:47:00: Reviewed Patient Profile empty metric sections; “等待生成” did not distinguish source absence or restricted mapping and could be read as a transient UI state.
- 2026-08-02 11:48:00: Added pure metadata-driven `profileMetricEmptyStateMessage` and explicit role=status copy; no populated metric path changed.
