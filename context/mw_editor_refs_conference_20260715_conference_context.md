# Conference Context: mw_editor_refs_conference_20260715

Created: 2026-07-15 14:21:52
Objective: 从医学经理真实写作视角审阅文档/表格统一富文本与全屏交互、主台垂直空间重构、项目级文献引用和GB/T 7714-2015/Word导出架构
Task type: `complex_delivery_conference`
Risk: `high`
Conference mode: `parallel`

## Codex Main Venue

- Chair: Codex.
- Duties: understand the real task, decompose, define sources of truth, route work, protect boundaries, verify final artifacts, own visual/browser/PPT/PDF checks, own production writes, and deliver to the user.

## Conference Panel Assignment

- Visual/design tasks use a Codex-led panel with no Hermes sub-venue chair: Hermes `aishuo / MiniMax-M3` and Hermes `aishuo-gpt55 / gpt-5.5`. If either is unavailable, the runner tries OpenCode Go `qwen3.7-plus`, then `mimo-v2.5`.
- Chinese labels or Chinese sentence review is handled directly by Codex and does not start a conference.
- Other complex tasks use Hermes `aishuo-gpt55 / gpt-5.5` as the sub-venue chair, leading Hermes `aishuo / MiniMax-M3` and OpenCode Go `deepseek-v4-flash`. If the OpenCode Go Flash role fails, the runner first switches to Reasonix `deepseek-v4-flash`, then tries OpenCode Go `qwen3.7-plus` and `mimo-v2.5`.
- Reasonix is used here only as the declared Flash fallback, not as a second review.
- Every conference role starts with one bounded same-session pass. Codex reviews its quality and may dispatch zero or more targeted follow-up prompts through the same session. A new session is a routing failure unless a primary role failed before a resumable session existed and the documented fallback was activated.

## Source Of Truth

- User requirements and durable record: `records/active_slices/medical_writing_editor_references_20260715/TASK_RECORD.md`.
- Current writing shell and rich editor: `frontend/src/App.jsx`, especially `RichProtocolEditor` and `WritingPage`.
- Current full-screen table designer: `frontend/src/features/medical-writing/StructuredTableDesigner.jsx` and `structured-table-designer.css`.
- Current table contract and deterministic mapping: `packages/contracts/workbench_contracts/models.py` (`StructuredTable*`) and `services/api/app/medical_writing_tables.py`.
- Current Word pipeline: `services/api/app/medical_writing_document_exporter.py` and `services/api/app/medical_writing_repository.py`.
- Current real-browser screenshots: `records/visual_qc_20260715/medical_writing_m11_registry_runtime_final/*.png` and `records/visual_qc_20260715/medical_writing_workspace_crash_probe_v5/*.png`.
- Current M11 acceptance: `records/visual_qc_20260715/medical_writing_m11_registry_runtime_final/qc_report.json`, failures empty.
- Official external evidence already verified by Codex on 2026-07-15:
  - Zotero Word integration exposes Add/Edit Citation, Add/Edit Bibliography, Document Preferences, Refresh and Unlink; citation selection searches author/title/year and the bibliography updates dynamically.
  - Crossref REST `/works/{doi}` returns publisher-deposited DOI metadata; public access is available without registration.
  - NCBI E-utilities are the public API for PubMed and support PMID-based retrieval.
  - CSL processors use structured item metadata and style definitions.
  - The national standard platform marks GB/T 7714-2015 abolished and GB/T 7714-2025 current from 2026-07-01. The user explicitly requires 2015 as the default; implementation must persist the selected standard/version and allow future 2025 selection without silently changing old documents.

## Current Technical Facts

- The main TipTap editor already supports font, size, bold, italic, underline, superscript, subscript, text color, highlight, lists, alignment, line spacing, indentation, paragraph spacing, styles, undo/redo and tables.
- Main-canvas tables can receive TipTap marks, but the separate full-screen table designer edits each cell as plain `textarea`; the `StructuredTableCell` contract currently persists only `text`, so format cannot survive designer save/reload/export.
- The main rich editor has no full-screen mode. The table designer is a full-screen fixed workspace.
- Ordinary source/work-copy state is rendered in a multi-row card plus one or more warning/info strips. The user identified repeated source-read-only, local-work-copy, AI-boundary and identity text as consuming valuable vertical space.
- AI quick actions currently consume a separate row above the status card. The user directed moving them beside the page title.
- Stable ports are `5174/8911`; changes are tested in isolated runtimes before touching stable data.

## Scope

- In scope: shared formatting command layer; rich cell storage and export; body/table full-screen modes; compact document command/status bar; project-level literature entity/import/deduplication; manual/AI citation insertion; stable numeric rendering; automatically generated References section; DOCX bookmarks/hyperlinks; tests and desktop QC.
- Out of scope: installing or depending on desktop Zotero/EndNote/Mendeley; editing external production files; making AI-generated citations valid without an admitted metadata record; current-web browsing by conference models; final visual or regulatory acceptance by Hermes.

## Success Criteria

- Table-cell and body formatting survive save, reload and Word export in two real projects plus one greenfield project.
- Body and table can each enter/exit full screen without React error, losing selection or changing content.
- At 1920x1080 the document canvas is materially taller and ordinary state notices do not occupy separate strips.
- DOI, PMID, PubMed URL and publisher URL imports resolve to one normalized project reference record with provenance, warnings and an explicit override boundary.
- In-text citations render as superscript clickable `[n]`; repeated citations reuse one number; first-occurrence order determines numbering; generated References updates deterministically.
- AI may cite only admitted reference IDs and must return reference bindings, not naked numeric strings.
- Draft and approved Word exports contain stable reference entries and internal citation-to-reference links; old documents without citations remain compatible.
- Codex performs final browser, Word XML, live API and source review.

## Parallel Work Rule

For logic-heavy, rigor-sensitive, or artifact-heavy tasks, each participant independently runs the whole bounded workflow and writes a separate output. Leads compare after all available participant outputs are in or explicitly marked pending.

## Timeout Policy

- Participant soft wait: 20 minutes.
- Large-task participant wait: 45 minutes.
- Chair hard wait: 90 minutes.
- Failure rule: Do not fail a model for slow response alone; fail only on terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.

## Risk Boundaries

- Hermes is advisory; Codex remains final authority.
- Codex owns visual/browser/PPT/PDF/rendered checks, live authority checks, final clinical/regulatory conclusions, and production writes.
- Do not mark a slow model failed solely due to latency.
- Do not recommend a visual-only toolbar that stores formatting nowhere.
- Do not make `GB/T 7714-2015` a mutable global singleton; old projects retain their selected style version.
- Do not treat DOI/PMID/URL as trusted complete metadata. Preserve source, retrieval time, normalized identifiers, completeness warnings, manual edits and audit history.
- Do not put ingestion logs, duplicate-resolution internals or AI provenance cards permanently beside the document canvas.

## Loop Log

- 2026-07-15 14:21:52: Conference initialized by `hermes_workflow_guard.py init-conference`.
- 2026-07-15 14:23: Global `/Users/smkzw/.codex/AGENTS.md` fully read in two segments; SHA-256 `058c2aba8196d225a0a1ddda7ec77695a12b5c4e46e97ae43bec5bcc4c372a8c`.
