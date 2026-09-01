# Codex Review: medical_monitoring_metric_api_20260805

Date: 2026-08-05
Delegated-agent output: direct Codex route; no delegated agent.

## Verdict

Pass for the declared read-only API boundary. This makes the LOOP 5.318
candidate contract reviewable by a future workbench surface, but it is not
medical confirmation, P1-02 completion, runtime acceptance, P10 completion or
commercial readiness.

## Boundary check

- The new service reads protocol facts and a complete frozen field profile and
  delegates all candidate validation to the existing strict builder.
- Main-app wiring adds one service instance and one GET router only.
- No metric/rule/fact/mapping confirmation or persistence path was introduced;
  no provider or worker wake is reachable from the route.
- No medical-writing file, frontend file, port, browser session or real project
  was touched.

## Evidence reviewed

1. Focused API/service tests verify candidate-only response metadata,
   unconfirmed-fact issue conservation, project/batch mismatch rejection,
   frozen-batch rejection and stable HTTP error detail.
2. Main import/route discovery confirms exactly one metric-candidate GET route.
3. Full monitoring suite passes **2540/2540** after the main-app wiring.

## Reviewer findings

- Identity binding is explicit at three levels: canonical project, protocol
  version owner, and listing batch owner; the field profile is checked again
  against project and batch ids.
- Passing all protocol facts preserves review visibility for unconfirmed or
  unsupported source facts instead of silently filtering them.
- Response metadata makes it difficult for a consumer to mistake a candidate
  for a medically confirmed metric.
- The route is deliberately not a POST/decision endpoint; confirmation remains
  a future, separately governed medical action.

## Residual risk

- No UI consumer or browser/scientific visual acceptance exists yet.
- The existing profiler may use its deterministic derived cache; this route was
  not served while the runtime gate was blocked, so live cache behavior remains
  unverified here.
- The formal B6/source-token/CAS/runtime gate remains blocked, so independent
  AI, real-project and commercial controls are unproven.
- `ruff` is not installed in this runtime; py_compile and pytest are the
  available deterministic checks.

## Hermes review-gate

This was direct Codex source work; no external provider or delegated agent was
used. The verification file under
`records/active_slices/medical_monitoring_metric_api_20260805/` is the evidence
source for the review gate.
