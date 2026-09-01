# Codex Review: medical_monitoring_primary_run_write_authorization_20260804

Date: 2026-08-04
Delegated-agent output: none; Codex implemented and reviewed directly. The
Hermes workflow guard was used for task bookkeeping only.

## Verdict

PASS for the bounded primary snapshot-run write authorization slice.

## Boundary Check

- No delegated agent was dispatched. Changes stayed within the monitoring
  router, module-contract test, and task/review/metrics/ledger evidence
  surfaces. No unrelated product or runtime path was changed.

## Codex Verification

`POST /runs` now calls the existing provider-neutral
`RUN_DETERMINISTIC_RULES` authorization before registry lookup, evaluation or
snapshot persistence. Missing principal is 503; a medical-writer principal is
403; offline factories opt out explicitly. Focused tests passed **119**,
adjacent identity/runtime/frontend contracts **176**, and full
`tests/test_monitoring*.py` passed **1936** with **25 warnings** in **485.58s**,
exit code **0**. Ruff and targeted `py_compile` passed. No browser, service,
provider, API login, runtime DB or real project ran; ports 8911/5174/8910/4173
remained empty.

## Delegated-Agent Output Review

The action mapping reuses the existing deterministic-rule permission and does
not invent a new identity policy. The route still preserves existing 201/200/
404 behavior once an authorized/offline call reaches the service.

## Residual Risk

Production snapshot generation remains fail-closed until the approved host
adapter supplies `request.state.monitoring_principal`. Protocol/rule authoring
write authorization, denied-attempt persistence, B6/C14, source-token/CAS,
approved-input, controlled runtime and real-project/Playwright/scientific/UAT
gates remain open or blocked.
