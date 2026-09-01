# Codex Review: medical_monitoring_site_deep_link_fail_closed_20260805

Date: 2026-08-05 (Asia/Shanghai)
Execution: Codex direct under the Hermes workflow guard; no external Hermes
agent or runner dispatch.

## Verdict

**Pass for the bounded source-only slice.** Site deep links now distinguish
known, pending and unavailable identities without substituting another center.

## Boundary Check

- Work stayed inside the workbench frontend and declared context/record/review/
  metrics surfaces. No production study path, provider, service or browser was
  touched.
- The direct Codex route did not edit the runner-owned report path.

## Codex Verification

- Focused route module: **54 passed**.
- All **33** frontend medical-monitoring pure modules passed.
- `npm run build`: passed in **1.92s**; existing >500 kB main-chunk warning
  remains.
- `node --check` passed for the changed route module.
- Gate re-read: `mode=read_only`, `status=blocked`, authority/provider/runtime/
  write flags false; mode coverage evidence remains zero.
- Reserved ports 8911, 5174, 8910 and 4173 were empty.
- Browser/Playwright, API login, provider, real-project and visual/clinical
  checks were not run because the formal gate blocks them.

## Direct Work Review

- Site candidates are restricted to current subject and risk-rollup identities;
  an empty candidate set is `pending`, so missing data is not mislabeled as a
  missing center.
- The warning only appears for a real unavailable site and returns to trial
  scope without changing project identity.
- No server-side permission or medical conclusion is inferred from the UI
  guard.

## Residual Risk

Real center authorization, browser interaction, stale-link semantics, real
site data and clinical correctness remain unproven. B6/C14 formal review,
source-token bytes and aggregate/CAS replay remain required before P10.
