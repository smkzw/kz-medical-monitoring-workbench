# Codex Review: medical_monitoring_ai_service_hash_shape_revalidation_20260805

Date: 2026-08-05
Review mode: Codex direct, source-only

## Verdict

Pass for the bounded source-only integrity slice. This does not establish
provider, runtime, browser, clinical, B6/C14 or commercial-release readiness.

## Hermes Role

Hermes was not dispatched because the authoritative real-loop gate is
read-only and forbids provider/runtime activation. No external agent output is
treated as acceptance evidence.

## Boundary Check

- Product changes are limited to
  `services/api/app/monitoring_ai_service.py` and
  `tests/test_monitoring_ai_service.py`.
- Durable context, review, metrics and task records are task-scoped.
- No provider, service, port, browser/Playwright, API login, real project or
  medical-writing action occurred.

## Codex Verification

- Service suite: **451 passed** in 11.04s.
- All discovered `tests/test_monitoring_ai*.py` source suites with `real_`
  excluded: **788 passed, 4 deselected, 17 warnings** in 14.54s.
- Compileall passed for changed service, contract and service-test modules.
- Guard prompt preflight passed.
- Reserved ports 8911, 5174, 8910 and 4173 were empty.
- Ruff is unavailable in the current venv/PATH; lint remains unverified.
- The authoritative gate remains `read_only`/`blocked`; real-loop and browser
  acceptance were intentionally not attempted.

## Delegated-Agent Output Review

No delegated-agent output was used. The service now rejects present required
and optional profile/source/revision/repair digests unless they are exact
lowercase 64-hex SHA-256 values, and no longer normalizes the current revision
resolver or deterministic-repair profile comparisons. A provider payload
tamper regression covers the post-persistence read boundary. Non-digest labels
and optional absence remain compatible. No unsupported runtime or clinical
claims are made.

## Residual Risk

Other AI service/repository surfaces may still contain independent
normalization logic and require separate bounded audits. Ruff/lint is not
verified. Formal B6, source-token/CAS replay, host/runtime identity,
real-project mode coverage, Playwright role rounds and final release dossier
remain blocked by authority.
