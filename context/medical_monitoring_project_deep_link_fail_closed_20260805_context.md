# Task Context: medical_monitoring_project_deep_link_fail_closed_20260805

Created: 2026-08-05 09:31:42
Objective: Prevent an unavailable medical-monitoring project deep link from silently falling back to another project; preserve the requested route, show a recoverable state, and verify pure routing contracts plus frontend build without starting runtime.
Task type: `code_scoped_patch_plan`
Risk: `high`
Selected agent route: `codex` / `codex-main` / `high`

## Trigger Reason

This task was initialized through the Codex x Hermes complex-task entrypoint because it is expected to involve more than three execution steps, research/writing/report/code/report-visual work, or source-grounded verification.

## Source Of Truth

- `frontend/src/App.jsx` project-list hydration, empty-project state and monitoring URL synchronization.
- `frontend/src/features/medical-monitoring/medicalMonitoringRouteState.mjs` and its pure Node regression module.
- `context/medical_monitoring_p9_source_only_checkpoint_20260805.md` and
  `records/active_slices/medical_monitoring_project_completion_audit_20260804/COMPLETION_MATRIX.md` for the current P9 boundary.
- `records/active_slices/medical_monitoring_real_loop_gate_audit_20260804/CURRENT_REAL_LOOP_GATE_AUDIT.json` is the authority boundary: read-only/blocked.

## Scope

- In scope: preserve an explicitly requested monitoring `project_id` when the
  project list does not contain it; expose a recoverable unavailable-link state;
  allow the user to select an available project; add pure route-resolution
  regressions and run the frontend pure suites/build.
- Out of scope: backend/API permission changes, runtime activation, services,
  ports, browser/Playwright, provider calls, real study data, B6/C14 review or
  migration, medical-writing content, and any commercial-release claim.

## Success Criteria

- An unavailable requested monitoring project never becomes another project ID
  in state or URL.
- The unavailable state is explicit and recoverable without a service restart;
  selecting an available project clears the stale monitoring route.
- A valid requested project and no requested project retain existing selection
  behavior.
- Focused route tests, all frontend pure modules, Vite build, compile/source
  checks and the per-slice review gate pass.

## Risk Boundaries

- Do not write to production paths until Codex review gate passes and writable paths are explicit.
- The delegated agent is not final authority; Codex owns verification and acceptance.
- Do not start 8911/5174/8910/4173 or any service, browser, API login, provider,
  or real-project loop while the authoritative gate remains blocked.

## Timeout Policy

- Do not mark the delegated agent failed for slow response alone.
- For complex or artifact-heavy work, wait and poll generously; use conference mode when multiple independent model perspectives are needed.
- Failure requires terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.

## Loop Log

- 2026-08-05 09:31:42: Task initialized by `tools/hermes_workflow_guard.py init-task`.
- 2026-08-05 09:34: Source audit located a concrete P9 gap in App project-list
  hydration: an unknown explicit monitoring project could fall back to another
  study. No external discovery was needed because this is a local route-state
  contract with existing source evidence.
- 2026-08-05 09:36: Added pure project-membership resolution and App-level
  fail-closed/recoverable handling. Focused route test passed (44 assertions).
- 2026-08-05 09:37: All 33 medical-monitoring pure frontend modules passed and
  Vite build passed in 2.02s with the pre-existing >500 kB warning. Runtime,
  services, ports, browser and providers stayed stopped.
