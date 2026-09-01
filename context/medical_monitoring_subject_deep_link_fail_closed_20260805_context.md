# Task Context: medical_monitoring_subject_deep_link_fail_closed_20260805

Created: 2026-08-05 09:45:15
Objective: Prevent an unavailable medical-monitoring subject deep link from silently falling back to another subject; preserve the requested route, show a recoverable state, and verify pure routing/build contracts without runtime.
Task type: `code_scoped_patch_plan`
Risk: `high`
Selected agent route: `codex` / `codex-main` / `high`

## Trigger Reason

This task was initialized through the Codex x Hermes complex-task entrypoint because it is expected to involve more than three execution steps, research/writing/report/code/report-visual work, or source-grounded verification.

## Source Of Truth

- `frontend/src/App.jsx` subject-catalog hydration, URL synchronization and
  Timeline/Profile routing.
- `frontend/src/features/medical-monitoring/medicalMonitoringRouteState.mjs`
  and its pure regression module.
- `context/medical_monitoring_p9_source_only_checkpoint_20260805.md` and
  `records/active_slices/medical_monitoring_project_completion_audit_20260804/COMPLETION_MATRIX.md`.
- `records/active_slices/medical_monitoring_real_loop_gate_audit_20260804/CURRENT_REAL_LOOP_GATE_AUDIT.json` remains the authority boundary.

## Scope

- In scope: resolve a subject deep link only against the current project's
  subject catalog, preserve an unavailable requested subject in the route,
  expose a recoverable UI state, add pure route regressions, and verify pure
  suites/build.
- Out of scope: server permission enforcement, runtime/API/browser/Playwright,
  providers, real study data, B6/C14 review or activation, medical-writing
  content, and commercial-release claims.

## Success Criteria

- An available requested subject remains selected and loads the existing path.
- An unavailable requested subject never becomes another subject id; the URL
  remains inspectable and the UI explains the boundary.
- Returning to monitoring or selecting a known subject clears the stale focus.
- Focused/full pure tests, build, source checks and review-gate pass.

## Risk Boundaries

- Do not write to production paths until Codex review gate passes and writable paths are explicit.
- The delegated agent is not final authority; Codex owns verification and acceptance.
- Do not start 8911/5174/8910/4173 or any service, browser, provider, API login
  or real-project loop while the authoritative gate is blocked.

## Timeout Policy

- Do not mark the delegated agent failed for slow response alone.
- For complex or artifact-heavy work, wait and poll generously; use conference mode when multiple independent model perspectives are needed.
- Failure requires terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.

## Loop Log

- 2026-08-05 09:45:15: Task initialized by `tools/hermes_workflow_guard.py init-task`.
- 2026-08-05 09:46: Source audit found subject-catalog hydration silently
  selected the first subject when an explicit route subject was absent.
- 2026-08-05 09:47: Added pure subject route resolution, preserved the route
  during unavailable state and surfaced a recoverable subject message in
  monitoring/Timeline/Profile consumers. Focused route assertions: **50 passed**.
- 2026-08-05 09:48: All **33** frontend medical-monitoring pure modules passed;
  Vite build passed in **1.78s** with the pre-existing >500 kB warning. A final
  recovery-action refinement was then rebuilt at **1.98s**. Runtime,
  services, ports, browser and providers stayed stopped.
