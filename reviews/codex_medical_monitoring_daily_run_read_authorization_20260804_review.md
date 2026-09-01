# Codex Review: medical_monitoring_daily_run_read_authorization_20260804

Date: 2026-08-04
Delegated-agent output: none; Codex implemented and reviewed this slice
directly. The Hermes workflow guard supplied task/review-gate bookkeeping only.

## Verdict

PASS for the bounded daily-run read authorization slice; not an
authentication, browser visual, e-signature, runtime or commercial-release
acceptance.

## Boundary Check

- Codex changed only the daily-run router, production wiring, daily-run route
  tests and task-scoped context/prompt/review/metrics/record surfaces.
- No authentication middleware, token/cookie parsing, fallback production
  identity, new ACL action, daily-run write route, schema/repository/service,
  frontend, audit write, service, browser, provider/API login, runtime
  database, real project, B6/C14 or approved-input gate was touched.
- The explicit `require_server_principal=False` branch is only used by the
  offline legacy test harness; `main.py` wires the existing host adapter and
  keeps `require_server_principal=True`.

## Codex Verification

- Dedicated daily-run router suite: **17 passed**.
- Adjacent daily-run/identity/runtime/frontend contracts: **153 passed**.
- Full `tests/test_monitoring*.py`: **1912 passed, 25 warnings in 508.20s**;
  process exit **0**.
- Ruff for the changed router/tests and targeted `py_compile` passed. A broad
  Ruff invocation including legacy `main.py` reports 18 pre-existing unused
  import/local findings; the wiring line introduced no new finding.
- Ports 8911, 5174, 8910 and 4173 were checked empty. No service, browser,
  provider, API login or real-project action was run.

## Review Findings

- The list, readiness, detail and AI-progress read routes now bind canonical
  project and server principal to `READ_MONITORING` before repository/service
  lookup. Missing/malformed identity returns 503; unscoped or unauthorized
  principals return 403; scoped medical managers retain downstream 200/404/
  analysis-unavailable behavior.
- The read guard never accepts client actors or mutates state. The resolver
  remains provider-neutral and only reads a verified principal supplied by the
  host.

## Residual Risk

The actual host verified-session middleware and denied-attempt persistence are
unresolved, and daily-run writes are not yet covered by this slice. B6/C14,
source-token/CAS, approved-input, controlled runtime, real-project and
Playwright/scientific/UAT gates remain open or blocked.
