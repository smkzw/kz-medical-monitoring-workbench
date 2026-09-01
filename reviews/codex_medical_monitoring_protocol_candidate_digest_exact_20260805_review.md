# Codex Review: medical_monitoring_protocol_candidate_digest_exact_20260805

Date: 2026-08-05 (Asia/Shanghai)
Delegated-agent output: `runs/codex_medical_monitoring_protocol_candidate_digest_exact_20260805.md`

## Verdict

**Pass for the bounded source-only protocol-candidate slice.** Candidate
lineage and frozen evidence reads now reject non-canonical digest bytes instead
of normalizing them.

## Hermes Role

Hermes was not dispatched. The authoritative gate is read-only and blocks
provider/runtime activation; Codex direct verification is the accepted route.

## Boundary Check

- Product changes are limited to
  `services/api/app/monitoring_protocol_preparation_service.py` and
  `tests/test_monitoring_protocol_preparation.py`; evidence is task-scoped.
- No protocol source files, provider, service, reserved port,
  browser/Playwright, API login, real project, medical-writing surface, B6/C14
  activation or release action was touched.

## Codex Verification

- Focused preparation suite: **49 passed** in 2.09s; digest/lineage subset **5
  passed**.
- Protocol listing-precheck/rule/API/repository/review adjacency: **121 passed**
  in 3.98s.
- `compileall` passed for the changed service and test modules.
- Service hash:
  `1f631d229482109c86d0f9e886bb91443d2e6c09bebd18426d6daa25c801f9fe`;
  test hash `b89053219266ae5944c59f5288ab30da975320ccd0619d6ddfeb8b65ba4cc34f`.
- Ruff is unavailable in the current venv/PATH, so lint is unverified.
- The authoritative gate remains `mode=read_only`, `status=blocked`, and
  reserved ports 8911, 5174, 8910 and 4173 were not started.
- Browser, API login, provider, runtime and real-project evidence was not run
  because the formal gate blocks it.

## Direct Work Review

- Expected input revision is accepted only as an exact lowercase 64-hex string;
  malformed values produce the existing candidate-source-stale denial.
- Frozen evidence content hashes must already be exact lowercase 64-hex strings
  and match the candidate evidence; no `str`, `strip` or `lower` rewrite is
  performed for that identity field.
- Existing source-revision text trimming remains intentionally unchanged and
  is not a digest normalization path.

## Residual Risk

The candidate's medical interpretation, live source registry, provider/runtime,
authorization, source-token/CAS replay, browser, clinical/scientific/visual
quality and five-project real-loop acceptance remain unproven. Formal B6/C14
outcomes and P10 activation remain blocked. Ruff/lint is unverified.
