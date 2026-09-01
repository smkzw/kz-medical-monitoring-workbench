# Codex Review: monitoring_p8b_frontend_20260729

Date: 2026-07-30  
Implementation handoff:
`records/handoffs/monitoring_p8b_frontend_handoff_20260729.md`

## Verdict

**PASS for source/old-runtime frontend integration.** New P8-A runtime acceptance remains
explicitly pending the authorized API restart after the V7 queue drains.

## Boundary Check

- Implementation changed only the medical-monitoring frontend component, shared App/style
  attachment points, the medical-monitoring client/state/model modules, and their tests.
- No medical-writing source, backend business module or runtime database was changed by this
  slice.
- The existing API process was not restarted.

## Codex Verification

- High-conflict backend/frontend contract selection:
  `78 passed` across assurance, taxonomy, risk repository/index and frontend monitoring/Safety
  projection contracts.
- Medical-writing consumer regression:
  `23 passed` across editor safety, waiting/progress and AI route freeze contracts.
- Frontend state modules:
  API `75`, checklist state `20`, models `44`, route state `33`; all passed.
- Vite production build passed: 1903 modules transformed. The pre-existing large-chunk warning
  remains non-blocking and was not introduced as a functional regression.
- Handoff browser evidence covered 1440x900 and 1728x1000, server query state, risk selection,
  evidence tabs, Timeline return and lack of body/cell overflow against the still-running old
  API.

## Conflict-Point Review

1. **No text classification:** `riskChecklistCategoryTags` now reads only
   `risk_category_label` and explicit `safety_pv_flag`; title, rationale, tags and source type
   cannot change category.
2. **No second Safety/PV risk store:** the peer page reads the same pinned risk snapshot and
   retains only rows whose backend boolean flag is `true`.
3. **Deep-link continuity:** scope, site, subject, risk ids, view, evidence tab, all seven
   filters, sort, page, page size and snapshot id survive URL round-trips.
4. **Desktop information hierarchy:** the checklist remains seven columns; sort/filter controls
   are in column headers/popovers rather than a permanent form row; detail remains in-page.

## Residual Risk

- P8-A does not yet expose `safety_pv_flag` as a server filter. The Safety/PV peer page therefore
  reads every page of one pinned snapshot and filters only the explicit backend boolean locally.
  This is semantically safe but may be inefficient for very large projects.
- Live taxonomy labels, all seven server filters, pinned pagination, 409/422 rendering and
  cross-project behavior must be rechecked after the current API is restarted with P8-A.
