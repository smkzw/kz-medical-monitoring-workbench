# Codex Review: mw_truthful_pipeline_progress_20260729

Date: 2026-07-29
Delegated-agent output: `runs/codex_mw_truthful_pipeline_progress_20260729.md`

## Verdict

Pass after Codex revision. The delegated implementation supplied the required
real child projections, but Codex corrected a terminal-to-retry monotonicity
defect before acceptance.

## Boundary Check

- Product changes stayed within the declared pipeline, compact authoring
  progress surface, and focused tests.
- Candidate projection, document admission, frozen r11 evidence/databases,
  release matrices, and unrelated runtime stores were not changed by this
  slice.

## Codex Verification

- Inspected stage anchors, child projections, persistence, refresh, retry,
  waiting, failed, and terminal transitions.
- Added regression proving `failed=100 -> triaging=22` and clearing stale
  document-preparation child labels.
- Added regression proving `preparing -> awaiting_document_validation`
  preserves same-phase observed child evidence.
- Focused progress/waiting tests: `12 passed`.
- Broad related suite: `321 passed`.
- Python compilation passed for changed backend modules.
- `frontend/npm run build` passed.

## Delegated-Agent Output Review

The formula and persistence design were traceable and appropriately reused the
existing compact banner. The initial use of `max(previous, stage_anchor)` in
`_set_stage` was unsafe across terminal-to-active transitions; this was fixed
and covered before acceptance. No claim from the delegated handoff was accepted
without local source/test verification.

Hermes was not dispatched for this bounded slice because the active nighttime
route forbade aishuo; the permitted Codex subagent supplied the implementation
and Codex performed the conflict/risk review and final acceptance.

## Residual Risk

Deterministic tests cannot prove the user-facing cadence of a long real
download/OCR/translation run. r12 must validate browser-visible parent percent,
child percent, current document/chapter label, reload persistence, and retry
reset against fresh isolated runtime data.
