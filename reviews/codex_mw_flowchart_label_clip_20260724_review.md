# Codex Review: mw_flowchart_label_clip_20260724

Date: 2026-07-25

## Verdict

PASS for the bounded study-flowchart label fix and the real Word
flowchart/IBDQ embedding gate.

## Boundary Check

- The Codex x Hermes workflow guard selected the visual conference route;
  delegated Grok/Kimi evidence was treated as review input, not final
  acceptance authority.
- Production changes stayed within the generic study-schema renderer and its
  focused tests. No MY009 identifier, dose string, node identifier or fixture
  coordinate was added to production logic.
- Regenerated artifacts are confined to the task evidence directory.
- The Word orchestrator opened, saved and closed only the task-owned roundtrip
  document. The user's pre-existing MG-K10 document remained open before and
  after the gate.

## Codex Verification

- `tests/test_medical_writing_study_schema.py`: 30 passed after the final
  generic placement revision.
- The regenerated DOCX passed all pre-Word OOXML media, relationship, title
  sequence and TOC checks.
- Microsoft Word 16.111.1 updated fields, saved, closed, reopened and exported
  a 13-page A4 PDF. Post-Word OOXML retained one SVG, the PNG fallback, nine
  unique IBDQ PNG pages, `svgBlip`, TOC and all nine appendix titles.
- `updateFields` was cleared by Word after the fields were actually updated;
  this is expected post-update state, not media loss.
- All 13 PDF pages were rendered at 200 DPI. Codex and an independent visual
  reviewer both confirmed page 3 shows the complete
  `240 mg BID安全性不佳` label with no node/arrow overlap or clipping.
- Pages 5-13 are consecutive IBDQ source pages 1/9 through 9/9 with the title
  and source page on the same Word page, no blank separator, omission,
  duplication or clipping.
- The calibrated deterministic page-level image gate passed every criterion.

## Residual Risk

- This acceptance is intentionally narrow. It proves the generic flowchart
  label repair, SVG/PNG Word compatibility, and nine-page assessment-instrument
  embedding. It does not accept the content or layout of a complete
  production clinical protocol.
- Quartz PDF emitted a reconstructable cross-reference warning in Poppler, but
  the PDF opened, rendered all 13 pages and was visually complete.
