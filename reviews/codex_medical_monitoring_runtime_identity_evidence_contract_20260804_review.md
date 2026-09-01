# Codex Review: medical_monitoring_runtime_identity_evidence_contract_20260804

Date: 2026-08-04  
Route: Codex direct; no Hermes or external-agent dispatch

## Verdict

`PASS — accepted_slice_complete`

## Boundary Check

- Changes are limited to the new provider-neutral evidence validator, focused tests, and this slice's records/review/metrics.
- No runtime principal, host attestation, B6/C14 state, source/CAS state, service, provider, browser, database, real-project data, or medical outcome was created or changed.
- 8911, 5174, 8910 and 4173 remained stopped.

## Codex Verification

- Existing runtime-principal, route-context, upstream-assembly and readiness contracts were read before implementation.
- New focused tests and the adjacent regressions passed: 54/54.
- Full `tests/test_monitoring*.py` regression passed: 2042/2042 in 528.16 s with 25 existing warnings.
- Python compile check passed for the new module and test.
- Current missing-evidence replay produced `blocked`, `observed_status=missing`, `runtime_identity_verified=false` and all authority flags false.
- Current approved-input dry-run replay produced `blocked`, `approved_input_ready=false`, 15 issues and the exact existing base/controlled report hashes; no source-batch binding was synthesized.
- Ruff was not run because the current environment has no `ruff` executable; this is recorded as an environment limitation, not a pass claim.

## Findings

- The new contract keeps evidence and readiness separate: a fresh `not_proven` observation is not a verified runtime gate.
- A `proven` observation requires a safe public principal snapshot, exact identity digest, complete five-project scope, valid current time window, safe attestation fields and an explicit caller-supplied host verifier returning strict `True`.
- Raw session/token/cookie/secret fields, hash/ref drift, scope/time drift and authority-flag attempts are rejected fail-closed.
- Even an accepted host-attestation verification cannot set runtime activation, provider, write, migration or medical authority flags in this diagnostic report.
- The report-to-upstream projection is fail-closed: `missing`, `not_proven` and `blocked` never become `proven`; only a fresh verified report emits the `proven` status for a later assembly pass.

## Residual Risk

No real server host attestation exists in the current filesystem, so the runtime gate remains missing. The module does not prove authentication, cryptographic signatures or production integration by itself. B6 formal reviewer outcomes, approved-input/source-token/aggregate-CAS evidence, controlled runtime, Playwright/scientific/visual acceptance and commercial release remain open.

## Delegated-Agent Output Review

No delegated agent or Hermes session was used; Codex performed the implementation review and acceptance directly.
