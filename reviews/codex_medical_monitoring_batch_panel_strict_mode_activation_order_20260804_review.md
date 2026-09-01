# Codex Review — batch-panel strict-mode activation ordering

## Verdict

Accepted for the bounded frontend lifecycle scope. The change prevents a strict-mode remount from loading through a disposed project request scope; it does not imply runtime or release readiness.

## Review findings

1. `createMedicalMonitoringProjectRequestScope` intentionally aborts requests started while disposed.
2. Before this patch, the batch panel's initial-load effect was declared before the activation effect. A strict-mode cleanup/replay could therefore run the load setup before the activation setup, producing an immediately aborted request.
3. The existing monitoring drawers use activation-before-load ordering. Moving the same existing effect above the load effect is the smallest coherent correction.
4. The LOOP 5.132 mounted guard and `batch-view` cleanup remain intact; no data, authority, or backend semantics changed.

## Verification

- Focused contract: 32 passed.
- All 32 monitoring Node contracts passed.
- Adjacent frontend Python contracts: 68 passed.
- Vite production build passed; only the existing large-chunk warning remains.
- Required ports are empty.

## Boundary

This review covers only source-level effect ordering and its deterministic regressions. B6/C14, source-token/CAS, approved-input, runtime, provider, browser/Playwright, API-login, real-project and commercial gates remain unchanged and blocked where previously blocked.

## Hermes review-gate

The local Hermes review-gate is the required evidence check for this tracked slice and must pass with `--require-verification`.
