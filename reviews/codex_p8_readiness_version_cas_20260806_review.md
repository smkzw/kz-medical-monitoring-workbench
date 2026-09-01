# Codex Review: p8_readiness_version_cas_20260806

Date: 2026-08-06 (Asia/Shanghai)
Delegated-agent output: not dispatched; the guard reservation is retained only as route metadata.

## Verdict

**Pass for the bounded offline CAS slice.** It is not a runtime, medical, real-project or commercial acceptance.

## Hermes

The guard-created Hermes prompt was not dispatched. No Hermes output is treated as evidence or final authority.

## Boundary Check

- Product source changes are limited to `services/api/app/monitoring_assurance_service.py` and `services/api/app/monitoring_assurance_router.py`.
- Test change is limited to `tests/test_monitoring_assurance_principal_route.py`.
- Evidence is limited to this task's context/review/metrics and the active-slice records.
- No provider, delegated agent, service, browser/Playwright, API login, runtime/SQLite, real project, B6/C14, source-token/CAS activation, Safety/PV or medical-writing action occurred.

## Codex Verification

- Focused backend assurance/principal/identity suite: **117 passed**.
- `py_compile` for both changed modules and focused test: passed.
- Ruff check for both modules and focused test: **All checks passed**.
- The new regression proves stale `expected_version` returns HTTP 409 with `assurance_version_conflict`, leaves the persisted version unchanged, and leaves only the create audit event.
- Existing fresh readiness route remains covered by the principal-route parameterized test.

## Implementation Review

The route already required a strict integer version but previously discarded it. The service now reloads the task and compares the version before readiness evaluation; the route passes the request version and maps the repository conflict through the existing 409 contract. This is the smallest backend-first correction and does not add an audit mutation to a read-only readiness check.

## Residual Risk

The actual session principal, source freshness, evidence generation, medical review/signature, Safety/PV authorization, B6 hash-bound outcomes, controlled runtime and real-project LOOP remain unproven. The current gate is still `read_only / blocked`; no claim of commercial readiness is made.
