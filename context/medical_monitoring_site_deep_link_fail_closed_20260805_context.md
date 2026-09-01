# Task Context: medical_monitoring_site_deep_link_fail_closed_20260805

Created: 2026-08-05 09:48:48
Objective: Prevent an unavailable medical-monitoring site deep link from silently becoming an empty or different scope; preserve current project scope, distinguish pending catalog from unavailable site, and verify pure routing/build contracts without runtime.
Task type: `code_scoped_patch_plan`
Risk: `high`
Selected agent route: `codex` / `codex-main` / `high`

## Trigger Reason

This task was initialized through the Codex x Hermes complex-task entrypoint because it is expected to involve more than three execution steps, research/writing/report/code/report-visual work, or source-grounded verification.

## Source Of Truth

- `frontend/src/App.jsx` monitoring scope, risk-rollup and site deep-link
  rendering.
- `frontend/src/features/medical-monitoring/medicalMonitoringRouteState.mjs`
  and its pure regression module.
- `context/medical_monitoring_p9_source_only_checkpoint_20260805.md` and
  `records/active_slices/medical_monitoring_project_completion_audit_20260804/COMPLETION_MATRIX.md`.
- `records/active_slices/medical_monitoring_real_loop_gate_audit_20260804/CURRENT_REAL_LOOP_GATE_AUDIT.json` remains the authority boundary.

## Scope

- In scope: resolve a site deep link against current-project subject/risk
  sources, distinguish `pending` from `unavailable`, show a recoverable scope
  warning, add pure route regressions, and verify pure suites/build.
- Out of scope: server permission enforcement, runtime/API/browser/Playwright,
  providers, real study data, B6/C14 review or activation, medical-writing
  content, and commercial-release claims.

## Success Criteria

- A known site in the current subject catalog or risk rollup remains matched.
- An unknown site is explicit and cannot be treated as an empty normal result or
  replaced by another center.
- An empty source catalog remains pending, not a false unavailable conclusion.
- The UI offers a route-safe return to trial scope; focused/full tests, build,
  source checks and review-gate pass.

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

- 2026-08-05 09:48:48: Task initialized by `tools/hermes_workflow_guard.py init-task`.
- 2026-08-05 09:49: Source audit identified a site-scope deep link that could
  render an empty result without telling the monitor whether the center was
  missing or the data was still pending.
- 2026-08-05 09:50: Added pure site route resolution and an App warning with a
  trial-scope recovery action. Focused route assertions: **54 passed**.
- 2026-08-05 09:51: All **33** frontend medical-monitoring pure modules passed;
  Vite build passed in **1.92s** with the pre-existing >500 kB warning. Runtime,
  services, ports, browser and providers stayed stopped.
