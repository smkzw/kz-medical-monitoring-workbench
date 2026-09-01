# Task Context: medical_monitoring_unclassified_structure_action_20260804

Created: 2026-08-04 15:23:51
Objective: Add a compact, fail-closed action from the visible unclassified listing-sheet warning to the existing batch/field-mapping workspace; preserve risk conclusions and avoid runtime/server changes.
Task type: `code_scoped_patch_plan`
Risk: `medium`
Selected agent route: `codex` / `codex-main` / `high`

## Trigger Reason

This task was initialized through the Codex x Hermes complex-task entrypoint because it is expected to involve more than three execution steps, research/writing/report/code/report-visual work, or source-grounded verification.

## Source Of Truth

- `frontend/AGENTS.md` and the current `frontend/src/App.jsx`, `frontend/src/styles.css`,
  `frontend/tests/monitoring_unavailable_state_qc.mjs`.
- LOOP 5.87/5.88 structure-driven intake records: unknown/ambiguous sheets are explicit
  `unclassified_sheet_names` and cannot enter risk conclusions without mapping confirmation.
- The medical-monitoring specification's low-noise, action-oriented desktop UX contract.

## Scope

- In scope: add one clearly labeled button in the existing amber unclassified-structure warning;
  the button opens the existing batch/field-mapping workspace through the current toggle path.
- In scope: add focused static contract assertions and preserve the warning's fail-closed copy.
- Out of scope: automatic mapping, risk/batch mutation, API/server/runtime changes, new routes,
  provider calls, browser startup, real-project execution, or medical conclusions.

## Success Criteria

- The warning remains visible with count, examples and explicit “not included in risk conclusions”
  language.
- The action is keyboard reachable, has an accessible name/title, and calls the existing workspace
  toggle; it does not claim that mapping has been confirmed.
- Focused static test, all frontend medical-monitoring Node tests and frontend build pass.
- No reserved port 8911/5174/8910/4173 is started and no medical-writing file is touched.

## Risk Boundaries

- Do not write to production paths until Codex review gate passes and writable paths are explicit.
- The delegated agent is not final authority; Codex owns verification and acceptance.

## Timeout Policy

- Do not mark the delegated agent failed for slow response alone.
- For complex or artifact-heavy work, wait and poll generously; use conference mode when multiple independent model perspectives are needed.
- Failure requires terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.

## Loop Log

- 2026-08-04 15:23:51: Task initialized by `tools/hermes_workflow_guard.py init-task`.
- 2026-08-04 15:24:10: Re-read applicable frontend contract and captured pre-edit hashes for App,
  styles and unavailable-state static QC.
- 2026-08-04 15:26:55: Added the warning action through the existing batch/field-mapping toggle;
  corrected the stale project-inbox fallback assertion; static, module, Python contract and Vite
  build checks passed. Hermes review-gate returned `ok=true` with no warnings/errors. No runtime,
  provider, browser, real-project or reserved-port activity occurred.
- 2026-08-04 15:28:00: Closed LOOP 5.112 evidence and retained B6/C14/real-loop blockers as the
  next external gate; overall Goal remains active.
