# Task Context: medical_monitoring_subject_identity_mismatch_visible_ux_20260803

## Objective

Make existing subject-catalog and subject-profile project/subject identity
mismatch guards visible to the medical monitor while preserving fail-closed
empty-state behavior.

## Source and scope

- Workbench `frontend/src/App.jsx` catalog/profile effects and
  `MonitoringPage` warning surface.
- In scope: visible warning state, project-reset behavior and static contracts.
- Out of scope: API/backend changes, subject data, service/provider/browser/
  API login, real projects, B6/C14, runtime and clinical conclusions.

## Success criteria

- Wrong or missing identity still cannot populate catalog/profile state.
- The monitoring view shows an explicit identity warning and clears it on a
  fresh valid project load or project reset.
- Focused contracts, Node suites, Vite and Ruff remain green.

## Risk boundary and route

No subject endpoint or runtime was called. Workflow route is recorded only and
not dispatched; direct Codex owns implementation and acceptance.

## Loop log

- 2026-08-03 13:35:12: `tools/hermes_workflow_guard.py init-task` completed.

## Final evidence

- Direct Codex implemented the bounded frontend change; no delegated route was
  dispatched.
- Focused Python contracts passed (144 passed, 17 warnings), the 22
  medical-monitoring Node suites passed, the Vite build passed, and Ruff passed
  on the changed contract files.
- A broader browser QC was not used as acceptance because it failed before
  exercising this slice (`Missing button: 医学监查`) and requires a runtime
  surface outside this offline boundary.

## Source of truth

- `frontend/src/App.jsx`
- `tests/test_frontend_source_manifest_contract.py`
- `tests/test_frontend_timeline_contract.py`
- Existing project-switch and response-identity contracts in the same
  workbench.

## Scope

- In scope: visible monitoring-view warning for existing subject catalog/profile
  identity mismatch guards, state reset on project reset, and static contracts.
- Out of scope: API/backend changes, subject data, services, providers,
  browser/API login, real projects, B6/C14 activation, runtime, and clinical
  conclusions.

## Success criteria

- Wrong or missing identity cannot populate catalog/profile state.
- The monitoring view shows an explicit identity warning and clears it on a
  fresh valid project load or project reset.
- Focused contracts, Node suites, Vite and changed-file Ruff checks pass.

## Risk boundaries

- No subject endpoint or runtime was called.
- 8911 and 5174 remain stopped; B6 and C14 remain blocked and unchanged.
- Workflow route is recorded only and not dispatched; Codex owns verification
  and acceptance.
