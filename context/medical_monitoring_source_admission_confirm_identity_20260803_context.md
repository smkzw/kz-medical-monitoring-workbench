# Task Context: medical_monitoring_source_admission_confirm_identity_20260803

## Objective

Require canonical project identity on shared `ModuleSourceAdmissionBand`
source-confirmation responses before success messaging or refresh.

## Source and scope

- Workbench `frontend/src/App.jsx` `ModuleSourceAdmissionBand.confirmSource`.
- Backend `SourceContentValidationRecord` and confirmation endpoint expose
  canonical `project_id`.
- In scope: success-response identity guard and static contract.
- Out of scope: API/backend changes, source confirmation, service/provider,
  browser/API login, real projects, B6/C14, runtime and clinical conclusions.

## Success criteria

- Wrong or missing identity cannot show confirmed status, clear the selection or
  trigger `onRefresh`.
- Existing per-check acknowledgement, reason validation and error handling
  remain.
- Focused Python contracts, Node suites, Vite and Ruff pass.

## Risk boundary and route

No source confirmation endpoint or runtime was called. Workflow route is
recorded only and not dispatched; direct Codex owns implementation and
acceptance.

## Final evidence

- Direct Codex added the success-response identity guard and static contract.
- Focused Python/source set passed (155 passed, 17 existing warnings), all 22
  medical-monitoring Node suites passed, Vite build passed, and Ruff passed on
  changed contract files.
- No browser/runtime/live authority check was run because B6/C14 remain closed.

## Risk boundaries

- 8911 and 5174 remain stopped; B6 and C14 remain blocked and unchanged.
- This is not runtime, scientific, UAT or commercial acceptance.
