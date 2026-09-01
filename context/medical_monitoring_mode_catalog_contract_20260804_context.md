# Task Context: medical_monitoring_mode_catalog_contract_20260804

Created: 2026-08-04 21:48:23
Objective: Bind the three medical-monitoring commercial modes to explicit user-facing labels and baseline semantics without changing runtime authority or state transitions.
Task type: `finite_code_task`
Risk: `medium`
Selected agent route: `opencode-go` / `deepseek-v4-flash` / `max`

## Trigger Reason

This task was initialized through the Codex x Hermes complex-task entrypoint because it is expected to involve more than three execution steps, research/writing/report/code/report-visual work, or source-grounded verification.

## Source Of Truth

- `frontend/src/features/medical-monitoring/medicalMonitoringModeCatalog.mjs`
  is the new read-only user-facing vocabulary for the three commercial modes.
- Existing daily-run implementation:
  `frontend/src/features/medical-monitoring/MedicalMonitoringDailyRunPanel.jsx`
  and `medicalMonitoringDailyRunView.mjs`.
- Existing P8 assurance implementation:
  `medicalMonitoringAssurance.mjs`,
  `MedicalMonitoringAssurancePanel.jsx`, and the backend's frozen
  `pre_lock` / `pre_inspection` task contract.
- Existing evidence vocabulary:
  `services/api/app/monitoring_real_loop_mode_coverage.py`.

## Scope

- In scope: a shared frontend mode catalog; explicit baseline/completion copy;
  binding the daily-run panel to `daily_incremental`; binding assurance tabs
  to `pre_lock_total` and `post_lock_fixed_total`; focused static/Node tests.
- Out of scope: changing APIs, task IDs, persistence, risk rules, source
  readiness, B6/C14/approved-input/host identity, runtime/provider/browser/
  Playwright, real project data, SQLite, or medical-writing code.

## Success Criteria

- The three mode IDs are frozen in one catalog with source, baseline and
  completion semantics.
- Daily UI visibly identifies the incremental workflow.
- Assurance tabs visibly distinguish pre-lock full recompute from post-lock
  fixed-total rollup without altering existing API-compatible labels or state.
- Node contracts, frontend monitoring/timeline/unified-risk contracts, Vite
  build, reserved-port checks and Hermes review-gate pass.

## Risk Boundaries

- Do not write to production paths until Codex review gate passes and writable paths are explicit.
- The delegated agent is not final authority; Codex owns verification and acceptance.

## Timeout Policy

- Do not mark the delegated agent failed for slow response alone.
- For complex or artifact-heavy work, wait and poll generously; use conference mode when multiple independent model perspectives are needed.
- Failure requires terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.

## Evidence Boundary

- This is a source-only readiness slice. No service, port, browser, API login,
  provider, runtime, SQLite database or supplied real project was started or
  touched.
- The catalog is descriptive only; it cannot select a mode, create a task,
  mutate a baseline or grant authority.

## Gate Snapshot at Closure

- B6 packet revalidation: `fresh`, `issue_count=0`, `authority_safe=true`, but
  activation/medical approval/migration/write/real-project/service flags are
  all false.
- Release coverage: `blocked`, `release_ready=false`.
- Real-loop gate: `blocked`, read-only/provider/runtime activation/write flags
  false.
- Required ports 8911, 5174, 8910 and 4173: empty.

## Loop Log

- 2026-08-04 21:48:23: Task initialized by `tools/hermes_workflow_guard.py init-task`.
- 2026-08-04 21:49–21:53: Added the read-only catalog, assurance-to-commercial
  mode bindings, daily/assurance UI copy and focused contracts. Existing
  internal API mode IDs remain unchanged.
- 2026-08-04 21:53: Node mode/assurance/project-isolation checks passed;
  frontend monitoring/timeline/unified-risk contracts passed; Vite build
  passed. Reserved ports remained empty.
