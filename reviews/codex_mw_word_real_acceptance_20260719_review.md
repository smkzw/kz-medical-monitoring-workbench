# Codex Review: mw_word_real_acceptance_20260719

Date: 2026-07-19
Current authority artifact:
`records/active_slices/medical_writing_cross_indication_reference_gate_20260718/docx_preflight_v9/d017_pnh_company_authority_word_acceptance_v9.docx`

## Verdict

PASS for the current D017 Word-native acceptance artifact. The medical-writing
subsystem release gate remains open until a post-merge end-to-end project is
generated from the new AI-first workflow and the same checks are repeated
across at least two projects.

## Codex Verification

- Microsoft Word opened, updated fields, resaved and exported the document to
  a 28-page A4 PDF.
- Open XML SDK Microsoft365 validation after Word resave returned zero errors.
- The title hierarchy is represented by real Word paragraph styles:
  `heading 1`, `heading 2`, `heading 3`; TOC 1-3 entries preserve parent-child
  numbering and page targets.
- Navigation contains 108 matching TOC bookmarks and hyperlinks.
- The first page has a controlled title, protocol number, version, indication,
  applicant and confidentiality statement; no blue title/table styling was
  observed.
- Chinese/Latin font contract is present in generated runs and styles:
  East Asian `宋体`; ASCII/HAnsi `Times New Roman`.
- Synopsis, body paragraphs, headers, footers, page numbering and draft
  watermark were visually checked in the Word-native PDF.

## Prior Cross-Project Evidence

- D001 and RUX source-preserving exports previously passed the relative
  OpenXML contract: passthrough/paragraph/table-cell edits introduced no new
  error signature beyond each source document.
- The greenfield RA schema-clean artifact previously passed Open XML
  validation and Word field update, but predates the current D017 synopsis and
  paragraph remediation. It cannot substitute for a fresh final integration
  export.

## Residual Risk

- Release acceptance must rerun after the editor Enter fix and AI prefill
  package are merged because they change the authoring path that supplies the
  exporter.
- The final gate must include at least two fresh projects with different
  indication/design/modality, one synopsis import and one three-field
  greenfield project.
