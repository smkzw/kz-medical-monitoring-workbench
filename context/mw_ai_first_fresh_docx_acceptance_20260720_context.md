# Task Context: mw_ai_first_fresh_docx_acceptance_20260720

Created: 2026-07-20 01:42:24
Objective: Generate and validate two fresh real-project DOCX artifacts from the current AI-first authoring path, one synopsis-import and one three-field greenfield, with native Word/OpenXML fidelity acceptance
Task type: `complex_delivery_conference`
Risk: `high`
Selected agent route: `mixed` / `conference:grok-build-grok45-chair+aishuo-cms+opencode-go-deepseek-flash` / `mixed:Grok Build default reasoning; Kimi then Reasonix then qwen then mimo replacement order`

## Trigger Reason

This task was initialized through the Codex x Hermes complex-task entrypoint because it is expected to involve more than three execution steps, research/writing/report/code/report-visual work, or source-grounded verification.

## Source Of Truth

- Current product source under this workspace:
  - `services/api/app/medical_writing_authoring_journey.py`
  - `services/api/app/medical_writing_authoring_prefill.py`
  - `services/api/app/medical_writing_authoring_prefill_ai.py`
  - `services/api/app/medical_writing_synopsis_import.py`
  - `services/api/app/medical_writing_greenfield.py`
  - `services/api/app/medical_writing_protocol_template.py`
  - `services/api/app/medical_writing_document_exporter.py`
  - `services/api/app/writing_reference.py`
  - relevant contracts and tests.
- Real project A authority:
  `/Users/smkzw/Documents/康哲项目资料/CMS-D017/4.方案/PNH/方案摘要/CMS-D017-PNH-方案摘要_v0.2.docx`
- Real project B authority:
  `/Users/smkzw/Documents/康哲项目资料/Ruxolitinib-AD/CFDI Inspection/RUX-03-002-自查文件包-20260107/10-临床试验重要文件/1-临床试验方案/V1.3版-2024.8.14/磷酸芦可替尼乳膏-AD3期临床研究方案V1.3-clean-20240814.docx`
- Company style/template authorities:
  - `/Users/smkzw/Documents/康哲项目资料/模版/方案模版/CMS-D017Ⅰ期方案-v1.1-20260209-clean.docx`
  - `/Users/smkzw/Documents/康哲项目资料/模版/方案模版/CMS-D005-减重II期临床试验方案概要-V0.3-KZYY0525-clean-DIP0526-KZYY0526 (2).docx`
- Current accepted bounded Word baseline and acceptance logic:
  - `records/active_slices/medical_writing_cross_indication_reference_gate_20260718/docx_preflight_v9/ACCEPTANCE_REPORT.md`
  - `reviews/codex_mw_word_real_acceptance_20260719_review.md`
  - `reviews/codex_mw_docx_indent_synopsis_qc_20260719_review.md`
- Current AI-first prefill acceptance:
  - `reviews/codex_prefill_v4_prod_acceptance_20260720.md`
  - `records/active_slices/medical_writing_ai_first_authoring_redesign_20260718/TASK_RECORD.md`

## Scope

- In scope:
  - create a new isolated evidence directory at
    `records/active_slices/medical_writing_ai_first_docx_release_20260720/`;
  - create project A through the actual synopsis-import journey path and project
    B through the actual three-minimum-fact AI-first journey path;
  - for project B, use the product's independently configured direct
    `deepseek-v4-pro`, adopt the English ClinicalTrials.gov condition term,
    execute the product discovery service, bind the immutable snapshot, and
    regenerate the package before document creation;
  - derive exact RUX dose, endpoints, timepoints and safety facts only from the
    supplied original RUX protocol and record source locators;
  - generate two fresh editable DOCX artifacts through the current product
    exporter;
  - run deterministic contract tests, OOXML package inspection and the bundled
    Open XML SDK Microsoft365 validator;
  - record a replayable harness, receipts, state snapshots, validation JSON and
    a concise report.
- Out of scope:
  - stable runtime databases and stable 5174/8911 writes;
  - product source or test edits in the first pass;
  - use of old generated DOCX files as current acceptance;
  - fabrication of missing exact clinical facts;
  - final Word-native visual acceptance, which remains Codex-owned.

## Success Criteria

- Both projects start from their declared raw source and current services, not a
  copied old database, previously generated DOCX, or pre-deconstructed skill
  output.
- Project A proves synopsis import, extracted-fact confirmation and fresh DOCX
  generation.
- Project B proves the current AI-first sequence from only drug, indication and
  phase through real English condition recommendation, user adoption, plan
  revision, real registry search, snapshot binding and regenerated prefill.
- AI/product provenance is recorded without secrets. Exact facts cite the
  original project protocol and are never attributed to competitor search or
  shared phrasing corpus.
- Each DOCX has real Heading 1-4 styles, hierarchical numbering, TOC/SEQ/REF
  fields, internal bookmarks/hyperlinks, synopsis grouped table, black body and
  table content, two-Chinese-character first-line indentation for normal body
  paragraphs, Chinese `宋体`, Latin/digits `Times New Roman`, headers, footers
  and page numbering.
- Open XML SDK Microsoft365 validation returns zero errors for both pre-Word
  files. If source-preserving export contains source-originated errors, no new
  error signature is allowed and the relative baseline must be explicit.
- The worker must not claim native Word/PDF acceptance. Codex will open both
  files in Microsoft Word, update all fields, save acceptance copies, export
  PDFs and inspect representative pages before release.

## Risk Boundaries

- The only worker write root is
  `records/active_slices/medical_writing_ai_first_docx_release_20260720/`.
- Real authority files are read-only. Stable databases and ports are read-only.
- Product AI calls use the existing local environment configuration without
  printing credentials.
- Do not run repository-wide Git operations.
- The delegated agent is not final authority; Codex owns verification and acceptance.

## Timeout Policy

- Do not mark the delegated agent failed for slow response alone.
- For complex or artifact-heavy work, wait and poll generously; use conference mode when multiple independent model perspectives are needed.
- Failure requires terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.

## Loop Log

- 2026-07-20 01:42:24: Task initialized by `tools/hermes_workflow_guard.py init-task`.
