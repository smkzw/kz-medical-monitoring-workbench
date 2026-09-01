# Codex Review: medical_monitoring_primary_read_authorization_20260804

Date: 2026-08-04
Delegated-agent output: none; Codex implemented and reviewed directly. The
Hermes workflow guard was used for task bookkeeping only.

## Verdict

PASS for the bounded primary read authorization slice.

## Boundary Check

- No delegated agent was dispatched. Changes stayed within the router, main
  production wiring, explicit offline test factories, focused tests, and the
  task/review/metrics/ledger evidence surfaces.
- No unrelated product source or runtime was changed.

## Codex Verification

Source review confirmed that summary, deep-link, current risk snapshot,
current risk export and risk-taxonomy reads call the existing provider-neutral
`READ_MONITORING` authorization before lookup. `main.py` wires the existing
host principal adapter with fail-closed production defaults; offline bypasses
are explicit in test factories. Focused tests passed **104**, adjacent tests
passed **161**, and full `tests/test_monitoring*.py` passed **1936** with
**25 warnings** in **490.15s**, exit code **0**. Ruff and targeted `py_compile`
passed. No browser, service, provider, API login, runtime database or real
project was run because the upstream gates remain closed; reserved ports
8911/5174/8910/4173 were empty.

## Delegated-Agent Output Review

The implementation is traceable to the existing principal/ACL/runtime route
context seams and preserves downstream 404/409/export semantics. It does not
claim to provide host session middleware, external signature verification,
protocol/rule-pack authorization, or live-project acceptance.

## Residual Risk

Production reads intentionally remain 503 until an approved host adapter
populates `request.state.monitoring_principal`. Denied-attempt persistence,
B6/C14, source-token/CAS, approved-input, controlled runtime, real-project and
Playwright/scientific/UAT gates remain open or blocked. No live service or
real-project test should be started from this slice.
