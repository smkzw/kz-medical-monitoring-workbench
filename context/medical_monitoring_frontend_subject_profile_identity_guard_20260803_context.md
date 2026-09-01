# Task Context: medical_monitoring_frontend_subject_profile_identity_guard_20260803

Created: 2026-08-03 12:42:18 (Asia/Shanghai)
Objective: Reject subject monitoring profile responses whose canonical project or subject identity does not match the active request before caching the profile.
Task type: `finite_code_task`; risk `high`; direct Codex execution.

## Source Of Truth

- `frontend/src/App.jsx` selected-subject profile effect and `monitoringResponseProjectIdRef`.
- `packages/contracts/workbench_contracts/models.py:SubjectMonitoringDrilldown`, whose response identity is top-level `project_id` and `subject_id`.
- Existing `tests/test_frontend_timeline_contract.py` and three project adapter/API test suites.

## Evidence Before Change

- The profile fetch wrote any JSON response to `[requestedProfileKey]` after only a cancellation check.
- A wrong subject or project response could therefore be rendered under the current selected subject. The project comparison must use the canonical active-project ref because MY009 route aliases are canonicalized.

## Scope

- In scope: guard profile cache writes on canonical `project_id` and requested `subject_id`, plus a static regression assertion.
- Out of scope: backend response construction, route aliases, profile values, services, providers, browser login, B6/C14 and runtime writes.

## Success Criteria

- Mismatched profile responses are ignored before `setSubjectProfiles`.
- Correct canonical project/subject responses remain accepted.
- Focused frontend/manifest tests, medical-monitoring Node suites, Vite build and Ruff pass.

## Risk Boundaries

- Preserve request cancellation and cache-key behavior; no fallback profile is introduced.
- No 8911/5174/service/provider/browser/real-project operation; no authority or migration action.
- The workflow route was recorded but not dispatched; direct Codex owns acceptance.

## Loop Log

- 2026-08-03 12:42:18: Initialized via workflow guard; no external route dispatched.
- 2026-08-03 12:43: Added project and subject identity checks before profile cache update.
- 2026-08-03 12:44: Frontend/timeline/manifest set **54 passed**, 17 existing warnings; medical-monitoring Node suites **22 passed**; Vite and Ruff passed. The previously established 4.95 adapter evidence remains 35 passed/19 warnings; no backend source changed.
