# Task Context: medical_monitoring_app_legacy_state_repair_20260804

Created: 2026-08-04 20:58:18
Objective: Restore App.jsx after incomplete unreachable legacy intake cleanup so the monitored frontend source remains buildable; do not activate runtime or real project pathways.
Task type: `code_scoped_patch_plan`
Risk: `high`
Selected agent route: `codex` / `codex-main` / `high`

## Trigger Reason

This task was initialized through the Codex x Hermes complex-task entrypoint because it is expected to involve more than three execution steps, research/writing/report/code/report-visual work, or source-grounded verification.

## Source Of Truth

- `frontend/src/App.jsx` — current `MonitoringPage` source and the incomplete legacy-intake cleanup boundary.
- `frontend/src/features/medical-monitoring/MedicalMonitoringBatchPanel.jsx` — visible project-bound batch intake surface.
- `tests/test_frontend_monitoring_contract.py` — static source contracts.
- Current workbench filesystem and applicable global/workbench `AGENTS.md` files.
- Hard gates: B6/C14/approved-input/host attestation/runtime/provider/browser/real-project gates remain closed; ports 8911, 5174, 8910 and 4173 must remain empty.

## Scope

- In scope: remove the historical `false && (...)` intake branch and its now-unused project-specific helpers/state from `App.jsx`, update the stale source contracts to the current project-bound `MedicalMonitoringBatchPanel` path, and verify the visible monitoring path remains buildable and contract-clean.
- Out of scope: API/service/storage redesign, B6/C14, approved-input or identity gates, runtime/provider/browser/Playwright/API login, real projects, databases and medical-writing.

## Success Criteria

- `App.jsx` has no unresolved references introduced by the incomplete cleanup attempt.
- Focused and adjacent static contracts, all medical-monitoring Node contracts, and the frontend production build pass.
- Required ports remain empty and no runtime or real-project authority state changes.

## Finding And Decision

The prior cleanup removed declarations and helpers while leaving the historical `false && (...)` branch and its helper functions in place. Vite could transpile that branch but a future activation would fail at runtime, and its old `/monitoring/intake` routes preserved project-specific overfit assumptions. The bounded repair was completed by deleting the unreachable branch and its local helpers/state together, then moving the static assertions to the current project-bound `MedicalMonitoringBatchPanel`/API path.

## Evidence Snapshot

- `frontend/src/App.jsx`: 786,380 bytes; SHA-256 `bd998952f42cc1a1a9afdfe4988cace8fd81069f014772a646f9ccd890dab05d` after cleanup.
- `tests/test_frontend_monitoring_contract.py`: 25,241 bytes; SHA-256 `0cc0bc02bebcbc5f83c68ba97b4c8955c95463bc82f0e04e2033fe2c990a05ad` after contract update.
- Focused frontend Python contracts: 33 passed.
- Adjacent frontend Python contracts: 69 passed.
- Medical-monitoring Node contracts: 32 files passed.
- Vite build: 1,952 modules passed; existing >500 kB chunk warning only.
- Required ports 8911/5174/8910/4173: empty.
- No service, browser, provider, API login, SQLite, real project or Playwright activity.

## Risk Boundaries

- Do not write to production paths until Codex review gate passes and writable paths are explicit.
- The delegated agent is not final authority; Codex owns verification and acceptance.

## Timeout Policy

- Do not mark the delegated agent failed for slow response alone.
- For complex or artifact-heavy work, wait and poll generously; use conference mode when multiple independent model perspectives are needed.
- Failure requires terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.

## Loop Log

- 2026-08-04 20:58:18: Task initialized by `tools/hermes_workflow_guard.py init-task`.
- 2026-08-04 20:57–21:00: Reintroduced the removed legacy-only `MonitoringPage` state/derived values and CSV/sheet helpers; no visible route or backend contract changed.
- 2026-08-04 21:00: Focused/adjacent contracts, Node contracts, Vite build and port checks passed.
- 2026-08-04 21:00–21:03: Removed the unreachable legacy branch, its helper functions, state and CSV/sheet-name helpers; updated stale static assertions to require the project-bound batch panel and forbid the old route.
- 2026-08-04 21:03: Re-ran focused/adjacent contracts, Node contracts, Vite build and port checks; all passed.
