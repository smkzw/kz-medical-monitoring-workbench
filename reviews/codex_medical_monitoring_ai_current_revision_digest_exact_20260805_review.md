# Codex Review: medical_monitoring_ai_current_revision_digest_exact_20260805

Date: 2026-08-05 (Asia/Shanghai)
Delegated-agent output: `runs/codex_medical_monitoring_ai_current_revision_digest_exact_20260805.md`

## Verdict

**Pass for the bounded source-only AI router slice.** Persisted mapping
revision reconstruction now fails closed on non-canonical profile digests and
malformed profile roots without changing provider or runtime behavior.

## Hermes Role

Hermes was not dispatched. The authoritative real-loop gate is read-only and
blocks provider/runtime activation; Codex direct verification is the accepted
route for this source-only slice.

## Boundary Check

- Product changes are limited to `services/api/app/monitoring_ai_router.py` and
  `tests/test_monitoring_ai_api.py`; task evidence is in the declared context,
  records, review and metrics surfaces.
- No provider, service, reserved port, browser/Playwright, API login, real
  project, medical-writing surface, B6/C14 activation or release action was
  touched.

## Codex Verification

- Focused router API suite: **27 passed** in 0.96s; current-revision subset
  **5 passed**.
- All discovered `tests/test_monitoring_ai*.py` source suites with `real_`
  excluded: **796 passed, 4 deselected, 17 warnings** in 14.61s.
- `compileall` passed for the changed router and API-test modules.
- Parser hash: `434a09cd723d6a1f6aceee838a99703ae873a74e64879b76f660c5f9209cfa63`;
  test hash: `1a2a19dbe68f73d46d801f39a14c8b30339db668e06c78313722b110fb3dbd98`.
- Ruff is unavailable in the current venv/PATH, so lint is unverified.
- The authoritative gate remains `mode=read_only`, `status=blocked`, with
  provider/runtime/write authority false; reserved ports 8911, 5174, 8910 and
  4173 remain empty/not started.
- Browser, API login, provider, runtime and real-project evidence was not run
  because the formal gate blocks it.

## Direct Work Review

- The persisted field-profile root is checked before reading fields.
- The profile digest is validated with the existing exact lowercase 64-hex
  router contract and is returned unchanged; a malformed value returns an
  unavailable revision instead of being normalized or compared.
- Existing batch-id trimming is retained as a non-digest compatibility rule;
  no new identity scheme or external dependency was introduced.

## Residual Risk

Provider responses, live runtime identity/authorization, source-token/CAS
replay, browser role rounds, clinical/scientific/visual quality and five-project
real-loop evidence remain unproven. Formal B6/C14 outcomes and the P10
activation sequence remain blocked. Ruff/lint remains unverified.
