# Codex Review: medical_monitoring_project_deep_link_fail_closed_20260805

Date: 2026-08-05 (Asia/Shanghai)
Execution: Codex direct under the Hermes workflow guard; no external Hermes
agent or runner dispatch was permitted or needed.

## Verdict

**Pass for the bounded source-only slice.** The implementation closes the
identified frontend deep-link fallback hazard without changing backend
authorization or the blocked real-loop gate.

## Boundary Check

- Work stayed inside the workbench and the declared frontend/context/record/
  review/metrics surfaces. No production study path, provider, service or
  browser session was touched.
- The direct Codex route wrote the declared source/test/build-derived and task
  evidence surfaces; the runner-owned report path was not edited.

## Codex Verification

- `medicalMonitoringRouteState.test.mjs`: **44 passed**.
- All **33** medical-monitoring frontend pure `.test.mjs` modules passed.
- `npm run build`: passed twice, final **1.76s**; Vite's existing main-chunk
  >500 kB warning remains and is not introduced as a functional failure.
- `node --check` for the changed route module passed; the generated bundle
  contains the new unavailable-link labels.
- Authoritative gate re-read after the change: `mode=read_only`,
  `status=blocked`, provider/runtime/write all false; mode coverage remains
  `evidence_count=0`, `release_ready=false`.
- Ports 8911, 5174, 8910 and 4173 were all `EMPTY`.
- Browser/Playwright, real project, server, API-login, provider and medical
  acceptance checks were intentionally not run because the formal gate blocks
  them.

## Direct Work Review

- The resolver is pure and membership-based; it preserves an explicit request
  and cannot select a different project for that request.
- App hydration, empty-project recovery, project selector enablement and URL
  synchronization were checked as the adjacent consumer surfaces.
- No server-side authorization claim is inferred from this frontend guard.
- The change is narrow; generated `frontend/dist` remains derived output and
  is not treated as runtime evidence.

## Residual Risk

Real role/permission enforcement, server-side project authorization, browser
deep-link interaction, project switching under a running service and all
clinical/scientific/visual acceptance remain unproven. B6/C14 formal reviewer
outcomes, source-token bytes and aggregate/CAS replay are still required before
P10 activation or real-project LOOP.
