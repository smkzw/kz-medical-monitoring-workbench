# Codex Review: medical_monitoring_daily_run_write_authorization_20260804

Date: 2026-08-04
Delegated-agent output: none; Codex implemented and reviewed this slice
directly. The Hermes workflow guard supplied task/review-gate bookkeeping only.

## Verdict

PASS for the bounded daily-run write authorization slice; not an
authentication, browser visual, e-signature, runtime or commercial-release
acceptance.

## Boundary Check

- Codex changed only the daily-run router, its production wiring, the daily-run
  route tests and task-scoped context/prompt/review/metrics/record surfaces.
- No authentication middleware, token/cookie parsing, fallback production
  identity, new ACL action, repository/service/schema, frontend visual surface,
  audit write, service, browser, provider/API login, runtime database, real
  project, B6/C14 or approved-input gate was touched.
- The explicit `require_server_principal=False` branch remains limited to the
  offline legacy harness; production `main.py` keeps the existing host adapter
  and fail-closed setting.

## Codex Verification

- Dedicated daily-run router suite: **37 passed**.
- Adjacent daily-run/identity/runtime/frontend contracts: **173 passed**.
- Full `tests/test_monitoring*.py`: **1932 passed, 25 warnings in 487.23s**;
  process exit **0**.
- Ruff for changed router/tests and targeted `py_compile` passed. Broad Ruff
  on legacy `main.py` retains 18 pre-existing unused import/local findings;
  the production wiring line introduced no new finding.
- Ports 8911, 5174, 8910 and 4173 were checked empty. No service, browser,
  provider, API login or real-project action was run.

## Review Findings

- All nine daily-run POST routes now authorize before repository/service
  mutation. Existing actions are used explicitly: intake, deterministic rules,
  AI candidate review and risk disposition. Production actors are derived from
  the verified principal; payload actor/confirmed_by values are ignored.
- Missing/malformed principal returns 503; unauthorized role/scope returns
  403; a scoped medical manager can reach the existing path and the event actor
  is the verified principal ID. Existing CAS, lease, idempotency and downstream
  error handling remain in place.

## Residual Risk

The host verified-session middleware and denied-attempt persistence remain
unresolved. Confirmation has role/project authorization but is not claimed as
final e-signature/reauth acceptance. B6/C14, source-token/CAS, approved-input,
controlled runtime, real-project and Playwright/scientific/UAT gates remain
open or blocked.
