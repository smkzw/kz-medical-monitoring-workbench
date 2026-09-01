# Task Context: medical_monitoring_risk_deep_link_fail_closed_20260805

Created: 2026-08-05 09:39:55
Objective: Make a medical-monitoring risk deep link explicit and fail closed when the requested risk is absent from the current project snapshot; preserve project scope, show a recoverable warning, and verify pure routing/build contracts without runtime.
Task type: `code_scoped_patch_plan`
Risk: `high`
Selected agent route: `codex` / `codex-main` / `high`

## Trigger Reason

This task was initialized through the Codex x Hermes complex-task entrypoint because it is expected to involve more than three execution steps, research/writing/report/code/report-visual work, or source-grounded verification.

## Source Of Truth

- `frontend/src/App.jsx` monitoring risk snapshot read and evidence-dock routing.
- `frontend/src/features/medical-monitoring/medicalMonitoringRouteState.mjs` and
  its pure regression module.
- `context/medical_monitoring_p9_source_only_checkpoint_20260805.md` and
  `records/active_slices/medical_monitoring_project_completion_audit_20260804/COMPLETION_MATRIX.md`.
- `records/active_slices/medical_monitoring_real_loop_gate_audit_20260804/CURRENT_REAL_LOOP_GATE_AUDIT.json` remains the authority boundary.

## Scope

- In scope: resolve a risk deep link only against rows scoped to the current
  project, make an absent risk explicit and recoverable in the UI, add pure
  route regressions, and verify the frontend pure suites/build.
- Out of scope: server permission enforcement, runtime/API/browser/Playwright,
  providers, real study data, B6/C14 review or activation, medical-writing
  content, and commercial-release claims.

## Success Criteria

- A risk id present in the current project matches and opens as before.
- A risk id absent from the current project is classified as `unavailable`,
  never substituted with another risk, and leaves the current project scope
  unchanged.
- The UI explains the missing risk and provides a route-safe return action.
- Focused and full pure tests, build, source checks and review-gate pass.

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

- 2026-08-05 09:39:55: Task initialized by `tools/hermes_workflow_guard.py init-task`.
- 2026-08-05 09:40: Source audit identified silent risk-deep-link loss when an
  initial risk was absent from the current project snapshot.
- 2026-08-05 09:41: Added pure risk route resolution and an App warning with a
  return-to-checklist action. Focused route assertions: **47 passed**.
- 2026-08-05 09:42: All **33** frontend medical-monitoring pure modules passed;
  Vite build passed in **1.86s** with the pre-existing >500 kB warning. Runtime,
  services, ports, browser and providers stayed stopped.
