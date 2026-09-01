# Task Context: medical_monitoring_planned_action_identity_guards_20260803

## Objective

Require canonical project identity on PlannedModulePage TFL and safety review
action responses before committing review state or showing success.

## Source and scope

- Workbench `frontend/src/App.jsx` `PlannedModulePage` TFL and safety action
  handlers.
- Existing backend contracts in `services/api/app/main.py` and
  `packages/contracts/workbench_contracts/models.py` already return canonical
  `project_id` on both review-workbench action results.
- In scope: success-response identity guards and static contracts.
- Out of scope: 409 source-admission handling, API/backend changes, actions,
  service/provider/browser/API login, real projects, B6/C14, runtime and
  clinical/PV conclusions.

## Success criteria

- A wrong or missing identity cannot populate TFL/safety review state or show a
  success message.
- Existing valid action, selection-race and source-admission behavior remains.
- Focused Python contracts, Node suites, Vite and Ruff pass.

## Risk boundary and route

No action endpoint or runtime was called. Workflow route is recorded only and
not dispatched; direct Codex owns implementation and acceptance.

## Final evidence

- Direct Codex added the two success-response guards and one static contract.
- Focused Python/source set passed (151 passed, 17 existing warnings), all 22
  medical-monitoring Node suites passed, Vite build passed, and Ruff passed on
  changed contract files.
- No browser/runtime/live authority check was run because B6/C14 remain closed.

## Risk boundaries

- No TFL or safety action was executed; no source-admission state was changed.
- 8911 and 5174 remain stopped; B6 and C14 remain blocked and unchanged.
- This is not runtime, scientific, UAT or commercial acceptance.
