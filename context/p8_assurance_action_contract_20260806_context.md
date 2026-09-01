# Task Context: p8_assurance_action_contract_20260806

Created: 2026-08-06 03:19:09; completed: 2026-08-06 (Asia/Shanghai)
Objective: Expose server-owned P8 assurance evidence, medical-review and completion action contracts in the monitoring feature without client identity or gate bypass.
Task type: `finite_code_task`
Risk: `medium`
Execution: direct Codex patch; guard-selected night route recorded, but no provider or delegated agent dispatched.

## Source Of Truth

- `frontend/src/features/medical-monitoring/medicalMonitoringAssuranceApi.mjs`: feature-owned assurance API.
- `frontend/src/features/medical-monitoring/medicalMonitoringAssurance.mjs`: task/evidence/action policy model.
- `frontend/src/features/medical-monitoring/medicalMonitoringAssurance.test.mjs`: focused model/API contract tests.
- `services/api/app/monitoring_assurance_router.py`: existing server-owned action routes and strict payload schemas.
- `services/api/app/monitoring_assurance_repository.py`: existing CAS, idempotency and audit mutation semantics.
- `records/active_slices/medical_monitoring_real_loop_gate_audit_20260804/CURRENT_REAL_LOOP_GATE_AUDIT.json`: runtime authority (`read_only / blocked`).

## Scope

- In scope: feature API methods for full-recompute proof, rollups, medical review and completion; top-level stripping of transitional client identity fields; a fail-closed action-availability model enforcing evidence → review → readiness/completion order; focused and full feature tests/build; evidence records.
- Out of scope: changing the backend action routes, principal/session middleware, Safety/PV role model, B6/C14/source-token/CAS activation, runtime/provider/browser/API login, real projects, SQLite/runtime data, medical-writing files, or automatically triggering any action from the panel.

## Success Criteria

- All four action methods POST the project/task-scoped JSON endpoint with strict expected-version payloads.
- Feature serialization removes top-level `actor` and `confirmed_by`; server principal remains the only identity source.
- Action model blocks writes without task/version/principal/authority and permits completion only after evidence, medical review and readiness.
- Full medical-monitoring Node suite and Vite build pass; existing backend CAS/principal suite remains green.

## Risk Boundaries

- Only the two feature-owned model/API files and one feature test may change.
- Do not add UI triggers that could submit real evidence while the runtime gate is blocked; action methods are an explicit adapter for a later controlled UI.
- No shared App, medical-writing, database/runtime, service/provider/browser, real-project, B6/C14, source-token activation or Safety/PV writes.

## Work Performed

1. Added `serverOwnedTaskActionPayload` to remove client identity fields before serialization.
2. Added four project/task-scoped action methods: proof, rollups, medical review and completion.
3. Added `assuranceActionAvailability` with fail-closed prerequisites and ordered completion gates.
4. Added positive/negative model and payload tests.

## Verification

- `node --test src/features/medical-monitoring/*.test.mjs`: **37 files passed**; assurance model/API **40 passed**.
- `npm run build`: Vite **1,956 modules transformed**, build passed; existing >500 kB advisory retained.
- `node --check` for changed model/API: passed.
- Backend CAS/principal/identity evidence remains **117 passed** from the immediately preceding P8 CAS slice.
- No runtime listener, provider, browser or real project was started.

## Residual / Next Safe Action

The panel still does not invoke these mutation methods; controlled UI wiring requires current principal, source/evidence freshness, approved-input and medical authority. Next offline action may add a visible read-only action-status surface, but any submit control must be bound to the same gates and explicit user confirmation. Safety/PV remains a separate product/medical decision.
