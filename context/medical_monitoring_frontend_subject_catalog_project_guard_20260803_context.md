# Task Context: medical_monitoring_frontend_subject_catalog_project_guard_20260803

Created: 2026-08-03 12:39:18 (Asia/Shanghai)
Objective: Reject subject-catalog responses that do not belong to the current canonical active project before updating monitoring subject state.
Task type: `finite_code_task`; risk `high`; direct Codex execution.

## Source Of Truth

- `frontend/src/App.jsx` subject-catalog effect and `monitoringResponseProjectIdRef`.
- `services/api/app/main.py:get_monitoring_subjects`, which canonicalizes route aliases before returning `project_id`.
- `tests/test_frontend_timeline_contract.py` and `tests/test_project_source_manifest.py`.
- MY009 manifest evidence: `my009_uc_monitoring_raw` is a route alias for canonical `proj_my009_uc`.

## Evidence Before Change

- The subject-catalog effect only checked `cancelled`; a wrong-project payload could update `monitoringSubjectCatalog` and `selectedSubject`.
- A direct comparison with `monitoringRouteProjectId` would be incorrect for MY009 alias routes, so the existing canonical `monitoringResponseProjectIdRef.current` is the correct guard.

## Scope

- In scope: one response-identity guard and one frontend contract assertion.
- Out of scope: backend canonicalization, source manifests, subject data, profile fetches, services, providers, browser login, B6/C14 and runtime writes.

## Success Criteria

- Mismatched `data.project_id` is ignored before state updates.
- Alias-compatible canonical responses remain accepted.
- Focused frontend/manifest tests, all medical-monitoring Node tests, Vite build and Ruff pass.

## Risk Boundaries

- Preserve the existing cancellation and project-switch behavior; do not alter backend aliases or data values.
- No 8911/5174/service/provider/browser/real-project operation; no B6/C14 authority action.
- The workflow guard route was recorded but not dispatched; direct Codex owns verification.

## Loop Log

- 2026-08-03 12:39:18: Initialized with `hermes_workflow_guard.py`; no external route dispatched.
- 2026-08-03 12:40: Confirmed canonical alias behavior in backend and manifest tests.
- 2026-08-03 12:40: Added `data.project_id !== monitoringResponseProjectIdRef.current` fail-closed guard and a static regression.
- 2026-08-03 12:41: Focused frontend/manifest tests **54 passed** (17 warnings); medical-monitoring Node suites **22 passed**; Vite build and Ruff passed.
