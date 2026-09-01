# Same-session follow-up: close frontend evidence gaps

First, fully read and comply with `/Users/smkzw/.hermes/SOUL.md`, the latest
`/Users/smkzw/.codex/AGENTS.md`, and the applicable workspace/frontend
`AGENTS.md` files. Continue Grok Build session
`e8f7f967-4b82-46bc-a048-157bdf4ea655`; do not restart the analysis from
scratch.

## Hard boundaries

- Codex remains chief architect and final browser/release authority.
- Work only inside the current workspace.
- Use disposable runtimes and non-stable ports.
- Do not touch stable ports/databases, credentials, backend product source, or
  original clinical files.
- Authorized writes are limited to the two frontend QC scripts, a narrowly
  implicated frontend source fix if and only if a real product defect is
  reproduced, durable browser evidence under
  `records/active_slices/medical_writing_prelaunch_acceptance_20260717/browser_final_qc/`,
  and the existing report
  `runs/execution/medical_writing_prelaunch_release_20260717_v2/frontend_remediation.md`.
- Preserve existing passing evidence, but replace the matrix/report summary
  with the corrected rerun result.
- Write exactly one output file:
  `runs/execution/medical_writing_prelaunch_release_20260717_v2/frontend_remediation.md`.

Read these files only for initial context:

- `/Users/smkzw/.hermes/SOUL.md`
- `/Users/smkzw/.codex/AGENTS.md`
- `AGENTS.md`
- `frontend/AGENTS.md`
- `runs/execution/medical_writing_prelaunch_release_20260717_v2/frontend_remediation.md`
- `records/active_slices/medical_writing_prelaunch_acceptance_20260717/browser_final_qc/frontend_remediation_matrix.json`
- `frontend/tests/medical_writing_frontend_remediation_qc.mjs`
- `frontend/src/App.jsx`

This initial list is not a blanket prohibition on later tools or evidence.
Record each additional target and why it was needed.

## Observed gaps that must be closed

1. `frontend_remediation_matrix.json` contains a non-contract status
   `source_imported_unverified` for `rux-api-session`, while the summary only
   counts PASS/FAIL/SKIPPED/UNVERIFIED. Normalize every check to exactly those
   four statuses. Unknown statuses must make the runner fail.
2. The RUX table-fullscreen check searches `textContent`, but the actual icon
   button exposes only `title`/`aria-label` (`全屏编辑当前表格结构与附注` or
   `全屏查看当前表格`). This made a present control look missing.
3. The current matrix records four HTTP 500 console errors and one 409 without
   recording URL, method, response body, request context, or whether each was
   expected. A release check cannot pass with unclassified 500s.
4. The user explicitly requires table editing and fullscreen behavior. A
   supported real table must be selected; cell edit, save, browser reload, and
   fullscreen open/close must be observed. Do not accept SKIPPED merely because
   the initially selected RUX section/control locator was wrong.

## Required actions

1. Instrument Playwright `response` events and record every response with
   status >=400: method, pathname (no secrets/query tokens), status, bounded
   response body, and the immediately preceding test action/check id.
2. Rerun the complete disposable greenfield + RUX matrix. Classify each 409
   against an explicit expected conflict assertion. Every 500 is FAIL unless
   its exact request is deliberately injected and asserted as a negative test;
   ordinary product/UI requests must not return 500.
3. Navigate to a real RUX section containing a table. Locate the fullscreen
   table button by accessible name/title, open the designer, verify the shared
   formatting controls and table structure/notes are visible, edit a bounded
   non-sensitive cell in the disposable working copy, save, reload, and verify
   the cell value through UI and API. Then close fullscreen and verify the
   normal editor remains usable.
4. If RUX source-preserving rules legitimately prevent the selected cell edit,
   use another real imported table section or the governed greenfield table
   template, but record why and still prove a supported production table
   edit/save/reload/fullscreen journey. Do not weaken imported-source rules.
5. Keep viewport checks at 1440x900, 1920x1080, and 2560x1440. Build the
   frontend and run the corrected matrix.
6. Update the report with an exact PASS/FAIL/SKIPPED/UNVERIFIED checklist,
   response ledger, changed files, commands, observations, and residual
   uncertainty. `PASS` must equal the number of checks whose literal status is
   PASS; unknown statuses are forbidden.

Stop and report if closing the table journey requires a backend contract
change. Do not claim publication acceptance.
