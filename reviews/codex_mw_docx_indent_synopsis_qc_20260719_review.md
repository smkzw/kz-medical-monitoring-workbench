# Codex Review: mw_docx_indent_synopsis_qc_20260719

Date: 2026-07-19
Primary evidence:
`records/active_slices/medical_writing_cross_indication_reference_gate_20260718/docx_preflight_v9/`

## Verdict

PASS for the bounded D017 synopsis-object and section 5.1 paragraph-format
remediation. This is not a release-wide Word acceptance decision.

## Boundary Check

- The evidence directory contains an isolated D017 SQLite store, generated
  DOCX/PDF, Open XML reports, navigation counts and selected 200 DPI pages.
- The original company synopsis remained read-only.
- No commercial Word engine was adopted. Microsoft Word was used only for
  interactive field update, native reopen, resave and PDF acceptance.

## Codex Verification

- Open XML SDK 3.5.1 / Microsoft365 gate: `ErrorCount=0` before and after Word
  resave.
- Microsoft Word native PDF: A4, 28 pages.
- Synopsis objective/endpoint object:
  - six internal rows, with the outer left label vertically merged;
  - bullet counts `1/2/3` for primary/secondary/exploratory objectives;
  - bullet counts `1/12/5` for corresponding endpoints;
  - endpoint category labels are bold.
- Section 5.1:
  - 24 non-empty body paragraphs before the next heading;
  - all carry `w:firstLineChars=200` and `w:firstLine=480`;
  - 200 DPI page 20 visually shows each real body paragraph indented by two
    Chinese characters rather than only the first paragraph.
- Word navigation retained 108 `_Toc*` bookmarks and 108 internal hyperlinks.
- Direct OOXML inspection found no blue run color: document colors are
  `AUTO`; the visible red text is the deliberate draft-preview watermark.
- Relevant deterministic regression recorded by the task: `72 passed`,
  Ruff clean.

## Rendered Review

- Page 10 shows the synopsis outer table, grouped objective/endpoint headings
  and first primary row with no cell collision.
- Pages 11-12 show secondary and exploratory groups, bullets and wrapped
  content without clipping or border drift.
- Page 20 shows Heading 1/2 hierarchy, black body text, correct first-line
  indentation, readable line spacing and no overlap.

## Residual Risk

- The implementation uses a six-row grouped table structure rather than a
  literal nested `w:tbl`. It meets the requested visible/editable
  table-within-table semantics in this artifact, but future editor round-trip
  tests must continue to preserve the row groups and merges.
- Final release still requires a fresh export from the completed AI-first
  authoring flow and at least one additional different project after all
  frontend/backend merges.
