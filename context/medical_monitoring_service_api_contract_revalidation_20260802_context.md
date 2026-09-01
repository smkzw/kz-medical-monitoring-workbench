# Context: medical_monitoring_service_api_contract_revalidation_20260802

## Goal

Revalidate the existing medical-monitoring service/API contracts in the actual
product virtual environment, because older evidence described a missing global
`cryptography` dependency. The check must not turn local unit/contract evidence
into runtime or clinical acceptance.

## In scope

- Current product `.venv` dependency import check.
- Collection and execution of the six existing monitoring API/router/assurance
  test modules.
- Port and shared-runtime boundary confirmation.

## Out of scope

- Starting 8911/5174 or any service/provider/browser.
- Shared runtime or SQLite writes.
- Real RUX, MG-K10 or MY009 onboarding/LOOP.
- B6/C14 activation, formal reviewer outcome, medical/scientific conclusion or
  commercial-release decision.
- Any medical-writing source or protected frontend change.

## Evidence

- Product `.venv`: `cryptography 49.0.0`.
- Collection: 61 tests.
- Execution: 61 passed, 17 pre-existing deprecation warnings, 17.16 seconds.
- Current B6 remains `pending_review`; C14/release remain fail-closed.

