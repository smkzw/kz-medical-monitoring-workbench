# Codex Review: medical_monitoring_route_scroll_restore_20260806

Date: 2026-08-06
Delegated-agent output: not dispatched; the runner reservation is retained only for workflow traceability.

## Verdict

**Pass for this bounded source/UI slice; not a runtime, clinical, B6/C14, or commercial-release acceptance.**

## Boundary Check

- No delegated agent was dispatched. Codex kept the change inside the task's
  declared frontend source/test/dist and evidence-record paths.
- No backend, database, service, provider, browser, Playwright, API login,
  real-project, medical-writing, B6, or C14 path was activated.

## Codex Verification

- Added a bounded `risk_scroll_top` route key with fail-closed normalization and
  stable project/scope/site/subject/query restoration key.
- Added a browser-only, 120 ms throttled restoration hook. It writes only the
  existing route view state and never risk, source, batch, or medical state.
- Wired Checklist scope/query changes to clear stale scroll offsets.
- `node --test frontend/src/features/medical-monitoring/*.test.mjs`: **35 test
  files passed, 0 failed**; new scroll module 8 checks and route module 56
  checks passed.
- `npm run build` in `frontend/`: **1957 modules transformed; build passed**.
  The existing >500 kB bundle advisory remains.
- The four-file Python frontend contract command returned **160 passed, 4
  failed**. The four failures are pre-existing static contract mismatches in
  source grouping/Timeline/source-body assertions and do not reference this
  slice's scroll modules or route key; they remain explicitly recorded in the
  verification record rather than being silently treated as a green full
  frontend gate.
- Live browser/visual checks were not run because the formal real-loop gate is
  still `read_only / blocked`.

## Delegated-Agent Output Review

Hermes was not dispatched because the active read-only gate forbids execution;
its workflow reservation is traceability only. No delegated output exists.
Codex reviewed the route-state contract, hook,
MonitoringPage wiring, focused tests, build output, and current gate directly.
The implementation does not change source authority, risk identity, medical
disposition, API contracts, runtime SQLite, or the parallel medical-writing
surface. The four unrelated static failures are a known adjacent backlog, not
evidence of a failed scroll implementation.

## Residual Risk

- Desktop rendering, keyboard/visual behavior, real project density, clinical
  correctness, provider quality, B6 formal outcomes, C14 activation, and
  commercial release remain unverified or blocked.
- Keep 8911/5174/8910/4173 stopped and do not run real LOOP/canary work until
  the five formal hash-bound B6 outcomes are submitted and source-token/CAS
  revalidation opens the gate.
