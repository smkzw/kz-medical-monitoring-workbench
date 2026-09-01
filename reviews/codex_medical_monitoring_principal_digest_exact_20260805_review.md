# Codex Review: medical_monitoring_principal_digest_exact_20260805

Date: 2026-08-05 (Asia/Shanghai)
Delegated-agent output: `runs/codex_medical_monitoring_principal_digest_exact_20260805.md`

## Verdict

**Pass for the bounded source-only slice.** The frontend principal parser now
rejects non-canonical digest bytes instead of normalizing them, while leaving
the blocked runtime/real-loop authority boundary unchanged.

## Boundary Check

- Work stayed in the declared workbench frontend and task evidence surfaces.
- No backend/authentication source, production study path, runtime database,
  service, provider, browser session or medical-writing surface was touched.
- This was a direct Codex route; no external Hermes agent or runner dispatch was
  used and no runner-owned report was edited.

## Codex Verification

- `medicalMonitoringPrincipal.test.mjs`: **17 passed**.
- All **33** medical-monitoring frontend pure `.test.mjs` modules passed.
- `npm run build`: passed in **1.74s**; Vite's existing main-chunk >500 kB
  warning remains and is not treated as a functional failure.
- `node --check frontend/src/features/medical-monitoring/medicalMonitoringPrincipal.mjs`:
  passed.
- Source hashes at review: parser
  `dc66e1aa4dd27f7366236d1c199c55273306c836b467bffeffd8f947cf9fbede`;
  focused test `e66873a72ecac7bdf11a85be59807f0f43d6626afdaeea8ff8ac807568bf054e`.
- The authoritative gate remains `mode=read_only`, `status=blocked`, with
  provider/runtime/write authority false; mode coverage remains empty and not
  release-ready. Reserved ports 8911, 5174, 8910 and 4173 were not started.
- Browser/Playwright, real projects, server/API login and providers were not
  run because the formal gate still blocks them.

## Direct Work Review

- The parser validates the raw digest value against `^[0-9a-f]{64}$` and no
  longer trims or lowercases identity-bound fields.
- The focused regressions cover malformed, uppercase and whitespace-padded
  values, while canonical lowercase values continue to normalize successfully.
- The change is narrow and does not attempt to create or verify a principal;
  server-issued claims and server-side authorization remain authoritative.

## Residual Risk

Real session issuance, server-side role/project enforcement, replay/CAS
revalidation, browser interaction, clinical/scientific/visual acceptance and
all five-project real-loop evidence remain unproven. B6/C14 formal reviewer
outcomes are still required before P10 activation. The pre-existing Vite bundle
size warning remains for a later scoped performance slice.
