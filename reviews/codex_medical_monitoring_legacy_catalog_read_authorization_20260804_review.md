# Codex Review: medical_monitoring_legacy_catalog_read_authorization_20260804

Date: 2026-08-04 (Asia/Shanghai)
Delegated-agent output: none; direct Codex implementation.

## Verdict

**PASS — the two legacy catalog reads are bound to the existing read action.**
No new action, role, middleware or cross-module policy was introduced.

## Boundary Check

- Work stayed inside the workbench source, tests and this task's durable
  context/review/metrics/active-slice records.
- No service, browser, provider, API login, runtime database, migration or real
  project was touched.

## Codex Verification

- `get_risks` and `get_data_batches` canonicalize the project, then call
  `_authorize_legacy_monitoring_action(..., READ_MONITORING)` before `repo.risks`
  or `repo.batches`; responses use the canonical project id.
- Focused suite: **27 passed, 17 existing warnings, 17.09s**.
- `python -m py_compile` passed for `main.py`, `test_monitoring_risk_index_api.py`
  and `test_contracts.py`.
- Full `tests/test_monitoring*.py`: **1940 passed, 25 existing warnings,
  539.76s**, exit code 0. Hermes review-gate is the remaining formal closure
  check.

## Delegated-Agent Output Review

- No delegated output was used. The decision is directly traceable to the
  existing action matrix and route inventory.
- Dashboard and workbench-inbox are intentionally not treated as generic
  monitoring reads; they remain a separate cross-module policy-gap decision.

## Residual Risk

Host verified-session middleware is still absent, so production catalog reads
remain fail-closed with 503. Full B6/C14 activation, source-token/CAS,
approved-input, controlled runtime and real-project/UAT gates remain closed.
