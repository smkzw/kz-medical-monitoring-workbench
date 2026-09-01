# Task Context: medical_monitoring_planned_read_identity_visible_ux_20260803

## Objective

Make existing PlannedModulePage read-response identity mismatches clear stale
state and visible across sources, evidence, TFL and safety/PV surfaces.

## Source and scope

- Workbench `frontend/src/App.jsx` `PlannedModulePage` read handlers.
- In scope: source registry, evidence manifest, TFL manifest/review, safety
  manifest/review/handoff stale-state clearing and visible identity messages.
- Out of scope: API/backend changes, action/confirmation calls, provider,
  browser/API login, real projects, B6/C14, runtime and clinical/PV
  conclusions.

## Success criteria

- Wrong or missing identities cannot leave stale project data displayed.
- Each affected surface exposes its existing message/error channel.
- Request-id and valid response behavior remains; focused Python contracts,
  Node suites, Vite and Ruff pass.

## Risk boundary and route

No read endpoint or runtime was called. Workflow route is recorded only and not
dispatched; direct Codex owns implementation and acceptance.

## Final evidence

- Direct Codex added visible identity messages and affected-state clearing for
  six PlannedModulePage read surfaces; the safety risk-index helper was already
  fail-closed from 5.12.
- Focused Python/source set passed (157 passed, 17 existing warnings), all 22
  medical-monitoring Node suites passed, Vite build passed, and Ruff passed on
  changed contract files.
- One stale static assertion was updated to reflect the deliberate separation
  of request-id and identity branches; no product behavior was weakened.
- No browser/runtime/live authority check was run because B6/C14 remain closed.

## Risk boundaries

- 8911 and 5174 remain stopped; B6 and C14 remain blocked and unchanged.
- This is not runtime, scientific, UAT or commercial acceptance.
