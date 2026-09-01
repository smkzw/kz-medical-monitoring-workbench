# Codex Review: medical_monitoring_ai_router_hash_shape_revalidation_20260805

Date: 2026-08-05
Review mode: Codex direct, source-only

## Verdict

Pass for the bounded source-only router integrity slice. This does not
establish provider, runtime, browser, clinical, B6/C14 or commercial-release
readiness.

## Hermes Role

Hermes was not dispatched because the authoritative real-loop gate is
read-only and forbids provider/runtime activation. No external agent output is
treated as acceptance evidence.

## Boundary Check

- Product changes are limited to `services/api/app/monitoring_ai_router.py` and
  `tests/test_monitoring_ai_api.py`.
- Durable context, review, metrics and task records are task-scoped.
- No provider, service, port, browser/Playwright, API login, real project or
  medical-writing action occurred.

## Codex Verification

- Focused router API suite: **23 passed** in 1.05s.
- All discovered `tests/test_monitoring_ai*.py` source suites with `real_`
  excluded: **792 passed, 4 deselected, 17 warnings** in 18.60s.
- Compileall passed for changed router/service/API-test modules.
- Guard prompt preflight passed.
- Reserved ports 8911, 5174, 8910 and 4173 were empty.
- Ruff is unavailable in the current venv/PATH; lint remains unverified.
- The authoritative gate remains `read_only`/`blocked`; live API/browser and
  real-loop acceptance were intentionally not attempted.

## Delegated-Agent Output Review

No delegated-agent output was used. Mapping assemble/adopt requests now
require exact lowercase 64-hex digests. Router status and legacy/adoption
matching compares persisted profile/input values without strip/lower rewrite;
malformed persisted status rows are skipped closed. Existing valid mapping
status/adoption tests remain green. No unsupported runtime or clinical claims
are made.

## Residual Risk

Daily-run AI locator/source-binding paths and other non-router repository
surfaces may still need separate bounded integrity audits. Ruff/lint is not
verified. Formal B6, source-token/CAS replay, host/runtime identity,
real-project mode coverage, Playwright role rounds and final release dossier
remain blocked by authority.
