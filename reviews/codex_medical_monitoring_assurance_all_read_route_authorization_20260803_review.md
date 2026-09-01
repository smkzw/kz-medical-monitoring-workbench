# Codex Review: medical_monitoring_assurance_all_read_route_authorization_20260803

Date: 2026-08-04
Delegated-agent output: none; Codex implemented and reviewed this slice
directly. The Hermes workflow guard supplied task/review-gate bookkeeping only.

## Verdict

PASS for the bounded assurance read-route authorization slice; not an
authentication, browser visual, e-signature, runtime or commercial-release
acceptance.

## Boundary Check

- Codex changed only the assurance router, its principal-route tests, and the
  task-scoped context/prompt/review/metrics/record surfaces.
- No authentication middleware, token/cookie parsing, fallback production
  identity, new provider, schema migration, frontend, audit write, service,
  browser, provider/API login, runtime database, real project, B6/C14 or
  approved-input gate was touched.
- The explicit `require_server_principal=False` branch remains isolated to the
  legacy offline route harness; `main.py` keeps `require_server_principal=True`.

## Codex Verification

- Dedicated assurance principal-route suite: **29 passed**.
- Focused assurance/principal regression: **52 passed**.
- Adjacent identity/audit/runtime/frontend contracts: **172 passed**.
- Full `tests/test_monitoring*.py`: **1903 passed, 25 warnings in 541.78s**;
  process exit **0**.
- Ruff and targeted `py_compile` passed for the changed router/tests.
- Ports 8911, 5174, 8910 and 4173 were checked empty. No service, browser,
  provider, API login or real-project action was run.

## Review Findings

- `GET /tasks`, `GET /tasks/{task_id}`, `POST /readiness`,
  `GET /full-recompute-proof` and `GET /rollups` now invoke the same
  provider-neutral `READ_RISK_AUDIT` principal/tenant/project/ACL decision
  before task or evidence lookup.
- Missing or malformed server identity fails closed with 503; an unscoped
  system-admin principal is rejected with 403; a scoped medical manager keeps
  existing 200/404 semantics. Read routes never accept a client actor or
  construct a write audit context.
- The result is a data-boundary hardening, not proof that a real host session
  can authenticate: the host middleware still does not populate
  `request.state.monitoring_principal`.

## Residual Risk

The real verified-session middleware and denied-attempt persistence policy are
still unresolved. B6/C14, source-token/CAS, approved-input, controlled runtime,
real-project, Playwright/scientific and UAT gates remain open or blocked.
