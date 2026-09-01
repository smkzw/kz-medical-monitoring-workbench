# Task Context: medical_monitoring_safety_projection_page_identity_20260803

## Objective

Require canonical project identity for every Safety/PV risk projection summary
and paginated snapshot response while preserving alias request paths.

## Source and scope

- Workbench `frontend/src/App.jsx` `fetchCompleteMonitoringRiskIndex` and the
  Safety/PV risk projection effect.
- Backend summary and risk-snapshot contracts were inspected and expose
  canonical `project_id`.
- In scope: per-response identity validation and canonical expected-id wiring.
- Out of scope: API/backend changes, risk queries, service/provider/browser/API
  login, real projects, B6/C14, runtime and clinical/PV conclusions.

## Success criteria

- Summary, first page and every later page must match the expected canonical
  project before the combined risk index is returned.
- Alias remains the request path while active canonical project is the expected
  identity.
- Focused Python contracts, Node suites, Vite and Ruff pass.

## Risk boundary and route

No risk endpoint or runtime was called. Workflow route is recorded only and not
dispatched; direct Codex owns implementation and acceptance.

## Final evidence

- Direct Codex added a shared identity validator to the summary/pagination
  helper and passed the canonical active project from Safety/PV projection.
- Focused Python/source set passed (154 passed, 17 existing warnings), all 22
  medical-monitoring Node suites passed, Vite build passed, and Ruff passed on
  changed contract files.
- No browser/runtime/live authority check was run because B6/C14 remain closed.

## Risk boundaries

- 8911 and 5174 remain stopped; B6 and C14 remain blocked and unchanged.
- This is not runtime, scientific, UAT or commercial acceptance.
