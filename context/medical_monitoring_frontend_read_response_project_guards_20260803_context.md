# Task Context: medical_monitoring_frontend_read_response_project_guards_20260803

Created: 2026-08-03 12:48:47 (Asia/Shanghai)
Objective: Fail closed on cross-project read responses in the monitoring risk snapshot, taxonomy, focused-risk and raw-intake views before committing state.
Task type: `finite_code_task`; risk `high`; direct Codex execution.

## Source Of Truth

- `frontend/src/App.jsx` `MonitoringPage` read effects.
- `sourceManifest.project_id`, which is canonical, and the existing route alias mapping.
- Backend contracts: risk snapshot, risk taxonomy, focused risk and raw-intake responses all include canonical `project_id`.

## Evidence Before Change

- Four read effects relied on cancellation/active flags but did not verify response project identity before state updates.
- `MonitoringPage` already had `sourceManifest`; the canonical expected identity is `sourceManifest?.project_id || monitoringProjectId`.

## Scope

- In scope: add the expected canonical project value and guard risk snapshot, taxonomy, focused-risk and raw-intake read commits; add static assertions.
- Out of scope: write actions, backend/API contracts, source manifests, route aliases, services, providers, browser login, B6/C14 and runtime state.

## Success Criteria

- Cross-project/malformed project responses cannot update the four read states.
- Correct MY009 alias-backed canonical responses remain accepted.
- Frontend contracts, Node medical-monitoring suites, Vite build and Ruff pass.

## Risk Boundaries

- No service/provider/browser/API login/real project operation; no CAS/source-token/migration/authority write.
- The workflow route was recorded but not dispatched; direct Codex owns acceptance.

## Loop Log

- 2026-08-03 12:48:47: Initialized through workflow guard; no external route dispatched.
- 2026-08-03 12:49: Added canonical expected-project guards to four read-only effects and static regression assertions.
- 2026-08-03 12:50: Focused frontend/timeline/risk/safety/manifest set **76 passed**, 17 existing warnings; medical-monitoring Node suites **22 passed**; Vite and Ruff passed.
