# Task Context: p8_readiness_version_cas_20260806

Created: 2026-08-06 03:10:04; completed: 2026-08-06 (Asia/Shanghai)
Objective: Bind P8 assurance readiness evaluation to the selected task version and fail closed on stale requests.
Task type: `finite_code_task`
Risk: `medium`
Execution: direct Codex patch; the guard-selected night route was recorded but no provider or delegated agent was dispatched.

## Source Of Truth

- `services/api/app/monitoring_assurance_service.py`: readiness service boundary.
- `services/api/app/monitoring_assurance_router.py`: FastAPI request/response and conflict mapping.
- `services/api/app/monitoring_assurance_repository.py`: `AssuranceVersionConflictError` and existing CAS semantics.
- `tests/test_monitoring_assurance_principal_route.py`: principal-bound route contracts and lifecycle tests.
- `records/active_slices/medical_monitoring_real_loop_gate_audit_20260804/CURRENT_REAL_LOOP_GATE_AUDIT.json`: current runtime authority (`read_only / blocked`).

## Scope

- In scope: pass `ReadinessRequest.expected_version` into the service; compare it with the persisted task version; map stale requests to the existing 409 `assurance_version_conflict` contract; add a no-mutation stale-version regression; write bounded evidence records.
- Out of scope: readiness evidence generation, medical review/completion actions, principal/session middleware, Safety/PV role selection, B6/C14/source-token/CAS activation gate, runtime/service/provider/browser/API login, real projects, SQLite/runtime data, and medical-writing files.

## Success Criteria

- A stale readiness request is rejected with HTTP 409 and `detail.code=assurance_version_conflict`.
- A stale request does not advance the task version or append an audit mutation.
- Existing fresh readiness route and assurance/identity contracts remain green.
- Changed Python files compile and pass Ruff; no runtime listener is started.

## Risk Boundaries

- Only the two assurance backend modules, one focused route test, and task evidence records may change.
- No shared App, frontend, medical-writing, database/runtime, service/provider/browser, or real-project writes.
- The real-loop gate remains authoritative and must stay `read_only / blocked`; this slice cannot grant activation or medical authority.

## Work Performed

1. Imported the existing repository `AssuranceVersionConflictError` into the service.
2. Added required `expected_version` to `MonitoringAssuranceService.evaluate_readiness` and fail-closed comparison against the freshly loaded task.
3. Passed the request version from the route and caught `MonitoringAssuranceError` through the existing conflict mapper.
4. Added `test_readiness_stale_version_fails_closed_without_mutation`.

## Verification

- `.venv/bin/python -m pytest -q tests/test_monitoring_assurance.py tests/test_monitoring_assurance_principal_route.py tests/test_monitoring_identity_authorization.py`: **117 passed**.
- `.venv/bin/python -m py_compile ...`: passed for the two modules and focused test.
- `ruff check` on the two modules and focused test: **All checks passed**.
- Prior P8 frontend slice remains independently verified at 37/37 Node files plus Vite build; this backend slice did not change frontend files.
- Ports 8911/5174/8910/4173 and the real-loop gate were rechecked after verification; no runtime activation was performed.

## Residual / Next Safe Action

P8 evidence generation, formal medical review, and completion action contracts remain pending and must stay behind principal, source-token/CAS, approved-input and medical authority gates. The next safe implementation is another offline feature-owned contract only if it does not require the unresolved Safety/PV decision; otherwise record the explicit role decision before touching that route.
