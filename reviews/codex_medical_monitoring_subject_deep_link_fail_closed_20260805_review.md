# Codex Review: medical_monitoring_subject_deep_link_fail_closed_20260805

Date: 2026-08-05 (Asia/Shanghai)
Execution: Codex direct under the Hermes workflow guard; no external Hermes
agent or runner dispatch.

## Verdict

**Pass for the bounded source-only slice.** An unavailable subject deep link
now fails closed without changing project or subject scope to another record.

## Boundary Check

- Work stayed inside the workbench frontend and declared context/record/review/
  metrics surfaces. No production study path, provider, service or browser was
  touched.
- The direct Codex route did not edit the runner-owned report path.

## Codex Verification

- Focused route module: **50 passed**.
- All **33** frontend medical-monitoring pure modules passed.
- `npm run build`: final verification passed in **1.98s**; existing >500 kB
  main-chunk warning remains.
- `node --check` passed for the changed route module.
- Gate re-read: `mode=read_only`, `status=blocked`, authority/provider/runtime/
  write flags false; mode coverage evidence remains zero.
- Reserved ports 8911, 5174, 8910 and 4173 were empty.
- Browser/Playwright, API login, provider, real-project and visual/clinical
  checks were not run because the formal gate blocks them.

## Direct Work Review

- Explicit subject ids are checked only against the current project's returned
  catalog. An absent id produces no subject-scoped fetch and no first-subject
  fallback.
- URL synchronization retains the requested subject until a user takes the
  route-safe recovery action; the Timeline/Profile branches show the same
  boundary message.
- No server-side permission or medical conclusion is inferred from the UI
  guard.

## Residual Risk

Real catalog authorization, browser interaction, stale-link semantics, real
subject data and clinical correctness remain unproven. B6/C14 formal review,
source-token bytes and aggregate/CAS replay remain required before P10.
