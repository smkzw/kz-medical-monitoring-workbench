# Task Context: mw_front_matter_synopsis_objects_20260717

Created: 2026-07-17 13:47:21
Objective: 建立首页排版对象与独立方案摘要表的明确边界，复用StudyDefinition、工作副本和DOCX链，在D001、RUX、PNH真实方案中避免把排版表当正文表，并让1.1摘要可结构化编辑与同步渲染。
Task type: `code_scoped_patch_plan`
Risk: `high`
Selected agent route: `codex` / `codex-main` / `high`

## Trigger Reason

This task was initialized through the Codex x Hermes complex-task entrypoint because it is expected to involve more than three execution steps, research/writing/report/code/report-visual work, or source-grounded verification.

## Source Of Truth

- User boundary: only tables that print as real content tables use the general table editor; invisible-border cover/layout tables remain layout objects; the protocol synopsis is one dedicated large table and must not be mixed with body tables.
- Current M11 registry: `services/api/app/medical_writing_protocol_template.py`, front matter and 1.1 interactions.
- Current route: `frontend/src/App.jsx::medicalWritingStructuredTarget()` maps both `front_matter_editor` and `synopsis_editor` back to framing identity instead of a dedicated object.
- Current import/runtime: `services/api/app/protocol_text_extractor.py`, `medical_writing_document.py`, `medical_writing_tables.py`, `medical_writing_document_exporter.py`.
- Current table editor: `frontend/src/features/medical-writing/StructuredTableDesigner.jsx`.
- Index boundary already implemented: `records/active_slices/medical_writing_word_indexes_crossrefs_20260716/TASK_RECORD.md`; index heuristics do not yet give the editor a durable object role.
- Company style authority: `CMS-D017-PNH-方案摘要_v0.2.docx` is P0 for front matter, synopsis, Chinese expression, SoA and notes; full protocols supplement full-document structure.
- Real full protocols: RUX-03-002, CMS-D001, and MY008-PNH paths registered in `services/api/app/medical_writing_manifest.py`.
- Runtime read-only evidence on 2026-07-17: all imported front-matter and synopsis tables have `domain=generic`, no template ID, and no dedicated interaction binding.

## Scope

- In scope: durable table/object role contract; deterministic import classification for front-matter layout and synopsis; dedicated front-matter/synopsis interaction routing; same working-copy/CAS/approval/DOCX chain; real D001/RUX/PNH tests and desktop QC.
- In scope: greenfield current-template behavior so new protocols do not regress to generic text-only front matter or synopsis.
- Out of scope: arbitrary Word page-layout recreation, electronic signatures, replacing the full rich-text editor, reclassifying every historical body table, or changing company medical facts without user action.
- Out of scope: writing test data into the stable runtime; all state-changing E2E uses an isolated runtime copied/seeded from original sources.

## Success Criteria

- Front matter layout tables never enter body-table numbering/index/cross-reference or the generic scientific table designer by default.
- The 1.1 protocol synopsis opens one dedicated synopsis-table workflow, synchronizes approved StudyDefinition facts, renders the actual table in the editor, and exports as a real Word table without entering the body table list.
- Imported source tables preserve source layout and remain user-reviewable; role inference is deterministic, project-agnostic and never silently grants medical approval.
- D001 and PNH complete edit/save/reload/DOCX; RUX is a third design/style counterexample. Stable SQLite hashes remain unchanged.
- Focused and broad tests, production build, 1920x1080 browser screenshots, DOCX OOXML/content checks and Codex visual review pass.

## Risk Boundaries

- Do not overwrite source DOCX or stable workbench data.
- Do not infer role from project ID, indication, sponsor or a single exact source filename.
- Border visibility alone is not sufficient: some cover identity tables use visible borders, and some true SoA tables use no explicit borders.
- Do not create a second version/approval store; roles and dedicated editors must reuse existing content-block, working-copy, approval and export contracts.
- Do not auto-approve imported fields or overwrite user-edited synopsis text when StudyDefinition changes; use impact preview and explicit reconciliation.

## Timeout Policy

- Do not mark the delegated agent failed for slow response alone.
- For complex or artifact-heavy work, wait and poll generously; use conference mode when multiple independent model perspectives are needed.
- Failure requires terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.

## Loop Log

- 2026-07-17 13:47:21: Task initialized by `tools/hermes_workflow_guard.py init-task`.
- 2026-07-17 13:47-14:00: Read-only runtime audit confirmed the open Gap Matrix issue. RUX front table 0 and synopsis table 1, D001 front tables 0-2 and synopsis table 4, PNH front tables 0-12 and synopsis table 13 are all generic tables. Direct source inspection confirms layout diversity: invisible-border cover grids, visible-border identity/confidentiality grids, dotted contact layout grids and bordered synopsis tables. D017 P0 synopsis has a 6x2 identity table, 18x3 synopsis table and 38x13 SoA.
- Global AGENTS SHA-256: `e82267a73f25bfca091854994217fae1a77feb06d415d4bc2c5f5b1d0687cf45`; this `code_scoped_patch_plan/high` route is Codex direct. No external Agent dispatch is permitted by the selected route.
