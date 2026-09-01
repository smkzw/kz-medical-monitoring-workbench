# Task Context: mw-w4a-recommendation-ui

Created: 2026-07-24 23:53:10
Objective: Implement and verify recommendation-first candidate-package composite adoption UI for the medical writing authoring journey using the already accepted W3 public API, without backend or editor changes
Task type: `visual_report_structure`
Risk: `high`
Selected agent route: `mixed` / `conference:visual-no-chair-grok45+kimi-code-k3` / `mixed:Codex-led visual panel; Grok Build then qwen then mimo replacement order`

## Trigger Reason

This task was initialized through the Codex x Hermes complex-task entrypoint because it is expected to involve more than three execution steps, research/writing/report/code/report-visual work, or source-grounded verification.

## Source Of Truth

- `runs/execution/mw_w4_recommendation_frontend_20260724/kimi_manager_plan_01.md`
- `packages/contracts/workbench_contracts/models.py`
- `services/api/app/medical_writing_authoring_journey.py`
- `services/api/app/medical_writing_authoring_prefill.py`
- `services/api/app/main.py`
- `frontend/src/features/medical-writing/MedicalWritingAuthoringJourneySetup.jsx`
- `frontend/src/styles.css`
- `frontend/tests/medical_writing_authoring_prefill_frontend_qc.mjs`
- Existing nearby medical-writing frontend tests and components.
- W3 is accepted: focused 62 tests plus 4 subtests, full W3 389 tests plus
  52 subtests, flowchart 30 tests, Python compile and frontend build passed.
- The real audience is a desktop-first, senior Chinese clinical medical
  writing manager. The primary workflow is AI recommendation and user
  correction/confirmation, not empty-form authoring.

## Scope

- In scope:
  - Add `frontend/src/features/medical-writing/AuthoringCandidatePackagePanel.jsx`.
  - Replace the fake sequential low-risk single-field adoption loop in
    `MedicalWritingAuthoringJourneySetup.jsx` with one public
    `prefill-package/adopt-composite` request.
  - Present one recommended candidate and at most four alternatives, with
    source text, rationale, tradeoffs and evidence gaps before collapsed
    locator metadata.
  - Support per-path overrides or explicit skips for pending decisions.
  - Render the server receipt exactly, including applied, overridden, derived,
    skipped, invalidated, replayed and stale states.
  - Add focused deterministic frontend tests and only the CSS needed by this
    slice.
- Out of scope:
  - Backend, contracts, TipTap, table editors, App.jsx, competitor drawer,
    instrument appendix preview, runtime data, and production service control.
  - Security/backdoor auditing or unrelated refactoring.

## Success Criteria

- Exactly one POST is issued for a composite adoption; there is no sequential
  loop pretending to be a batch.
- Stable idempotency uses the existing `stableAuthoringWriteKey` convention.
- A 409 reloads journey/package state once, informs the user, and never
  silently retries the adoption.
- Pending paths cannot be submitted until each path has an override or an
  explicit skip.
- No UI string says `待医学批准`; a medical manager's explicit choice is the
  decision.
- Single-field candidate adoption remains available for true field candidates.
- Focused tests and `npm --prefix frontend run build` pass.
- The worker returns a compact loop trace and the marker
  `W4A_RECOMMENDATION_UI_COMPLETE`; Codex retains final browser and visual
  acceptance.

## Risk Boundaries

- Authorized write set:
  - `frontend/src/features/medical-writing/AuthoringCandidatePackagePanel.jsx`
  - `frontend/src/features/medical-writing/MedicalWritingAuthoringJourneySetup.jsx`
  - `frontend/src/styles.css`
  - focused `frontend/tests/medical_writing_*prefill*_qc.mjs` or
    `frontend/tests/medical_writing_composite_adopt_frontend_qc.mjs`
- Do not write backend, contracts, runtime databases, App.jsx, editor/table
  components, task records, or runner-managed report files.
- Preserve W4-B/W4-C changes already present in the journey component and CSS.
- Do not start, stop or restart stable services.
- Do not use Qoder/qwen3.8-max-preview for this run.
- The delegated agent is not final authority; Codex owns verification and acceptance.

## Timeout Policy

- Do not mark the delegated agent failed for slow response alone.
- For complex or artifact-heavy work, wait and poll generously; use conference mode when multiple independent model perspectives are needed.
- Failure requires terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.

## Acceptance Update

- 2026-07-25: The initial direct-AI browser run completed the RA and PNH
  recommendation/search/adoption flows but exposed a QC-only hard-coded
  `availableFields >= 10` assumption. A valid partial package had six
  recommendations and the three core identity candidates.
- The acceptance condition now checks package identity, valid ready/partial
  state, at least one recommendation and at least one core candidate. Product
  pending-field gates are unchanged.
- The candidate package UI now keeps unselected alternatives to a compact
  summary; the selected candidate keeps source text visible and places
  clinical trade-offs, evidence gaps, limitations and affected paths behind a
  deliberate disclosure control.
- A fresh isolated run using the configured independent
  `deepseek/deepseek-v4-pro` product AI and live ClinicalTrials.gov searches
  passed every check at 1920x1080 and 2560x1440, including reload persistence,
  design adoption, stale-revision recovery and no horizontal overflow.

## Loop Log

- 2026-07-24 23:53:10: Task initialized by `tools/hermes_workflow_guard.py init-task`.
