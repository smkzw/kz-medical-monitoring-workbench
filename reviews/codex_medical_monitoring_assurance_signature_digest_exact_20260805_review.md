# Codex Review: medical_monitoring_assurance_signature_digest_exact_20260805

Date: 2026-08-05 (Asia/Shanghai)
Delegated-agent output: `runs/codex_medical_monitoring_assurance_signature_digest_exact_20260805.md`

## Verdict

**Pass for the bounded source-only assurance context slice.** The downstream
write context now rejects non-canonical signature evidence bytes rather than
normalizing them.

## Hermes Role

Hermes was not dispatched. The authoritative real-loop gate is read-only and
blocks provider/runtime activation; Codex direct verification is the accepted
route.

## Boundary Check

- Product changes are limited to `services/api/app/monitoring_assurance_repository.py`
  and `tests/test_monitoring_assurance.py`; evidence is task-scoped.
- No authentication/e-signature provider, service, reserved port,
  browser/Playwright, API login, real project, medical-writing surface, B6/C14
  activation or release action occurred.

## Codex Verification

- Focused signature-shape subset: **4 passed**.
- Assurance/identity/runtime adjacency: **134 passed** in 1.99s.
- `compileall` passed for the changed repository and test modules.
- Repository hash:
  `c4cc4cb8276d3dc64d16c8a3337eed325709974798573c6921425987c511f099`;
  test hash `5d72107c04dbb395a8a00a5bc08a6f935370de71ebb72de2489fba4cb20ffa96`.
- Ruff is unavailable in the current venv/PATH, so lint is unverified.
- The authoritative gate remains `mode=read_only`, `status=blocked`; provider,
  runtime and write authority are false. Ports 8911, 5174, 8910 and 4173 were
  not started.
- Browser, provider, API login and real-project evidence was not run because
  the formal gate blocks it.

## Direct Work Review

- `None`/empty optional evidence remains empty; every non-empty value must be a
  string of exactly 64 lowercase hexadecimal characters.
- The parser no longer calls `str`, `strip` or `lower` on identity-bound
  signature evidence.
- Existing route-level authorization still validates the request token before
  constructing this context; this downstream check closes the direct-context
  bypass without adding a new signature scheme.

## Residual Risk

No external e-signature is verified by this contract, and no live principal,
authorization, provider/runtime, source-token/CAS, browser, clinical,
scientific/visual or five-project real-loop evidence is established. Formal
B6/C14 outcomes and P10 activation remain blocked. Ruff/lint remains
unverified.
