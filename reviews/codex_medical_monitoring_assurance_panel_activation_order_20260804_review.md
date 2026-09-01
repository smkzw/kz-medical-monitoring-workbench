# Codex Review — assurance-panel activation ordering

## Verdict

Accepted for the bounded frontend lifecycle scope. The patch aligns the assurance panel with the established monitoring request-scope order and prevents strict-mode disposed-request starts; it does not grant evidence or release authority.

## Review findings

- `createMedicalMonitoringProjectRequestScope` rejects work begun while disposed.
- The assurance panel's open-state `loadTasks(mode)` effect previously preceded activation, unlike the batch, daily-run, protocol-preparation and rule-release drawers.
- Moving the existing activation/disposal effect before task loading is the smallest coherent fix; task detail/audit effects remain after task loading and retain their cancellation guards.
- No principal, medical evidence, API, data, gate or authority semantics changed.

## Verification

- Focused contract: 33 passed.
- All 32 monitoring Node contracts passed.
- Adjacent frontend Python contracts: 69 passed.
- Vite build passed with the existing large-chunk warning.
- Required ports are empty.

## Boundary

Source-level only; no B6/C14, source-token/CAS, approved-input, runtime, provider, browser/Playwright, API login, real-project, database or medical-writing activity.

## Hermes review-gate

The local Hermes review-gate is the required evidence check for this tracked slice and must pass with `--require-verification`.
