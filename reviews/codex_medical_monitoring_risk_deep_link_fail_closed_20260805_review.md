# Codex Review: medical_monitoring_risk_deep_link_fail_closed_20260805

Date: 2026-08-05 (Asia/Shanghai)
Execution: Codex direct under the Hermes workflow guard; no external Hermes
agent or runner dispatch.

## Verdict

**Pass for the bounded source-only slice.** Current-project risk deep links are
now explicit and fail closed without changing the runtime gate.

## Boundary Check

- Work stayed inside the workbench frontend and declared context/record/review/
  metrics surfaces. No production study path, provider, service or browser was
  touched.
- The direct Codex route did not edit the runner-owned report path.

## Codex Verification

- Focused route module: **47 passed**.
- All **33** frontend medical-monitoring pure modules passed.
- `npm run build`: passed in **1.86s**; existing >500 kB main-chunk warning
  remains.
- `node --check` passed for the changed route module.
- Gate re-read: `mode=read_only`, `status=blocked`, authority/provider/runtime/
  write flags false; mode coverage evidence remains zero.
- Reserved ports 8911, 5174, 8910 and 4173 were empty.
- Browser/Playwright, API login, provider, real-project and visual/clinical
  checks were not run because the formal gate blocks them.

## Direct Work Review

- Matching is restricted to rows already scoped to the current project; the
  resolver never searches or invents a cross-project fallback.
- App fetch, initial-risk matching, empty-result handling and the warning's
  focus-clear action were checked as one consumer path.
- No server-side permission or medical conclusion is inferred from the UI
  guard; the scope is deliberately source-only.

## Residual Risk

Real role/permission enforcement, stale snapshot semantics, browser interaction,
real study data and clinical correctness remain unproven. B6/C14 formal review,
source-token bytes and aggregate/CAS replay remain required before P10.
