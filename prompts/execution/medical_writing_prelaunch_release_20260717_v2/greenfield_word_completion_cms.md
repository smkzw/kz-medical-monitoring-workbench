# Same-session completion: greenfield Word release gate

First, fully read and comply with `/Users/smkzw/.hermes/SOUL.md` and the latest
`/Users/smkzw/.codex/AGENTS.md`. Continue Hermes session
`20260717_224444_db88e6`; do not repeat completed imported-document checks.

## Hard boundaries

- Work only inside the current workspace.
- Use disposable artifacts only. Do not touch stable ports, stable databases,
  credentials, or original company/clinical documents.
- Codex owns final Microsoft Word and release acceptance.
- Authorized product writes remain limited to
  `services/api/app/medical_writing_document_exporter.py`, directly related
  medical-writing figure/export modules and tests, plus durable evidence under
  `records/active_slices/medical_writing_prelaunch_acceptance_20260717/word_final_qc/greenfield_ra/`.
- Preserve all passing imported RUX/D001 source-preserving behavior.
- Write exactly one output file:
  `runs/execution/medical_writing_prelaunch_release_20260717_v2/greenfield_word_remediation.md`.

Read these files only for initial context:

- `/Users/smkzw/.hermes/SOUL.md`
- `/Users/smkzw/.codex/AGENTS.md`
- `runs/execution/medical_writing_prelaunch_release_20260717_v2/worker_02.md`
- `records/active_slices/medical_writing_prelaunch_acceptance_20260717/word_final_qc/greenfield_ra/production_assembly_report.json`
- `records/active_slices/medical_writing_prelaunch_acceptance_20260717/word_final_qc/greenfield_ra/render_production/render_report.json`
- `records/active_slices/medical_writing_prelaunch_acceptance_20260717/word_final_qc/greenfield_ra/build_production_document.py`
- `services/api/app/medical_writing_document_exporter.py`
- `services/api/app/medical_writing_figure_exporter.py`

The initial list is not a blanket prohibition on later tools or evidence.
Record every additional target and why it was needed.

## Current evidence and exact remaining work

The timed-out pass already produced `greenfield_ra_production.docx` with ten
rendered pages, company-like cover/synopsis, portrait and landscape sections,
TOC/table-list fields, two indexed ordinary tables, a populated SoA with notes,
references, headers, and a footer with PAGE/NUMPAGES fields. Do not rebuild the
task from scratch.

The current artifact is not releasable because:

1. `figure_count=0`, `figure_index_field=false`, and no media part exists even
   though the protocol contains a “研究流程图” section.
2. The required study flow diagram and figure list are absent.
3. The report's top-level PAGE/NUMPAGES counters conflict with its OOXML
   comparison, so the inspection contract must be corrected and deterministic.
4. LibreOffice renders field fallback text such as `更新域后显示目录`. The final
   package must contain valid live fields and cached/fallback content suitable
   for review before a manual Word field update. Do not claim that an empty
   placeholder is a populated directory.
5. The latest footer patch was in progress when the hard timeout occurred.
   Finish it and prove PAGE/NUMPAGES field structure without relying only on
   rendered string parsing.

## Required completion checks

1. Add a governed `study_schema` figure block generated from the synthetic RA
   project inputs. Embed the SVG with a PNG fallback through the existing
   maintained figure exporter; include provenance/hash, figure caption,
   bookmark, index entry, and a non-empty figure-list field. The SVG must be
   the authoritative vector object, not merely a raster screenshot.
2. Regenerate the greenfield production DOCX and inspection JSON. Require
   `figure_count >= 1`, `indexed_figure_count >= 1`, valid SVG + PNG fallback
   package parts/relationships, and a study-flow caption.
3. Verify cover, synopsis table, heading numbering, TOC/table/figure lists,
   page fields, headers/footers, ordinary table, SoA notes, references,
   portrait/landscape sections, and the vector figure. Distinguish live fields
   from cached display text.
4. Render every page using the repository CJK QC path and inspect all pages for
   clipping, missing CJK, blank pages, broken figures, repeated `第1页 共1页`,
   and unexpected orientation/layout changes.
5. Run focused exporter/figure tests and imported RUX/D001 source-preserving
   regressions. Record exact commands and results.
6. Produce an exact PASS/FAIL/UNVERIFIED checklist. Leave Microsoft Word GUI
   opening as UNVERIFIED for Codex; do not claim it.

When implementation uncertainty exists, use official Microsoft/Open XML
documentation or a maintained implementation and record source authority,
fit, and rejected alternatives. Stop if a change would weaken imported-source
fidelity.

Use the required execution-report headings and finish the report before
ending the pass.
