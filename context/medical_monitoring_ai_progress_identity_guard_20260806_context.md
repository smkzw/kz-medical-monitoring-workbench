# Task Context: medical_monitoring_ai_progress_identity_guard_20260806

Created: 2026-08-06 04:40:39
Objective: Fail closed when daily AI progress response project or run identity does not match the selected monitoring context
Task type: `code_scoped_patch_plan`
Risk: `high`
Selected agent route: `codex` / `codex-main` / `high`

## Trigger Reason

This task was initialized through the Codex x Hermes complex-task entrypoint because it is expected to involve more than three execution steps, research/writing/report/code/report-visual work, or source-grounded verification.

## Source Of Truth

- Workbench source: `/Users/smkzw/Documents/康哲项目资料/AI/医学经理工作台/implementation/workbench`.
- Requirements and current gate: `docs/medical_monitoring_manual/医学监查子系统说明书.md`, P10 records under `records/active_slices/medical_monitoring_goal_p10_20260730/`, and `records/active_slices/medical_monitoring_real_loop_gate_audit_20260804/CURRENT_REAL_LOOP_GATE_AUDIT.json`.
- API response contract: `_ai_progress_dict` in `services/api/app/monitoring_daily_run_router.py` returns `project_id` and `run_id`; `medicalMonitoringApi.mjs` reads the endpoint.
- UI surfaces: `frontend/src/features/medical-monitoring/MedicalMonitoringDailyRunPanel.jsx`, `medicalMonitoringDailyRunView.mjs`, and focused project-switch/identity tests.
- Current gate is `read_only / blocked`; no provider/runtime/browser/real-project action is permitted.

## Scope

- In scope: a strict client-side normalizer/guard for daily AI progress identity (`project_id` and `run_id`) plus panel integration that rejects mismatched/missing identity before state commit, clears stale AI progress, and exposes a precise read-only error; focused positive/negative tests and full frontend verification.
- Out of scope: backend/API schema changes, provider calls, services/ports, Playwright/API login, real projects, runtime/SQLite/CAS/B6/C14, P8 authority, Safety/PV, shared App.jsx and medical-writing/reference.

## Success Criteria

- Matching project/run progress is accepted; missing or mismatched identity is rejected fail-closed and does not overwrite current state.
- A stale or mismatched response leaves no candidate/progress data in the selected run; the error identifies project/run identity mismatch without exposing source data.
- Existing request-scope cancellation behavior and all focused/full tests/builds remain green; ports stay stopped.

## Risk Boundaries

- Do not write to production paths until Codex review gate passes and writable paths are explicit.
- The delegated agent is not final authority; Codex owns verification and acceptance.

## Timeout Policy

- Do not mark the delegated agent failed for slow response alone.
- For complex or artifact-heavy work, wait and poll generously; use conference mode when multiple independent model perspectives are needed.
- Failure requires terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.

## Loop Log

- 2026-08-06 04:40:39: Task initialized by `tools/hermes_workflow_guard.py init-task`.
- 2026-08-06 04:41:00: Re-anchored the panel/API path. `load()` currently commits the AI progress response after request-scope checks but without checking the response project/run IDs; this is a cross-context contamination risk and the next patch adds a strict model guard.
