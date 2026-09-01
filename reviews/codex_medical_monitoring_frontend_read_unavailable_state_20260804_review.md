# Codex Review: medical_monitoring_frontend_read_unavailable_state_20260804

Date: 2026-08-04
Route: Codex direct; no Hermes/external-agent dispatch

## Verdict

`PASS — accepted_slice_complete`

## Boundary Check

- This was a direct Codex slice, so there was no delegated-agent write. Changes are confined to the workbench frontend, its focused static test, and the task context/records/review/metrics surfaces.
- No production path, service, provider, browser session, real project, B6/C14 gate, or runner-owned report was written.

## Codex Verification

- Reviewed the full applicable global, workspace, and workbench AGENTS.md instructions before acting.
- `node frontend/tests/monitoring_unavailable_state_qc.mjs`: PASS.
- 31 pure Node tests under `frontend/src/features/medical-monitoring/*.test.mjs`: PASS (31/31).
- `npm run build` from `frontend/`: PASS; only existing Vite large-chunk warning.
- Ports 8911, 5174, 8910, 4173: STOPPED. No browser/API/service verification was attempted because the contract intentionally remains fail-closed and this slice is offline.

## Review Findings

- The old failure path could convert a policy/principal failure into empty arrays or zero counts. The new path preserves structured error codes and renders a visible unavailable state with a technical code.
- Client-detected response project mismatches now become the same explicit fail-closed state; they are not silently discarded.
- The monitoring shell no longer displays an active-project inbox as a fallback when the monitoring route read failed.
- Inbox, subject-catalog and subject-profile failures are held separately; a later success in one read surface cannot erase an unresolved failure in another.
- Client-side response-contract failures are labeled as contract validation rather than as a network outage.
- The project-list loading/error surface also avoids presenting zero as a measured value.
- The review caught and fixed a conditional-Hook ordering hazard in `OverviewPage` before acceptance.
- No unrelated medical-writing or backend behavior was changed.

## Residual Risk

- The real browser appearance and keyboard interaction are not independently accepted in this offline slice.
- Backend route authorization, server principal binding, approved-input/source-token/CAS, B6 formal reviewer outcomes, C14 activation, controlled runtime, and five-project Playwright LOOP remain unproven and unchanged.
