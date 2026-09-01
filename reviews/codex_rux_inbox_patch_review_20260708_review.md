# Codex Review: rux_inbox_patch_review_20260708

Date: 2026-07-08 CST
Hermes output: `runs/hermes_rux_inbox_patch_review_20260708.md`

## Verdict

Pass for the current backend-only RUX P0 inbox slice after Codex-applied fixes.

This is not commercial-complete RUX medical monitoring and not frontend acceptance. It only accepts the backend P0 behavior: verified RUX medical-monitoring risk anchors project into the unified inbox contract with source locators and explicit P0 boundaries.

## Boundary Check

- Hermes stayed inside the allowed read list and wrote only `runs/hermes_rux_inbox_patch_review_20260708.md`.
- Hermes did not read original clinical project folders, browse web, run tests, or edit files.
- Hermes read `/Users/smkzw/.hermes/SOUL.md` and reported it fully read.
- Codex performed final source checks, edits, and verification.

## Hermes Findings And Codex Disposition

- F1/F2: RUX inbox is intentionally limited to medical-monitoring items and one module summary for P0. Codex does not accept this as a blocking architecture defect because RUX is not yet registered in the project catalog and this slice intentionally avoids fake demo metadata. Codex accepted the "silent narrowing" part and added visible item-level boundary wording: `当前RUX P0 inbox仅展示医学监查风险项`.
- F3: Accepted. `SubjectOverview.treatment_arm` changed from developer-facing placeholder to `待解盲`.
- F4: Accepted as frontend follow-up. `dose_adjustment` requires timeline renderer support before RUX frontend/browser acceptance. No frontend UI change was made in this backend slice.
- F5: Accepted. `_rux_monitoring_risk_items()` now logs per-subject risk-evaluation failures.
- F6-F8: Accepted as follow-up risks: hardcoded P0 subject list, local path config, and row-index-based ID stability.

## Codex Verification

Red tests observed before fixes:

- RUX inbox baseline returned 404 for `/api/projects/proj_rux_03_002/workbench-inbox?limit=20`.
- New tests failed because ECB events were still `protocol_deviation`, RUX inbox returned 404, `treatment_arm` exposed developer-facing text, RUX boundary wording was missing, and subject risk exceptions were silently swallowed.

Green verification after fixes:

- Focused target tests: 2 OK.
- RUX service tests: 6 OK.
- Workbench inbox tests: 6 OK.
- Combined contract/RUX/inbox regression: 32 OK.
- Full backend regression: `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -v` -> 124 OK.
- API spot check: RUX inbox returned 200, 4 items, subjects `S01003`, `S01017`, `S03040`, no `/Users/`, no `protocol_deviation`.
- Frontend production build: `npm run build` -> passed; known Vite chunk-size warning only.

## Residual Risk

- RUX frontend project switching and timeline renderer support for `dose_adjustment` remain unaccepted.
- RUX P0 inbox currently projects only verified medical-monitoring risk anchors and does not represent full RUX project work across every subsystem.
- Performance is acceptable for tests but still parses/calculates real RUX workbook on request; production needs caching/incremental parsing.
- P0 subject list is hardcoded and must be replaced before broad subject coverage.
- Row-index-derived IDs are not durable enough for repeated EDC listing refreshes.
