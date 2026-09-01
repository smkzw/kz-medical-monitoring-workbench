# Codex Review: medical_monitoring_phase_b7_shared_risk_projection_20260801

Date: 2026-08-02 00:05 CST
Execution: Codex direct; no Hermes route, conference, or sub-agent was used.
Changed source/test:
- `frontend/src/features/medical-monitoring/medicalMonitoringRiskProjection.mjs`
- `frontend/src/features/medical-monitoring/medicalMonitoringRiskProjection.test.mjs`

## Verdict

**Pass for the isolated read-only shared risk projection contract; runtime/UI integration
remains a later controlled step.**

## Boundary Check

- Only the new projection module/test and task records were changed; `App.jsx`, API
  clients, runtime databases, services and medical-writing paths were untouched.
- The projection consumes canonical aggregate-shaped rows only. It does not read inbox
  state, create a second fact source, infer categories from title text, or persist data.
- Missing/ambiguous identity and mixed project/trial rows fail closed; exact duplicate
  instances are counted once and conflicting duplicate payloads fail closed.

## Codex Verification

- New projection test: **16 passed**; existing `medicalMonitoringModels` test: **44 passed**.
- All medical-monitoring frontend Node feature tests passed in one sweep:
  API 123, checklist 20, daily-run gate 7, field mapping 6, models 44, project scope 14,
  project-switch isolation 23, protocol preparation 17, risk projection 16, route state 40,
  rule release 63, template recommendation 22, subject models (pass).
- `node --check` passed for the new module and test.
- No browser/runtime check was run by scope; the output is a contract for later UI wiring,
  not evidence that the live page has been migrated.

## Direct Work Review

- Fact fields (`findingClass`, category, severity, detection status), workflow fields
  (`unread`, needs-action, disposition/query) and evidence fields (source/rule/engine,
  locators) remain separate.
- Explicit Timeline/Profile/AE/lab/vitals/ECG/PD IDs are preserved as sorted arrays;
  display text cannot create a clinical link.
- Project/site/subject rollups use distinct risk-instance IDs and deterministic ordering;
  site and subject groups remain drilldown projections, not new authority records.

## Residual Risk

- This does not replace the existing `riskIndexRowsFromApi` path or wire the new contract
  into `App.jsx`; doing so requires an approved authority/API integration slice after B6
  review and migration gates.
- It does not prove visual density, chart interaction, responsive layout, or browser
  acceptance. Those remain Phase E/H work and must be validated in the real workbench.
- B6 mapping approval remains pending and continues to block any runtime dual-read,
  migration or disposition write.
